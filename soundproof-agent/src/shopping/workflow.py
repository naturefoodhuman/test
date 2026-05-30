# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 16:41:07 CST

from __future__ import annotations

import time
from uuid import uuid4

from security.anti_bot_policy import ShoppingAntiBotPolicy
from shopping.cache_models import ProductCacheEntry, ShoppingRunCache
from shopping.executor_interface import ShoppingExecutor
from shopping.filtering import IntentListingFilter
from shopping.keyword_builder import KeywordBuilder
from shopping.llm_services import ShoppingFieldNormalizerService, ShoppingSummaryService
from shopping.ranking import IntentProductRanker
from shopping.review_enricher import ProductReviewEnricher
from shopping.schemas import ProductDetail, ShoppingSearchIntent, ShoppingSessionSnapshot, WorkflowStepTrace
from shopping.sqlite_cache import ShoppingCacheStore


class ShoppingWorkflow:
    """购物工作流编排器。"""

    def __init__(
        self,
        *,
        executor: ShoppingExecutor,
        keyword_builder: KeywordBuilder,
        summary_service: ShoppingSummaryService | None,
        cache_store: ShoppingCacheStore | None = None,
        field_normalizer_service: ShoppingFieldNormalizerService | None = None,
        ranker: IntentProductRanker | None = None,
        listing_filter: IntentListingFilter | None = None,
        review_enricher: ProductReviewEnricher | None = None,
        review_top_n: int = 3,
        anti_bot_policy: ShoppingAntiBotPolicy | None = None,
        enforce_delay: bool = False,
    ) -> None:
        self.executor = executor
        self.keyword_builder = keyword_builder
        self.summary_service = summary_service
        self.cache_store = cache_store
        self.field_normalizer_service = field_normalizer_service
        self.ranker = ranker or IntentProductRanker()
        self.listing_filter = listing_filter or IntentListingFilter()
        self.review_enricher = review_enricher
        self.review_top_n = review_top_n
        self.anti_bot_policy = anti_bot_policy or ShoppingAntiBotPolicy()
        self.enforce_delay = enforce_delay

    def run(self, intent: ShoppingSearchIntent, limit: int = 5) -> ShoppingSessionSnapshot:
        """运行一次购物工作流。"""

        workflow_notes: list[str] = []
        step_traces: list[WorkflowStepTrace] = []
        search_query = self.keyword_builder.build_query(intent)
        run_id = f"run_{uuid4().hex[:12]}"
        self.executor.start_run_context(run_id, search_query)

        if self.cache_store is not None:
            recent_searches = self.cache_store.count_recent_events("search", within_seconds=3600)
            search_decision = self.anti_bot_policy.evaluate_search(searches_in_last_hour=recent_searches)
            workflow_notes.extend(search_decision.reasons)
            if not search_decision.allowed:
                step_traces.append(self._trace_step("search_guard", 0, status="error", notes=search_decision.reasons))
                self.executor.end_run_context()
                raise ValueError("当前搜索频率超过安全策略上限，请稍后再试。")
            self._apply_delay_if_needed(search_decision.suggested_delay_seconds)
            self.cache_store.record_event(
                "search",
                {
                    "run_id": run_id,
                    "query": search_query,
                    "recent_searches": recent_searches,
                    "delay_seconds": search_decision.suggested_delay_seconds,
                },
            )
            step_traces.append(self._trace_step("search_guard", 0, notes=search_decision.reasons))

        raw_listings, duration_ms = self._timed(lambda: self.executor.search(search_query, limit=limit))
        listings, rejected_listings = self.listing_filter.analyze(intent, raw_listings)
        listings = listings[:limit]
        step_traces.append(self._trace_step("search_listings", duration_ms, notes=[f"原始候选数：{len(raw_listings)}", f"保留候选数：{len(listings)}", f"过滤候选数：{len(rejected_listings)}"]))

        detail_batch_decision = self.anti_bot_policy.evaluate_detail_batch(requested_detail_pages=len(listings))
        workflow_notes.extend(detail_batch_decision.reasons)
        if not detail_batch_decision.allowed:
            step_traces.append(self._trace_step("detail_guard", 0, status="error", notes=detail_batch_decision.reasons))
            self.executor.end_run_context()
            raise ValueError("当前详情页抓取数量超过安全策略上限，请缩减候选数量后重试。")
        self._apply_delay_if_needed(detail_batch_decision.suggested_delay_seconds)
        step_traces.append(self._trace_step("detail_guard", 0, notes=detail_batch_decision.reasons))

        details: list[ProductDetail] = []
        total_detail_ms = 0
        for product in listings:
            detail, duration_ms = self._timed(lambda product=product: self.executor.fetch_detail(product))
            total_detail_ms += duration_ms
            detail = self._maybe_normalize_detail(detail)
            details.append(detail)
            if self.cache_store is not None:
                self.cache_store.record_event(
                    "detail",
                    {
                        "run_id": run_id,
                        "title": detail.title,
                        "detail_url": detail.detail_url,
                    },
                )
        step_traces.append(self._trace_step("detail_fetch", total_detail_ms, notes=[f"详情页数：{len(details)}"]))

        ranked_details, rank_duration_ms = self._timed(lambda: self.ranker.rank(intent, details))
        step_traces.append(self._trace_step("first_rank", rank_duration_ms, notes=[f"排序后候选数：{len(ranked_details)}"]))

        review_decision = self.anti_bot_policy.evaluate_review_batch(requested_review_fetches=min(self.review_top_n, len(ranked_details)))
        workflow_notes.extend(review_decision.reasons)
        if review_decision.allowed:
            ranked_details, review_duration_ms = self._timed(lambda: self._maybe_enrich_reviews(intent, ranked_details, run_id=run_id))
            step_traces.append(self._trace_step("review_enrich", review_duration_ms, notes=review_decision.reasons or [f"评论增强候选数：{min(self.review_top_n, len(ranked_details))}"]))
        else:
            workflow_notes.append("已跳过评论增强，原因：评论抓取批次超出安全策略")
            step_traces.append(self._trace_step("review_enrich", 0, status="skipped", notes=review_decision.reasons))

        ranked_details, second_rank_ms = self._timed(lambda: self.ranker.rank(intent, ranked_details))
        step_traces.append(self._trace_step("second_rank", second_rank_ms))

        summary = None
        if self.summary_service is not None:
            summary, summary_ms = self._timed(lambda: self.summary_service.summarize(intent=intent, products=ranked_details))
            step_traces.append(self._trace_step("summary", summary_ms))
            if self.cache_store is not None:
                self.cache_store.record_event(
                    "summary",
                    {
                        "run_id": run_id,
                        "recommended_option": summary.recommended_option,
                    },
                )

        artifact_names = self.executor.get_recent_artifact_names()
        snapshot = ShoppingSessionSnapshot(
            run_id=run_id,
            search_intent=intent,
            search_query=search_query,
            listing_products=listings,
            filtered_out_products=rejected_listings,
            detailed_products=ranked_details,
            comparison_summary=summary,
            workflow_notes=workflow_notes,
            artifact_names=artifact_names,
            step_traces=step_traces,
        )

        if self.cache_store is not None:
            self.cache_store.initialize()
            run_cache = ShoppingRunCache(
                run_id=run_id,
                search_query=search_query,
                search_intent=intent,
                entries=[
                    ProductCacheEntry(
                        cache_id=f"entry_{index + 1}",
                        search_query=search_query,
                        listing=listing,
                        detail=detail,
                    )
                    for index, (listing, detail) in enumerate(zip(listings, ranked_details))
                ],
                filtered_out_products=rejected_listings,
                summary=summary,
                artifact_names=artifact_names,
                workflow_notes=workflow_notes,
                step_traces=step_traces,
            )
            self.cache_store.save_run(run_cache)

        self.executor.end_run_context()
        return snapshot

    def _timed(self, func):
        start = time.perf_counter()
        result = func()
        duration_ms = int((time.perf_counter() - start) * 1000)
        return result, duration_ms

    @staticmethod
    def _trace_step(step: str, duration_ms: int, *, status: str = "ok", notes: list[str] | None = None) -> WorkflowStepTrace:
        return WorkflowStepTrace(step=step, duration_ms=duration_ms, status=status, notes=notes or [])

    def _apply_delay_if_needed(self, seconds: float) -> None:
        if self.enforce_delay and seconds > 0:
            time.sleep(seconds)

    def _maybe_enrich_reviews(self, intent: ShoppingSearchIntent, products: list[ProductDetail], *, run_id: str) -> list[ProductDetail]:
        if self.review_enricher is None:
            return products

        enriched: list[ProductDetail] = []
        for index, product in enumerate(products):
            if index < self.review_top_n:
                enriched_product = self.review_enricher.enrich(intent=intent, product=product)
                enriched.append(enriched_product)
                if self.cache_store is not None:
                    self.cache_store.record_event(
                        "review_enrich",
                        {
                            "run_id": run_id,
                            "title": enriched_product.title,
                            "review_sample_count": enriched_product.review_sample_count,
                            "review_effective_count": enriched_product.review_effective_count,
                        },
                    )
            else:
                enriched.append(product)
        return enriched

    def _maybe_normalize_detail(self, detail: ProductDetail) -> ProductDetail:
        if self.field_normalizer_service is None:
            return detail
        if not detail.raw_spec_text:
            return detail

        return self.field_normalizer_service.normalize(
            title=detail.title,
            raw_text=detail.raw_spec_text,
            price_text=detail.price_text,
            shop_name=detail.shop_name,
            detail_url=detail.detail_url,
        )

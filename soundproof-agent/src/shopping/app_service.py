# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 14:27:11 CST

from __future__ import annotations

from typing import Any

from shopping.bundle_exporter import ShoppingBundleExporter
from shopping.history_analysis import build_history_summary
from shopping.history_compare import compare_runs
from shopping.intent_builder import ConsultationContext, ShoppingIntentBuilder
from shopping.keyword_builder import KeywordBuilder
from shopping.probe_suite import analyze_full_probe
from shopping.report_builder import ShoppingReportBuilder
from shopping.run_analysis import RunAnalyzer
from shopping.schemas import ListingProduct, ProductDetail, ShoppingSessionSnapshot
from shopping.workflow import ShoppingWorkflow


class ShoppingApplicationService:
    """购物应用服务。"""

    def __init__(
        self,
        *,
        executor,
        cache_store,
        summary_service=None,
        field_normalizer_service=None,
        anti_bot_policy=None,
        review_enricher=None,
        review_top_n: int = 3,
        enforce_delay: bool = False,
    ) -> None:
        self.executor = executor
        self.cache_store = cache_store
        self.summary_service = summary_service
        self.field_normalizer_service = field_normalizer_service
        self.anti_bot_policy = anti_bot_policy
        self.review_enricher = review_enricher
        self.review_top_n = review_top_n
        self.enforce_delay = enforce_delay
        self.keyword_builder = KeywordBuilder()
        self.intent_builder = ShoppingIntentBuilder()
        self.report_builder = ShoppingReportBuilder()
        self.run_analyzer = RunAnalyzer()
        artifact_root = getattr(executor, "artifact_root", None)
        self.bundle_exporter = ShoppingBundleExporter(artifact_root) if artifact_root else None

    def build_workflow(self) -> ShoppingWorkflow:
        """构建工作流实例。"""

        return ShoppingWorkflow(
            executor=self.executor,
            keyword_builder=self.keyword_builder,
            summary_service=self.summary_service,
            cache_store=self.cache_store,
            field_normalizer_service=self.field_normalizer_service,
            anti_bot_policy=self.anti_bot_policy,
            review_enricher=self.review_enricher,
            review_top_n=self.review_top_n,
            enforce_delay=self.enforce_delay,
        )

    def preview_intent(self, context: ConsultationContext) -> dict[str, Any]:
        """仅预览购物意图，不执行抓取。"""

        return self.intent_builder.build(context).model_dump()

    def run_from_consultation_context(
        self,
        context: ConsultationContext,
        *,
        limit: int,
    ) -> ShoppingSessionSnapshot:
        """从咨询上下文直接运行购物工作流。"""

        intent = self.intent_builder.build(context)
        return self.build_workflow().run(intent=intent, limit=limit)

    def build_markdown_report(self, snapshot: ShoppingSessionSnapshot) -> str:
        """把一次购物快照导出为 Markdown 报告。"""

        return self.report_builder.build_markdown(snapshot)

    def probe_full_candidate(
        self,
        *,
        query: str,
        title: str,
        detail_url: str,
        wait_after_load_ms: int = 3000,
        review_limit: int = 10,
    ) -> dict[str, Any]:
        """对一次真实联调做全链路探针汇总。"""

        search_probe = self.executor.probe_search_query(query, wait_after_load_ms=wait_after_load_ms)
        detail_probe = self.executor.probe_detail_url(detail_url, wait_after_load_ms=wait_after_load_ms)
        review_probe = self.probe_reviews_for_detail(title=title, detail_url=detail_url, limit=review_limit)
        full_analysis = analyze_full_probe(
            search_probe=search_probe,
            detail_probe=detail_probe,
            review_probe=review_probe,
        )
        return {
            "search_probe": search_probe,
            "detail_probe": detail_probe,
            "review_probe": review_probe,
            "full_analysis": full_analysis,
        }

    def search_once(self, query: str, *, limit: int) -> list[ListingProduct]:
        """执行一次搜索。"""

        return self.executor.search(query=query, limit=limit)

    def probe_reviews_for_detail(
        self,
        *,
        detail_url: str,
        title: str,
        limit: int = 10,
    ) -> dict[str, Any] | None:
        """对某个详情页做评论探针。"""

        if self.review_enricher is None:
            return None
        fetcher = self.review_enricher.review_fetcher
        probe_method = getattr(fetcher, "probe_reviews", None)
        if probe_method is None:
            return None
        return probe_method(ProductDetail(title=title, detail_url=detail_url), limit=limit)

    def detail_once(self, product: ListingProduct, *, normalize_with_llm: bool = True) -> ProductDetail:
        """抓取一个详情页，并按需做字段补归纳。"""

        detail = self.executor.fetch_detail(product)
        if normalize_with_llm and self.field_normalizer_service is not None:
            return self.field_normalizer_service.normalize(
                title=detail.title,
                raw_text=detail.raw_spec_text or detail.title,
                price_text=detail.price_text,
                shop_name=detail.shop_name,
                detail_url=detail.detail_url,
            )
        return detail

    def recent_events(self, limit: int = 50) -> list[dict]:
        """查看最近事件日志。"""

        return self.cache_store.list_recent_events(limit=limit)

    def recent_event_stats(self, within_seconds: int = 3600) -> dict[str, int]:
        """查看最近一段时间的执行事件统计。"""

        return self.cache_store.summarize_recent_events(within_seconds=within_seconds)

    def build_artifact_manifest(self, run_id: str) -> list[dict[str, Any]]:
        """构建某次运行的 artifact manifest。"""

        if self.bundle_exporter is None:
            return []
        result = self.cache_store.get_run(run_id)
        if result is None:
            return []
        return self.bundle_exporter.build_manifest(result)

    def list_run_artifacts(self, run_id: str) -> list[str]:
        """列出某次运行关联的产物。"""

        result = self.cache_store.get_run(run_id)
        if result is None:
            return []
        if result.artifact_names:
            return list(result.artifact_names)
        return []

    def export_run_bundle(self, run_id: str, output_dir: str | Path) -> dict[str, Any] | None:
        """导出某次运行为独立目录。"""

        if self.bundle_exporter is None:
            return None
        result = self.cache_store.get_run(run_id)
        if result is None:
            return None
        return self.bundle_exporter.export_run(result, output_dir)

    def export_latest_bundle(self, output_dir: str | Path) -> dict[str, Any] | None:
        """导出最近一次运行。"""

        run_id = self.cache_store.latest_run_id()
        if run_id is None:
            return None
        return self.export_run_bundle(run_id, output_dir)

    def export_run_archive(self, run_id: str, output_root: str | Path) -> dict[str, Any] | None:
        """导出某次运行的 zip 档案。"""

        if self.bundle_exporter is None:
            return None
        result = self.cache_store.get_run(run_id)
        if result is None:
            return None
        return self.bundle_exporter.export_run_archive(result, output_root)

    def export_latest_archive(self, output_root: str | Path) -> dict[str, Any] | None:
        """导出最近一次运行的 zip 档案。"""

        run_id = self.cache_store.latest_run_id()
        if run_id is None:
            return None
        return self.export_run_archive(run_id, output_root)

    def compare_history_runs(self, left_run_id: str, right_run_id: str) -> dict[str, Any] | None:
        """比较两次历史运行。"""

        left = self.cache_store.get_run(left_run_id)
        right = self.cache_store.get_run(right_run_id)
        if left is None or right is None:
            return None
        return compare_runs(left, right)

    def compare_latest_two_runs(self) -> dict[str, Any] | None:
        """比较最近两次运行。"""

        runs = self.cache_store.list_recent_run_caches(limit=2)
        if len(runs) < 2:
            return None
        return compare_runs(runs[1], runs[0])

    def history_summary(self, limit: int = 20) -> dict[str, Any]:
        """汇总最近若干次运行的总体情况。"""

        runs = self.cache_store.list_recent_run_caches(limit=limit)
        return build_history_summary(runs)

    def list_history_summaries(self, limit: int = 20) -> list[dict]:
        """列出带时间的历史摘要。"""

        return self.cache_store.list_run_summaries(limit=limit)

    def list_history(self) -> list[tuple[str, str, str]]:
        """列出历史运行。"""

        return self.cache_store.list_runs()

    def get_history(self, run_id: str) -> dict[str, Any] | None:
        """读取历史运行。"""

        result = self.cache_store.get_run(run_id)
        if result is None:
            return None
        return result.model_dump()

    def analyze_history_run(self, run_id: str) -> dict[str, Any] | None:
        """分析某次历史运行。"""

        result = self.cache_store.get_run(run_id)
        if result is None:
            return None
        return self.run_analyzer.analyze(result)

    def analyze_latest_run(self) -> dict[str, Any] | None:
        """分析最近一次运行。"""

        run_id = self.cache_store.latest_run_id()
        if run_id is None:
            return None
        return self.analyze_history_run(run_id)

    def build_history_report(self, run_id: str) -> str | None:
        """把某次历史运行导出为 Markdown 报告。"""

        result = self.cache_store.get_run(run_id)
        if result is None:
            return None
        return self.report_builder.build_markdown(result.to_snapshot())

    def build_latest_report(self) -> str | None:
        """导出最近一次历史运行的 Markdown 报告。"""

        run_id = self.cache_store.latest_run_id()
        if run_id is None:
            return None
        return self.build_history_report(run_id)

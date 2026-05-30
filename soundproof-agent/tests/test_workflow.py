# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 23:56:44 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shopping.keyword_builder import KeywordBuilder
from shopping.replay_executor import ReplayShoppingExecutor
from shopping.review_enricher import ProductReviewEnricher
from shopping.review_fetcher import ReplayReviewFetcher
from shopping.schemas import ProductComparisonSummary, ShoppingSearchIntent
from shopping.sqlite_cache import ShoppingCacheStore
from shopping.workflow import ShoppingWorkflow


class _FakeSummaryService:
    """测试用假总结服务。"""

    def summarize(self, *, intent: ShoppingSearchIntent, products):
        return ProductComparisonSummary(
            recommended_option=products[0].title,
            reason_summary=f"场景：{intent.scene}，优先推荐首个候选。",
            risk_points=["测试风险点"],
            search_refinement=["测试 refinement"],
        )


class _FakeFieldNormalizerService:
    """测试用假字段补归纳服务。"""

    def normalize(self, *, title, raw_text, price_text=None, shop_name=None, detail_url=None):
        from shopping.schemas import ProductDetail

        if "四玻双夹胶单中空" in title:
            return ProductDetail(
                title=title,
                price_text=price_text,
                shop_name=shop_name,
                detail_url=detail_url,
                raw_spec_text=raw_text + " 四玻 双夹胶 四道密封 系统窗",
                glass_spec="四玻双夹胶单中空",
                frame_spec="108系统窗",
                seal_spec="四道密封",
                extracted_keywords=["normalized-high-spec"],
            )
        return ProductDetail(
            title=title,
            price_text=price_text,
            shop_name=shop_name,
            detail_url=detail_url,
            raw_spec_text=raw_text,
            glass_spec="5+20A+5中空玻璃",
            frame_spec="推拉窗",
            seal_spec="两道密封",
            risk_flags=["推拉窗结构隔音上限通常弱于平开窗"],
            extracted_keywords=["normalized-basic-spec"],
        )


class ShoppingWorkflowTestCase(unittest.TestCase):
    """购物工作流测试。"""

    def test_run_workflow(self) -> None:
        fixture_root = Path(__file__).resolve().parent / "fixtures"
        executor = ReplayShoppingExecutor(fixture_root)
        keyword_builder = KeywordBuilder()

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_store = ShoppingCacheStore(Path(temp_dir) / "shopping_cache.sqlite3")
            workflow = ShoppingWorkflow(
                executor=executor,
                keyword_builder=keyword_builder,
                summary_service=_FakeSummaryService(),
                cache_store=cache_store,
                field_normalizer_service=_FakeFieldNormalizerService(),
                review_enricher=ProductReviewEnricher(ReplayReviewFetcher(fixture_root)),
                review_top_n=2,
            )

            intent = ShoppingSearchIntent(
                scene="高架低频卧室",
                budget_level="medium",
                solution_type="replace_window",
                primary_keywords=["隔音窗", "夹胶中空"],
                notes=["低频场景"],
            )
            snapshot = workflow.run(intent, limit=2)

            self.assertTrue(snapshot.run_id)
            self.assertEqual(snapshot.search_query, "隔音窗 夹胶中空 系统窗")
            self.assertEqual(len(snapshot.listing_products), 2)
            self.assertIsNotNone(snapshot.comparison_summary)
            self.assertGreaterEqual(len(cache_store.list_runs()), 1)
            self.assertEqual(snapshot.detailed_products[0].title, "四玻双夹胶单中空 高配隔音窗")
            self.assertGreater((snapshot.detailed_products[0].ranking_score or 0), (snapshot.detailed_products[1].ranking_score or 0))
            self.assertGreaterEqual(snapshot.detailed_products[0].review_sample_count, 1)
            self.assertEqual(snapshot.artifact_names, [])
            self.assertTrue(snapshot.step_traces)
            self.assertTrue(any(item.step == "summary" for item in snapshot.step_traces))


if __name__ == "__main__":
    unittest.main()

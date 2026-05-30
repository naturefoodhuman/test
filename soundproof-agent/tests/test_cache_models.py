# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 02:58:44 CST

from __future__ import annotations

import unittest

from shopping.cache_models import ProductCacheEntry, ShoppingRunCache
from shopping.schemas import ListingProduct, ProductComparisonSummary, ProductDetail, RejectedListingProduct, ShoppingSearchIntent, WorkflowStepTrace


class ShoppingRunCacheTestCase(unittest.TestCase):
    """缓存快照转换测试。"""

    def test_to_snapshot(self) -> None:
        run_cache = ShoppingRunCache(
            run_id="run_001",
            search_query="隔音窗 夹胶中空 系统窗",
            search_intent=ShoppingSearchIntent(
                scene="高架低频卧室",
                budget_level="medium",
                solution_type="replace_window",
                primary_keywords=["隔音窗", "夹胶中空"],
            ),
            entries=[
                ProductCacheEntry(
                    cache_id="entry_1",
                    search_query="隔音窗 夹胶中空 系统窗",
                    listing=ListingProduct(title="A", detail_url="https://example.com/a"),
                    detail=ProductDetail(title="A"),
                )
            ],
            filtered_out_products=[
                RejectedListingProduct(title="密封条", reason="命中配件关键词")
            ],
            summary=ProductComparisonSummary(
                recommended_option="A",
                reason_summary="测试推荐",
            ),
            artifact_names=["run_001_taobao_search_test.json"],
            workflow_notes=["测试备注"],
            step_traces=[WorkflowStepTrace(step='summary', duration_ms=88)],
        )

        snapshot = run_cache.to_snapshot()
        self.assertEqual(snapshot.run_id, "run_001")
        self.assertEqual(snapshot.search_query, "隔音窗 夹胶中空 系统窗")
        self.assertEqual(len(snapshot.listing_products), 1)
        self.assertEqual(len(snapshot.detailed_products), 1)
        self.assertEqual(snapshot.comparison_summary.recommended_option, "A")
        self.assertEqual(snapshot.artifact_names, ["run_001_taobao_search_test.json"])
        self.assertEqual(snapshot.filtered_out_products[0].title, "密封条")


if __name__ == "__main__":
    unittest.main()

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 21:32:14 CST

from __future__ import annotations

import unittest
from pathlib import Path

from shopping.review_enricher import ProductReviewEnricher
from shopping.review_fetcher import ReplayReviewFetcher
from shopping.schemas import ProductDetail, ShoppingSearchIntent


class ProductReviewEnricherTestCase(unittest.TestCase):
    """评论增强器测试。"""

    def test_enrich_product_with_reviews(self) -> None:
        fixture_root = Path(__file__).resolve().parent / "fixtures"
        enricher = ProductReviewEnricher(ReplayReviewFetcher(fixture_root))
        intent = ShoppingSearchIntent(
            scene="高架低频卧室",
            budget_level="medium",
            solution_type="replace_window",
            primary_keywords=["夹胶", "三道密封"],
            notes=["低频场景"],
        )
        product = ProductDetail(
            title="70系统平开窗 5+5夹胶+20A+5双层钢化中空玻璃",
            glass_spec="5+5夹胶+20A+5双层钢化中空玻璃",
            seal_spec="三道密封",
            extracted_keywords=["夹胶", "三道密封"],
        )

        enriched = enricher.enrich(intent=intent, product=product)
        self.assertEqual(enriched.review_sample_count, 3)
        self.assertGreaterEqual(enriched.review_effective_count, 2)
        self.assertTrue(enriched.review_risk_flags)


if __name__ == "__main__":
    unittest.main()

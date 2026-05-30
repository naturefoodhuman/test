# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 21:13:05 CST

from __future__ import annotations

import unittest

from shopping.review_models import RawReview
from shopping.review_pipeline import ReviewSignalExtractor
from shopping.schemas import ProductDetail, ShoppingSearchIntent


class ReviewSignalExtractorTestCase(unittest.TestCase):
    """评论有效性识别测试。"""

    def test_summarize_reviews(self) -> None:
        extractor = ReviewSignalExtractor()
        intent = ShoppingSearchIntent(
            scene="高架低频卧室",
            budget_level="medium",
            solution_type="replace_window",
            primary_keywords=["夹胶", "三道密封"],
            notes=["低频场景"],
        )
        product = ProductDetail(
            title="70系统平开窗 5+5夹胶+20A+5中空",
            glass_spec="5+5夹胶+20A+5中空玻璃",
            seal_spec="三道密封",
            extracted_keywords=["夹胶", "三道密封", "平开窗"],
        )
        reviews = [
            RawReview(content="安装后临街噪音明显小了，夹胶玻璃和三道密封确实有用", rating=5, image_count=2),
            RawReview(content="很好", rating=5),
            RawReview(content="还是有点漏风，夜里大车经过时低频还能听见", rating=3),
        ]

        summary = extractor.summarize(reviews, intent=intent, product=product)
        self.assertEqual(summary.total_reviews, 3)
        self.assertGreaterEqual(summary.effective_reviews, 2)
        self.assertGreaterEqual(summary.suspected_brushed_reviews, 1)
        self.assertTrue(any("疑似刷评" in item for item in summary.risk_notes))


if __name__ == "__main__":
    unittest.main()

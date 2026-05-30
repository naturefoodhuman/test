# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 02:58:44 CST

from __future__ import annotations

import unittest

from shopping.filtering import IntentListingFilter
from shopping.schemas import ListingProduct, ShoppingSearchIntent


class IntentListingFilterTestCase(unittest.TestCase):
    """列表页候选过滤测试。"""

    def test_filter_out_accessories(self) -> None:
        filtering = IntentListingFilter()
        intent = ShoppingSearchIntent(
            scene="高架低频卧室",
            budget_level="medium",
            solution_type="replace_window",
            primary_keywords=["隔音窗", "系统窗"],
            negative_keywords=["单层普通玻璃"],
        )
        products = [
            ListingProduct(title="隔音窗密封条 加厚胶条", detail_url="https://example.com/a"),
            ListingProduct(title="70系统平开窗 5+5夹胶+20A+5中空", detail_url="https://example.com/b"),
        ]

        kept, rejected = filtering.analyze(intent, products)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0].title, "70系统平开窗 5+5夹胶+20A+5中空")
        self.assertEqual(len(rejected), 1)
        self.assertIn("配件", rejected[0].reason)


if __name__ == '__main__':
    unittest.main()

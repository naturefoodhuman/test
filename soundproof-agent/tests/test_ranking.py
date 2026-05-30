# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 23:55:38 CST

from __future__ import annotations

import unittest

from shopping.ranking import IntentProductRanker
from shopping.schemas import ProductDetail, ShoppingSearchIntent


class IntentProductRankerTestCase(unittest.TestCase):
    """商品排序器测试。"""

    def test_rank_low_frequency_products(self) -> None:
        ranker = IntentProductRanker()
        intent = ShoppingSearchIntent(
            scene="高架低频卧室",
            budget_level="medium",
            solution_type="replace_window",
            primary_keywords=["隔音窗", "夹胶", "系统窗"],
            notes=["低频场景"],
        )

        products = [
            ProductDetail(
                title="推拉窗 普通中空",
                price_text="680元/㎡",
                glass_spec="5+20A+5中空玻璃",
                seal_spec="两道密封",
                raw_spec_text="推拉窗 5+20A+5中空玻璃 两道密封",
                risk_flags=["推拉窗结构隔音上限通常弱于平开窗"],
            ),
            ProductDetail(
                title="70系统平开窗 5+5夹胶+20A+5中空",
                price_text="718元/㎡",
                frame_spec="70系统平开窗",
                glass_spec="5+5夹胶+20A+5中空玻璃",
                seal_spec="三道密封",
                raw_spec_text="70系统平开窗 5+5夹胶+20A+5中空玻璃 三道密封",
            ),
        ]

        ranked = ranker.rank(intent, products)
        self.assertEqual(ranked[0].title, "70系统平开窗 5+5夹胶+20A+5中空")
        self.assertIsNotNone(ranked[0].ranking_score)
        self.assertGreater(ranked[0].ranking_score or 0, ranked[1].ranking_score or 0)


if __name__ == "__main__":
    unittest.main()

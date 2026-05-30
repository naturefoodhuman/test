# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 23:00:19 CST

from __future__ import annotations

import unittest

from shopping.intent_builder import ConsultationContext, ShoppingIntentBuilder


class ShoppingIntentBuilderTestCase(unittest.TestCase):
    """购物意图构建器测试。"""

    def test_build_intent_for_low_frequency_traffic_scene(self) -> None:
        builder = ShoppingIntentBuilder()
        context = ConsultationContext(
            scene="高架低频卧室",
            budget=8000,
            noise_source="traffic",
            frequency_profile="low",
            preferred_solution="replace_window",
            notes=["夜间大车明显"],
        )

        intent = builder.build(context)

        self.assertEqual(intent.budget_level, "medium")
        self.assertEqual(intent.solution_type, "replace_window")
        self.assertIn("夹胶", intent.primary_keywords)
        self.assertIn("三道密封", intent.primary_keywords)
        self.assertIn("系统窗", intent.primary_keywords)
        self.assertIn("临街", intent.primary_keywords)
        self.assertIn("单层普通玻璃", intent.negative_keywords)


if __name__ == "__main__":
    unittest.main()

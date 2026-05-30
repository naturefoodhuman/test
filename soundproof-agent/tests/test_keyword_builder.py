# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 22:10:40 CST

from __future__ import annotations

import unittest

from shopping.keyword_builder import KeywordBuilder
from shopping.schemas import ShoppingSearchIntent


class KeywordBuilderTestCase(unittest.TestCase):
    """关键词构建器测试。"""

    def test_build_query_for_replace_window_high_budget(self) -> None:
        builder = KeywordBuilder()
        intent = ShoppingSearchIntent(
            scene="儿童房地铁高配",
            budget_level="high",
            solution_type="replace_window",
            primary_keywords=["隔音窗", "夹胶中空", "儿童房"],
        )

        result = builder.build_query(intent)

        self.assertIn("隔音窗", result)
        self.assertIn("夹胶中空", result)
        self.assertIn("系统窗", result)
        self.assertIn("高配", result)


if __name__ == "__main__":
    unittest.main()

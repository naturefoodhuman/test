# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 22:10:40 CST

from __future__ import annotations

import unittest
from pathlib import Path

from shopping.replay_executor import ReplayShoppingExecutor


class ReplayShoppingExecutorTestCase(unittest.TestCase):
    """回放执行器测试。"""

    def test_search_and_fetch_detail(self) -> None:
        fixture_root = Path(__file__).resolve().parent / "fixtures"
        executor = ReplayShoppingExecutor(fixture_root)

        listings = executor.search("隔音窗 夹胶中空")
        self.assertGreaterEqual(len(listings), 2)

        detail = executor.fetch_detail(listings[0])
        self.assertEqual(detail.frame_spec, "70系统平开窗")
        self.assertEqual(detail.glass_spec, "5+5夹胶+20A+5双层钢化中空玻璃")


if __name__ == "__main__":
    unittest.main()

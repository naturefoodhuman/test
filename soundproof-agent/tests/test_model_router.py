# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 22:10:40 CST

from __future__ import annotations

import unittest
from pathlib import Path

from core.model_router import load_model_router


class ModelRouterTestCase(unittest.TestCase):
    """模型路由加载测试。"""

    def test_load_model_router(self) -> None:
        router = load_model_router(Path(__file__).resolve().parent.parent / "model_router.yaml")
        self.assertEqual(router.get_primary("coordinator"), "qwen3.6:35b-a3b-q8_0")
        self.assertEqual(router.get_primary("shopping_summary"), "qwen3-coder-next:q4_K_M")


if __name__ == "__main__":
    unittest.main()

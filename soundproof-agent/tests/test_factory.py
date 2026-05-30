# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:35:12 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shopping.factory import build_shopping_runtime_bundle


class ShoppingFactoryTestCase(unittest.TestCase):
    """运行时工厂测试。"""

    def test_build_runtime_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            # 动态定位项目根目录（tests 的父目录）
            project_root = Path(__file__).parent.parent
            (root / "config.yaml").write_text((project_root / "config.yaml").read_text(encoding='utf-8'), encoding='utf-8')
            (root / "model_router.yaml").write_text((project_root / "model_router.yaml").read_text(encoding='utf-8'), encoding='utf-8')
            bundle = build_shopping_runtime_bundle(root)
            self.assertEqual(bundle.router.get_primary("shopping_summary"), "qwen3-coder-next:q4_K_M")
            self.assertIsNotNone(bundle.anti_bot_policy)


if __name__ == "__main__":
    unittest.main()
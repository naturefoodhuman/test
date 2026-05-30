# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:16:05 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from config import ShoppingRuntimeConfig
from shopping.diagnostics import build_runtime_diagnostics
from shopping.profile_manager import BrowserProfileManager
from shopping.sqlite_cache import ShoppingCacheStore


class DiagnosticsTestCase(unittest.TestCase):
    """运行时诊断构建测试。"""

    def test_build_runtime_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager = BrowserProfileManager(ShoppingRuntimeConfig(), root)
            manager.ensure_directories()
            (manager.artifact_root / "sample.txt").write_text("hello", encoding="utf-8")

            store = ShoppingCacheStore(manager.cache_db_path)
            store.initialize()
            store.record_event("search", {"query": "隔音窗"})

            payload = build_runtime_diagnostics(
                profile_manager=manager,
                cache_store=store,
                artifact_limit=10,
            )
            self.assertIn("profile_root", payload)
            self.assertIn("recent_event_stats", payload)
            self.assertIn("recent_artifacts", payload)
            self.assertEqual(payload["recent_event_stats"].get("search"), 1)
            self.assertIn("sample.txt", payload["recent_artifacts"])


if __name__ == "__main__":
    unittest.main()

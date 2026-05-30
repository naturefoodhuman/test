# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 16:41:07 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shopping.cache_models import ShoppingRunCache
from shopping.schemas import ShoppingSearchIntent
from shopping.sqlite_cache import ShoppingCacheStore


class ShoppingCacheStoreTestCase(unittest.TestCase):
    """SQLite 缓存测试。"""

    def test_save_and_load_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "shopping_cache.sqlite3"
            store = ShoppingCacheStore(db_path)
            store.initialize()

            run_cache = ShoppingRunCache(
                run_id="run_001",
                search_query="隔音窗 夹胶中空 系统窗",
                search_intent=ShoppingSearchIntent(
                    scene="高架低频卧室",
                    budget_level="medium",
                    solution_type="replace_window",
                    primary_keywords=["隔音窗", "夹胶中空", "系统窗"],
                ),
            )
            store.save_run(run_cache)
            store.record_event("search", {"run_id": "run_001", "query": run_cache.search_query})
            store.record_event("detail", {"run_id": "run_001", "title": "A"})

            loaded = store.get_run("run_001")
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.search_query, "隔音窗 夹胶中空 系统窗")
            self.assertEqual(loaded.search_intent.scene, "高架低频卧室")

            stats = store.summarize_recent_events(3600)
            self.assertEqual(stats.get("search"), 1)
            self.assertEqual(stats.get("detail"), 1)

            logs = store.list_recent_events(limit=10)
            self.assertEqual(len(logs), 2)
            self.assertEqual(logs[0]["event_type"], "detail")

            filtered_logs = store.list_recent_events(limit=10, run_id="run_001")
            self.assertEqual(len(filtered_logs), 2)


if __name__ == "__main__":
    unittest.main()

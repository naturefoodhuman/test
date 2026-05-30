# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 02:04:17 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shopping.app_service import ShoppingApplicationService
from shopping.intent_builder import ConsultationContext
from shopping.replay_executor import ReplayShoppingExecutor
from shopping.sqlite_cache import ShoppingCacheStore


class ShoppingApplicationServiceTestCase(unittest.TestCase):
    """购物应用服务测试。"""

    def test_run_from_consultation_context(self) -> None:
        fixture_root = Path(__file__).resolve().parent / 'fixtures'
        executor = ReplayShoppingExecutor(fixture_root)

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_store = ShoppingCacheStore(Path(temp_dir) / 'shopping_cache.sqlite3')
            service = ShoppingApplicationService(
                executor=executor,
                cache_store=cache_store,
                summary_service=None,
                field_normalizer_service=None,
            )
            snapshot = service.run_from_consultation_context(
                ConsultationContext(
                    scene='高架低频卧室',
                    budget=8000,
                    noise_source='traffic',
                    frequency_profile='low',
                    preferred_solution='replace_window',
                ),
                limit=2,
            )
            self.assertEqual(snapshot.search_query, '隔音窗 系统窗 夹胶 三道密封 临街')
            self.assertEqual(len(snapshot.listing_products), 2)
            self.assertGreaterEqual(len(service.list_history()), 1)
            self.assertEqual(service.list_run_artifacts(snapshot.run_id or ''), snapshot.artifact_names)
            self.assertIsInstance(service.build_artifact_manifest(snapshot.run_id or ''), list)


if __name__ == '__main__':
    unittest.main()

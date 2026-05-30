# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 20:23:45 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shopping.app_service import ShoppingApplicationService
from shopping.cache_models import ShoppingRunCache
from shopping.schemas import ProductComparisonSummary, ShoppingSearchIntent
from shopping.sqlite_cache import ShoppingCacheStore
from shopping.replay_executor import ReplayShoppingExecutor


class ReportFromHistoryTestCase(unittest.TestCase):
    """历史报告导出测试。"""

    def test_build_history_report(self) -> None:
        fixture_root = Path(__file__).resolve().parent / "fixtures"
        executor = ReplayShoppingExecutor(fixture_root)

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_store = ShoppingCacheStore(Path(temp_dir) / "shopping_cache.sqlite3")
            cache_store.initialize()
            run_cache = ShoppingRunCache(
                run_id="run_001",
                search_query="隔音窗 夹胶中空 系统窗",
                search_intent=ShoppingSearchIntent(
                    scene="高架低频卧室",
                    budget_level="medium",
                    solution_type="replace_window",
                    primary_keywords=["隔音窗", "夹胶中空"],
                ),
                summary=ProductComparisonSummary(
                    recommended_option="测试推荐项",
                    reason_summary="测试推荐理由",
                ),
            )
            cache_store.save_run(run_cache)

            service = ShoppingApplicationService(
                executor=executor,
                cache_store=cache_store,
                summary_service=None,
                field_normalizer_service=None,
            )
            report = service.build_history_report("run_001")
            self.assertIsNotNone(report)
            assert report is not None
            self.assertIn("# 购物决策报告", report)
            self.assertIn("测试推荐项", report)


if __name__ == "__main__":
    unittest.main()

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 03:20:12 CST

from __future__ import annotations

import unittest

from shopping.cache_models import ShoppingRunCache
from shopping.history_compare import compare_runs
from shopping.schemas import ProductComparisonSummary, ShoppingSearchIntent, WorkflowStepTrace


class HistoryCompareTestCase(unittest.TestCase):
    """运行对比测试。"""

    def test_compare_runs(self) -> None:
        left = ShoppingRunCache(
            run_id='run_left',
            search_query='隔音窗 夹胶中空',
            search_intent=ShoppingSearchIntent(
                scene='高架低频卧室',
                budget_level='medium',
                solution_type='replace_window',
                primary_keywords=['隔音窗', '夹胶中空'],
            ),
            entries=[],
            summary=ProductComparisonSummary(recommended_option='A', reason_summary='旧结果'),
            step_traces=[WorkflowStepTrace(step='summary', duration_ms=100)],
        )
        right = ShoppingRunCache(
            run_id='run_right',
            search_query='隔音窗 夹胶中空 系统窗',
            search_intent=ShoppingSearchIntent(
                scene='高架低频卧室',
                budget_level='medium',
                solution_type='replace_window',
                primary_keywords=['隔音窗', '夹胶中空', '系统窗'],
            ),
            entries=[],
            summary=ProductComparisonSummary(recommended_option='B', reason_summary='新结果'),
            step_traces=[WorkflowStepTrace(step='summary', duration_ms=180)],
        )

        payload = compare_runs(left, right)
        self.assertTrue(payload['search_query_changed'])
        self.assertTrue(payload['recommended_option_changed'])
        self.assertEqual(payload['step_durations'][0]['delta_ms'], 80)


if __name__ == '__main__':
    unittest.main()

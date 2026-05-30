# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 01:26:58 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shopping.bundle_exporter import ShoppingBundleExporter
from shopping.cache_models import ShoppingRunCache
from shopping.schemas import ProductComparisonSummary, ShoppingSearchIntent, WorkflowStepTrace


class ShoppingBundleExporterTestCase(unittest.TestCase):
    """运行 bundle 导出测试。"""

    def test_export_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_root = root / 'artifacts'
            artifact_root.mkdir(parents=True, exist_ok=True)
            (artifact_root / 'run_001_sample.txt').write_text('hello', encoding='utf-8')

            exporter = ShoppingBundleExporter(artifact_root)
            run_cache = ShoppingRunCache(
                run_id='run_001',
                search_query='隔音窗 夹胶中空 系统窗',
                search_intent=ShoppingSearchIntent(
                    scene='高架低频卧室',
                    budget_level='medium',
                    solution_type='replace_window',
                    primary_keywords=['隔音窗', '夹胶中空'],
                ),
                summary=ProductComparisonSummary(
                    recommended_option='测试推荐项',
                    reason_summary='测试推荐理由',
                ),
                artifact_names=['run_001_sample.txt'],
                workflow_notes=['测试备注'],
                step_traces=[WorkflowStepTrace(step='summary', duration_ms=88)],
            )
            result = exporter.export_run(run_cache, root / 'exported')
            self.assertEqual(result['artifact_count'], 1)
            self.assertTrue((root / 'exported' / 'report.md').exists())
            self.assertTrue((root / 'exported' / 'artifacts' / 'run_001_sample.txt').exists())
            self.assertTrue((root / 'exported' / 'snapshot.json').exists())

    def test_export_run_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_root = root / 'artifacts'
            artifact_root.mkdir(parents=True, exist_ok=True)
            (artifact_root / 'run_002_sample.txt').write_text('hello', encoding='utf-8')

            exporter = ShoppingBundleExporter(artifact_root)
            run_cache = ShoppingRunCache(
                run_id='run_002',
                search_query='隔音窗 夹胶中空 系统窗',
                search_intent=ShoppingSearchIntent(
                    scene='高架低频卧室',
                    budget_level='medium',
                    solution_type='replace_window',
                    primary_keywords=['隔音窗', '夹胶中空'],
                ),
                artifact_names=['run_002_sample.txt'],
            )
            result = exporter.export_run_archive(run_cache, root / 'archives')
            self.assertTrue(result['archive_path'].endswith('.zip'))
            self.assertTrue(Path(result['archive_path']).exists())


if __name__ == '__main__':
    unittest.main()

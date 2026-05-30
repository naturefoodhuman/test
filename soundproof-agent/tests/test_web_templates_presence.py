# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 14:36:08 CST

from __future__ import annotations

import unittest
from pathlib import Path


class WebTemplatesPresenceTestCase(unittest.TestCase):
    """Web 模板存在性测试。"""

    def test_templates_exist(self) -> None:
        root = Path(__file__).resolve().parent.parent / 'src' / 'web' / 'templates'
        self.assertTrue((root / 'base.html').exists())
        self.assertTrue((root / 'dashboard.html').exists())
        self.assertTrue((root / 'run_detail.html').exists())
        self.assertTrue((root / 'run_analysis.html').exists())
        self.assertTrue((root / 'artifact_detail.html').exists())
        self.assertTrue((root / 'artifact_manifest.html').exists())
        self.assertTrue((root / 'tools.html').exists())
        self.assertTrue((root / 'compare_runs.html').exists())
        self.assertTrue((root / 'event_log.html').exists())


if __name__ == '__main__':
    unittest.main()

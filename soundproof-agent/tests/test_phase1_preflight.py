# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 23:00:19 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from config import ShoppingRuntimeConfig
from shopping.preflight import run_phase1_preflight


class Phase1PreflightTestCase(unittest.TestCase):
    """Phase 1 预检查测试。"""

    def test_run_phase1_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ShoppingRuntimeConfig()
            result = run_phase1_preflight(Path(temp_dir), config)

            self.assertEqual(result["platform"], "taobao")
            self.assertTrue(Path(result["profile_root"]).exists())
            self.assertTrue(Path(result["artifact_root"]).exists())
            self.assertTrue(Path(result["cache_db_path"]).parent.exists())


if __name__ == "__main__":
    unittest.main()

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:44:06 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.handoff_snapshot import build_handoff_snapshot


class HandoffSnapshotTestCase(unittest.TestCase):
    """接续快照构建测试。"""

    def test_build_handoff_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            # 动态定位项目根目录（tests 的父目录）
            project_root = Path(__file__).parent.parent
            (root / 'config.yaml').write_text((project_root / 'config.yaml').read_text(encoding='utf-8'), encoding='utf-8')
            (root / 'model_router.yaml').write_text((project_root / 'model_router.yaml').read_text(encoding='utf-8'), encoding='utf-8')
            payload = build_handoff_snapshot(root, artifact_limit=5)
            self.assertEqual(payload['phase'], 'phase1')
            self.assertIn('diagnostics', payload)
            self.assertEqual(payload['shopping_summary_model'], 'qwen3-coder-next:q4_K_M')


if __name__ == '__main__':
    unittest.main()
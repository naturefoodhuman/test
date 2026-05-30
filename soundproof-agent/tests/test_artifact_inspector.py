# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 14:02:18 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shopping.artifact_inspector import artifact_exists, list_artifacts, list_artifacts_for_run, read_artifact_text


class ArtifactInspectorTestCase(unittest.TestCase):
    """产物检查器测试。"""

    def test_list_and_read_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / 'run_001_a.json').write_text('{}', encoding='utf-8')
            (root / 'run_001_b.txt').write_text('hello', encoding='utf-8')
            (root / 'run_002_c.txt').write_text('world', encoding='utf-8')

            items = list_artifacts(root)
            self.assertEqual(set(items), {'run_001_a.json', 'run_001_b.txt', 'run_002_c.txt'})
            self.assertEqual(read_artifact_text(root, 'run_001_b.txt'), 'hello')
            self.assertIsNone(read_artifact_text(root, 'missing.txt'))
            self.assertEqual(set(list_artifacts_for_run(root, 'run_001')), {'run_001_a.json', 'run_001_b.txt'})
            self.assertTrue(artifact_exists(root, 'run_002_c.txt'))
            self.assertFalse(artifact_exists(root, 'missing.txt'))


if __name__ == '__main__':
    unittest.main()

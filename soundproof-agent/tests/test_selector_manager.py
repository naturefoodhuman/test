# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 02:31:18 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shopping.selector_manager import (
    backup_selector_override,
    list_selector_override_backups,
    read_selector_override_backup,
    read_selector_override_text,
    restore_selector_override_backup,
    validate_selector_override,
    write_selector_override_text,
)


class SelectorManagerTestCase(unittest.TestCase):
    """选择器 override 管理测试。"""

    def test_validate_selector_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / 'selector_overrides.yaml'
            write_selector_override_text(path, 'detail:\n  title_selectors:\n    - "h1.custom"\n')
            result = validate_selector_override(path)
            self.assertTrue(result['exists'])
            self.assertTrue(result['valid'])
            self.assertEqual(read_selector_override_text(path).strip(), 'detail:\n  title_selectors:\n    - "h1.custom"')
            backup = backup_selector_override(path)
            self.assertIsNotNone(backup)
            assert backup is not None
            self.assertTrue(Path(backup).exists())
            backups = list_selector_override_backups(path, limit=10)
            self.assertEqual(len(backups), 1)
            preview = read_selector_override_backup(path, backups[0])
            self.assertIn('h1.custom', preview or '')
            write_selector_override_text(path, 'detail:\n  title_selectors:\n    - "changed"\n')
            restored = restore_selector_override_backup(path, backups[0])
            self.assertIsNotNone(restored)
            self.assertIn('h1.custom', read_selector_override_text(path) or '')


if __name__ == '__main__':
    unittest.main()

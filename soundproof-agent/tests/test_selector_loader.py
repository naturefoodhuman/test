# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 01:18:32 CST

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from shopping.selector_loader import export_default_selector_profile, load_taobao_selector_profile


class SelectorLoaderTestCase(unittest.TestCase):
    """选择器覆盖加载测试。"""

    def test_load_and_export_selector_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = export_default_selector_profile(root / 'selector_overrides.yaml')
            self.assertTrue(output.exists())

            output.write_text(
                'detail:\n  title_selectors:\n    - \'h1.custom\'\n',
                encoding='utf-8',
            )
            profile = load_taobao_selector_profile(output)
            self.assertEqual(profile.detail.title_selectors, ['h1.custom'])
            self.assertTrue(profile.search.card_candidates)


if __name__ == '__main__':
    unittest.main()

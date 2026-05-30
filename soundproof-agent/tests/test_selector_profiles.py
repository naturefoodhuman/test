# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:44:06 CST

from __future__ import annotations

import unittest

from shopping.selector_profiles import TAOBAO_SELECTOR_PROFILE


class SelectorProfilesTestCase(unittest.TestCase):
    """选择器配置测试。"""

    def test_selector_profile_not_empty(self) -> None:
        self.assertTrue(TAOBAO_SELECTOR_PROFILE.search.card_candidates)
        self.assertTrue(TAOBAO_SELECTOR_PROFILE.detail.title_selectors)
        self.assertTrue(TAOBAO_SELECTOR_PROFILE.review.review_tab_selectors)


if __name__ == '__main__':
    unittest.main()

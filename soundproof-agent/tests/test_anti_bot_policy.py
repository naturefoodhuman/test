# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:55:19 CST

from __future__ import annotations

import unittest

from security.anti_bot_policy import ShoppingAntiBotPolicy


class ShoppingAntiBotPolicyTestCase(unittest.TestCase):
    """反爬风险策略测试。"""

    def test_evaluate_search_and_detail_batch(self) -> None:
        policy = ShoppingAntiBotPolicy(max_detail_pages_per_run=5, max_searches_per_hour=20, max_review_fetches_per_run=3)

        search_decision = policy.evaluate_search(searches_in_last_hour=18)
        self.assertTrue(search_decision.allowed)
        self.assertGreater(search_decision.suggested_delay_seconds, 2.5)

        detail_decision = policy.evaluate_detail_batch(requested_detail_pages=6)
        self.assertFalse(detail_decision.allowed)

        review_decision = policy.evaluate_review_batch(requested_review_fetches=4)
        self.assertFalse(review_decision.allowed)

        captcha_decision = policy.should_stop_on_captcha()
        self.assertFalse(captcha_decision.allowed)


if __name__ == "__main__":
    unittest.main()

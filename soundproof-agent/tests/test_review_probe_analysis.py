# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 16:12:18 CST

from __future__ import annotations

import unittest

from shopping.review_probe_analysis import analyze_review_probe


class ReviewProbeAnalysisTestCase(unittest.TestCase):
    """评论探针分析测试。"""

    def test_review_probe_ready(self) -> None:
        payload = {
            "risk": {"detected": False},
            "review_count": 4,
            "with_images": 2,
            "anonymous_count": 1,
            "average_length": 48,
            "selector_counts": [{"selector": "div", "count": 5}],
        }
        result = analyze_review_probe(payload)
        self.assertEqual(result["readiness"], "ready")
        self.assertEqual(result["positive_selector_count"], 1)

    def test_review_probe_needs_fix(self) -> None:
        payload = {
            "risk": {"detected": False},
            "review_count": 0,
            "with_images": 0,
            "anonymous_count": 0,
            "average_length": 0,
            "selector_counts": [{"selector": "div", "count": 0}],
        }
        result = analyze_review_probe(payload)
        self.assertEqual(result["readiness"], "needs_fix")
        self.assertTrue(result["suggestions"])


if __name__ == '__main__':
    unittest.main()

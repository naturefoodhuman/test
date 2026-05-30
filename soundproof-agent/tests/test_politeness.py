# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:55:19 CST

from __future__ import annotations

import unittest

from security.politeness import compute_polite_delay


class PolitenessTestCase(unittest.TestCase):
    """节流延时计算测试。"""

    def test_compute_polite_delay(self) -> None:
        self.assertEqual(compute_polite_delay(2.5), 2.5)
        self.assertEqual(compute_polite_delay(2.5, multiplier=1.2), 3.0)
        self.assertEqual(compute_polite_delay(2.5, multiplier=1.0, extra_seconds=0.5), 3.0)


if __name__ == "__main__":
    unittest.main()

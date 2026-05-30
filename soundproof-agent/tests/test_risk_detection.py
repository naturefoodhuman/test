# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:05:58 CST

from __future__ import annotations

import unittest

from shopping.risk_detection import detect_page_risk


class RiskDetectionTestCase(unittest.TestCase):
    """页面风险识别测试。"""

    def test_detect_captcha_signal(self) -> None:
        report = detect_page_risk("请拖动滑块完成验证后继续访问")
        self.assertTrue(report.detected)
        self.assertEqual(report.risk_type, "captcha")

    def test_detect_access_limited_signal(self) -> None:
        report = detect_page_risk("访问过于频繁，请稍后再试")
        self.assertTrue(report.detected)
        self.assertEqual(report.risk_type, "access_limited")

    def test_detect_safe_page(self) -> None:
        report = detect_page_risk("70系统平开窗 5+5夹胶+20A+5中空玻璃 三道密封")
        self.assertFalse(report.detected)


if __name__ == "__main__":
    unittest.main()

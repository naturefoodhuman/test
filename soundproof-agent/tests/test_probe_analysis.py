# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 17:30:00 CST

from __future__ import annotations

import unittest

from shopping.probe_analysis import analyze_detail_probe, analyze_search_probe


class ProbeAnalysisTestCase(unittest.TestCase):
    """探针结果分析测试。"""

    def test_analyze_search_probe(self) -> None:
        """测试搜索页探针分析（正常情况）。"""
        payload = {
            "risk": {"detected": False},
            "selector_counts": [{"selector": "div[class*=Card]", "count": 3}],
            "records_count": 2,
            "body_length": 500,
            "records_preview": [
                {"title": "隔音窗 夹胶中空", "price_text": "718元/㎡", "detail_url": "https://item.taobao.com/item.htm?id=123"},
            ],
        }
        result = analyze_search_probe(payload)
        self.assertEqual(result["readiness"], "ready")
        self.assertIn("suggestions", result)
        self.assertIn("quality_analysis", result)

    def test_analyze_search_probe_with_risk(self) -> None:
        """测试搜索页探针分析（遇到风控）。"""
        payload = {
            "risk": {"detected": True, "risk_type": "captcha", "signals": ["验证码"]},
            "selector_counts": [],
            "records_count": 0,
            "body_length": 100,
        }
        result = analyze_search_probe(payload)
        self.assertEqual(result["readiness"], "blocked")
        self.assertTrue(any("风控" in s or "验证码" in s for s in result["suggestions"]))

    def test_analyze_search_probe_no_selectors(self) -> None:
        """测试搜索页探针分析（选择器全部未命中）。"""
        payload = {
            "risk": {"detected": False},
            "selector_counts": [{"selector": "div[class*=Card]", "count": 0}],
            "records_count": 0,
            "body_length": 500,
        }
        result = analyze_search_probe(payload)
        self.assertEqual(result["readiness"], "needs_fix")
        self.assertTrue(any("选择器" in s for s in result["suggestions"]))

    def test_analyze_search_probe_quality_analysis(self) -> None:
        """测试搜索页探针的质量分析功能。"""
        payload = {
            "risk": {"detected": False},
            "selector_counts": [{"selector": "div.item", "count": 5}],
            "records_count": 5,
            "body_length": 800,
            "records_preview": [
                {"title": "隔音窗 专业定制", "price_text": "500元/㎡"},
                {"title": "系统窗 夹胶玻璃", "price_text": "720元/㎡"},
                {"title": "密封窗 双层中空", "price_text": "650元/㎡"},
            ],
        }
        result = analyze_search_probe(payload)
        self.assertIn("quality_analysis", result)
        self.assertIn("price_range", result)
        self.assertEqual(result["quality_analysis"]["price_coverage"], 1.0)

    def test_analyze_detail_probe(self) -> None:
        """测试详情页探针分析（正常情况）。"""
        payload = {
            "risk": {"detected": False},
            "title_candidates": [{"selector": "h1", "text": "隔音窗 70系统平开窗"}],
            "shop_candidates": [{"selector": "a[href*=shop]", "text": "门窗旗舰店"}],
            "price_candidates": [{"selector": "[class*=price]", "text": "718元/㎡"}],
            "body_length": 600,
        }
        result = analyze_detail_probe(payload)
        self.assertEqual(result["readiness"], "ready")
        self.assertIn("suggestions", result)
        self.assertIn("field_priority", result)

    def test_analyze_detail_probe_with_risk(self) -> None:
        """测试详情页探针分析（遇到风控）。"""
        payload = {
            "risk": {"detected": True, "risk_type": "access_limited", "signals": ["访问受限"]},
            "title_candidates": [],
            "shop_candidates": [],
            "price_candidates": [],
            "body_length": 50,
        }
        result = analyze_detail_probe(payload)
        self.assertEqual(result["readiness"], "blocked")
        self.assertTrue(any("风控" in s or "验证码" in s for s in result["suggestions"]))

    def test_analyze_detail_probe_missing_fields(self) -> None:
        """测试详情页探针分析（多个字段缺失）。"""
        payload = {
            "risk": {"detected": False},
            "title_candidates": [],
            "shop_candidates": [],
            "price_candidates": [],
            "body_length": 200,
        }
        result = analyze_detail_probe(payload)
        self.assertEqual(result["readiness"], "needs_fix")
        self.assertIn("priority_fixes", result)
        self.assertTrue(len(result["priority_fixes"]) > 0)

    def test_analyze_detail_probe_field_priority(self) -> None:
        """测试详情页探针分析的字段优先级。"""
        payload = {
            "risk": {"detected": False},
            "title_candidates": [{"selector": "h1", "text": "标题文本"}],
            "shop_candidates": [],
            "price_candidates": [{"selector": "[class*=price]", "text": "718元/㎡"}],
            "body_length": 600,
        }
        result = analyze_detail_probe(payload)
        self.assertIn("field_priority", result)
        self.assertTrue(len(result["field_priority"]) > 0)
        # 店铺名为缺失状态
        shop_priority = next((f for f in result["field_priority"] if f["field"] == "shop_name"), None)
        self.assertIsNotNone(shop_priority)
        self.assertEqual(shop_priority["status"], "missing")

    def test_analyze_detail_probe_quality_score(self) -> None:
        """测试详情页探针分析的质量评分。"""
        # 高质量情况
        payload_high = {
            "risk": {"detected": False},
            "title_candidates": [{"selector": "h1", "text": "标题"}],
            "shop_candidates": [{"selector": "a", "text": "店铺"}],
            "price_candidates": [{"selector": "[class*=price]", "text": "718元/㎡"}],
            "body_length": 600,
        }
        result_high = analyze_detail_probe(payload_high)
        self.assertIn("quality_score", result_high)
        self.assertGreaterEqual(result_high["quality_score"], 0.8)

        # 低质量情况
        payload_low = {
            "risk": {"detected": False},
            "title_candidates": [],
            "shop_candidates": [],
            "price_candidates": [],
            "body_length": 100,
        }
        result_low = analyze_detail_probe(payload_low)
        self.assertLess(result_low["quality_score"], 0.5)


if __name__ == '__main__':
    unittest.main()
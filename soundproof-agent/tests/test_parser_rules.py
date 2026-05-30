# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 22:10:40 CST

from __future__ import annotations

import unittest

from shopping.parser_rules import build_product_detail_from_text


class ParserRulesTestCase(unittest.TestCase):
    """确定性解析规则测试。"""

    def test_build_product_detail_from_text(self) -> None:
        detail = build_product_detail_from_text(
            title="断桥铝系统窗卧室隔音窗定制",
            raw_text="70系统平开窗 5+5夹胶+20A+5双层钢化中空玻璃 三道密封 HOPO执手 包测量安装拆旧",
            price_text="798元/㎡",
            shop_name="XX门窗旗舰店",
        )

        self.assertEqual(detail.frame_spec, "70系统平开窗")
        self.assertEqual(detail.glass_spec, "5+5夹胶+20A+5双层钢化中空玻璃")
        self.assertEqual(detail.seal_spec, "三道密封")
        self.assertEqual(detail.hardware_keyword, "HOPO执手")
        self.assertIn("测量", detail.installation_services)
        self.assertIn("安装", detail.installation_services)
        self.assertIn("拆旧", detail.installation_services)


if __name__ == "__main__":
    unittest.main()

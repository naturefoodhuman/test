# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 17:30:00 CST

from __future__ import annotations

import unittest

from shopping.extraction_utils import (
    choose_best_body_text,
    choose_best_price_text,
    choose_best_shop_name,
    choose_best_title,
)


class ExtractionUtilsTestCase(unittest.TestCase):
    """详情页提取工具测试。"""

    def test_choose_best_title(self) -> None:
        result = choose_best_title(["隔音窗", "70系统平开窗 5+5夹胶+20A+5中空玻璃"])
        self.assertEqual(result, "70系统平开窗 5+5夹胶+20A+5中空玻璃")

    def test_choose_best_title_with_page_title(self) -> None:
        """测试使用 page.title 作为回退。"""
        result = choose_best_title([], page_title="70系统平开窗 隔音窗")
        self.assertEqual(result, "70系统平开窗 隔音窗")

    def test_choose_best_title_empty_candidates(self) -> None:
        """测试候选为空时使用 page.title。"""
        result = choose_best_title([], page_title=None)
        self.assertIsNone(result)

    def test_choose_best_title_length_filter(self) -> None:
        """测试标题长度过滤。"""
        result = choose_best_title(["短", "这是一个更长的产品标题文本"])
        self.assertEqual(result, "这是一个更长的产品标题文本")

    def test_choose_best_shop_name(self) -> None:
        result = choose_best_shop_name(["XX门窗旗舰店", "客服", "首页"])
        self.assertEqual(result, "XX门窗旗舰店")

    def test_choose_best_shop_name_with_body_fallback(self) -> None:
        """测试从 body 文本中正则匹配店铺名作为回退。"""
        body = "产品详情 XX静音门窗旗舰店 专业定制 安装服务"
        result = choose_best_shop_name([], body_text=body)
        self.assertEqual(result, "XX静音门窗旗舰店")

    def test_choose_best_shop_name_preferred_keywords(self) -> None:
        """测试店铺名优先选择包含关键词的候选。"""
        result = choose_best_shop_name(["某店", "某某门窗旗舰店", "官方店"])
        self.assertEqual(result, "某某门窗旗舰店")

    def test_choose_best_price_text(self) -> None:
        result = choose_best_price_text(["¥ 718元/㎡", "其他文字"], body_text="")
        self.assertEqual(result, "718元/㎡")

    def test_choose_best_price_text_body_fallback(self) -> None:
        """测试从 body 文本中提取价格作为回退。"""
        result = choose_best_price_text([], body_text="隔音窗价格：650元/㎡，包含安装服务")
        self.assertEqual(result, "650元/㎡")

    def test_choose_best_price_text_with_unit(self) -> None:
        """测试价格提取包含单位。"""
        result = choose_best_price_text(["800元/平米"], body_text="")
        self.assertIn("元", result)

    def test_choose_best_body_text(self) -> None:
        result = choose_best_body_text(["短文本", "这是一个更长的详情正文，包含更多产品信息和安装说明"])
        self.assertEqual(result, "这是一个更长的详情正文，包含更多产品信息和安装说明")

    def test_choose_best_body_text_min_length(self) -> None:
        """测试正文提取的最小长度要求。"""
        candidates = ["短", "中等长度文本"]
        result = choose_best_body_text(candidates, min_length=100)
        self.assertEqual(result, "中等长度文本")

    def test_choose_best_body_text_empty(self) -> None:
        """测试空候选列表。"""
        result = choose_best_body_text([])
        self.assertEqual(result, "")

    def test_choose_best_title_all_short(self) -> None:
        """测试所有候选都很短时的处理。"""
        result = choose_best_title(["短", "更短"])
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
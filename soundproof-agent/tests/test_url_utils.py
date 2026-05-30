# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:28:41 CST

from __future__ import annotations

import unittest

from shopping.url_utils import canonicalize_detail_url


class UrlUtilsTestCase(unittest.TestCase):
    """详情页 URL 规范化测试。"""

    def test_canonicalize_detail_url(self) -> None:
        url = canonicalize_detail_url(
            "http://item.taobao.com/item.htm?id=123&spm=aaa&skuId=456#detail"
        )
        self.assertEqual(url, "https://item.taobao.com/item.htm?id=123&skuId=456")


if __name__ == "__main__":
    unittest.main()

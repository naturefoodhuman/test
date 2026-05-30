# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:28:41 CST

from __future__ import annotations

import unittest

from security.url_guard import ensure_safe_readonly_url, is_allowed_host
from shopping.errors import ShoppingExecutionError


class UrlGuardTestCase(unittest.TestCase):
    """URL 风险控制测试。"""

    def test_allowed_host(self) -> None:
        self.assertTrue(is_allowed_host("item.taobao.com"))
        self.assertTrue(is_allowed_host("detail.tmall.com"))
        self.assertFalse(is_allowed_host("example.com"))

    def test_ensure_safe_readonly_url(self) -> None:
        safe = ensure_safe_readonly_url("https://item.taobao.com/item.htm?id=123&spm=abc")
        self.assertEqual(safe, "https://item.taobao.com/item.htm?id=123")

    def test_block_dangerous_url(self) -> None:
        with self.assertRaises(ShoppingExecutionError):
            ensure_safe_readonly_url("https://www.taobao.com/cart/add")


if __name__ == "__main__":
    unittest.main()

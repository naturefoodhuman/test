# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-30 14:10:00 CST
"""TaobaoPlaywrightExecutor 的 dry-run 测试（不依赖真实 Playwright）。

测试策略：
- 用 FakePage / FakeContext / FakeCtxManager 替换执行器内部的 _open_context()，
  让所有 page.goto / page.evaluate / page.content / page.locator 等调用都拿到可控的假数据。
- 验证：搜索抽取、详情抽取、风险中断、选择器回退、节流被调用、探针接口的 payload 形状。

不覆盖的部分（需要真实联调）：
- 真实淘宝页面的 DOM 结构（仍然是脆弱的）；
- Playwright 浏览器启动流程。
"""

from __future__ import annotations

import contextlib
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from config import ShoppingRuntimeConfig
from shopping.errors import ShoppingRiskDetectedError
from shopping.playwright_executor import TaobaoPlaywrightExecutor
from shopping.schemas import ListingProduct


class _FakeLocator:
    """一个最小可用的 Playwright Locator 替身。"""

    def __init__(self, text: str | None) -> None:
        self._text = text

    @property
    def first(self) -> "_FakeLocator":
        return self

    def inner_text(self, timeout: int = 1000) -> str:
        if self._text is None:
            raise RuntimeError("selector not matched")
        return self._text


class _FakePage:
    """一个最小可用的 Playwright Page 替身。"""

    def __init__(
        self,
        *,
        body_text: str = "",
        listing_records_primary: list[dict[str, Any]] | None = None,
        listing_records_fallback: list[dict[str, Any]] | None = None,
        selector_counts: list[dict[str, Any]] | None = None,
        selector_text_map: dict[str, str] | None = None,
        page_title_text: str = "",
        html: str = "<html></html>",
        login_payload: dict[str, Any] | None = None,
    ) -> None:
        self.body_text = body_text
        self.listing_records_primary = listing_records_primary or []
        self.listing_records_fallback = listing_records_fallback or []
        self.selector_counts = selector_counts or []
        self.selector_text_map = selector_text_map or {}
        self.page_title_text = page_title_text
        self._html = html
        self._login_payload = login_payload or {
            "is_logged_in": True,
            "body_preview": body_text[:200],
            "nickname_candidates": [],
            "login_hint_present": False,
        }
        self.goto_calls: list[tuple[str, dict]] = []
        self.evaluate_calls: list[str] = []
        self.wait_calls: list[int] = []
        self.screenshot_calls: list[str] = []
        self._primary_evaluate_yielded = False

    # ===== Playwright API 表面 =====

    def goto(self, url: str, *, wait_until: str = "load", timeout: int = 60000) -> None:
        self.goto_calls.append((url, {"wait_until": wait_until, "timeout": timeout}))

    def wait_for_timeout(self, ms: int) -> None:
        self.wait_calls.append(ms)

    def content(self) -> str:
        return self._html

    def title(self) -> str:
        return self.page_title_text

    def screenshot(self, *, path: str, full_page: bool = False) -> None:
        # 写一个空文件，模拟截图行为
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(b"")
        self.screenshot_calls.append(path)

    def evaluate(self, script: str, *args, **kwargs) -> Any:
        self.evaluate_calls.append(script)

        # 识别脚本类型：
        # - 列表提取脚本：包含 "cardSelectors"
        # - 选择器命中计数脚本：包含 "selectors.map((selector) => ({"
        # - 登录态判定脚本：包含 "is_logged_in"
        # - 滚动脚本：包含 "scrollBy"
        if "scrollBy" in script:
            return None
        if "is_logged_in" in script:
            return self._login_payload
        if "cardSelectors" in script:
            # 第一次返回 primary，第二次返回 fallback
            if not self._primary_evaluate_yielded:
                self._primary_evaluate_yielded = True
                return list(self.listing_records_primary)
            return list(self.listing_records_fallback)
        if "selectors.map" in script:
            return list(self.selector_counts)
        return []

    def locator(self, selector: str) -> _FakeLocator:
        # 优先用显式 map；否则对 "body" 选择器回落到 body_text；其余返回 None（不匹配）。
        if selector in self.selector_text_map:
            return _FakeLocator(self.selector_text_map[selector])
        if selector.strip().lower() == "body":
            return _FakeLocator(self.body_text)
        return _FakeLocator(None)


class _FakeContext:
    def __init__(self, page: _FakePage) -> None:
        self.pages = [page]

    def new_page(self) -> _FakePage:
        return self.pages[0]

    def close(self) -> None:
        pass


@contextlib.contextmanager
def _fake_context_manager(page: _FakePage):
    yield _FakeContext(page)


def _make_executor(tmp_root: Path, *, enforce_delay: bool = False) -> TaobaoPlaywrightExecutor:
    cfg = ShoppingRuntimeConfig()
    cfg.headed = False
    cfg.anti_bot.enforce_delay = enforce_delay
    cfg.anti_bot.base_delay_seconds = 0.01  # 测试用，不真等
    return TaobaoPlaywrightExecutor(cfg, tmp_root)


def _patch_open_context(executor: TaobaoPlaywrightExecutor, page: _FakePage):
    """把 executor._open_context 替换为 fake 上下文管理器。"""

    return patch.object(executor, "_open_context", lambda: _fake_context_manager(page))


class TaobaoPlaywrightExecutorDryRunTestCase(unittest.TestCase):
    """TaobaoPlaywrightExecutor 在 mock page 上的 dry-run 测试。"""

    def test_search_returns_structured_listing(self) -> None:
        """正常搜索：mock 列表脚本返回 2 条记录，应抽取出 ListingProduct。"""

        with tempfile.TemporaryDirectory() as tmp:
            executor = _make_executor(Path(tmp))
            page = _FakePage(
                body_text="搜索结果页 正常",
                listing_records_primary=[
                    {
                        "title": "70系统平开窗 5+5夹胶+20A+5双层钢化中空玻璃",
                        "detail_url": "https://item.taobao.com/item.htm?id=111",
                        "price_text": "718元/㎡",
                        "sales_text": "已售300+",
                        "shop_name": "XX门窗旗舰店",
                    },
                    {
                        "title": "四玻双夹胶单中空 高配隔音窗",
                        "detail_url": "https://item.taobao.com/item.htm?id=222",
                        "price_text": "980元/㎡",
                        "sales_text": "已售90+",
                        "shop_name": "YY高配门窗店",
                    },
                ],
            )
            with _patch_open_context(executor, page):
                products = executor.search("隔音窗 夹胶中空", limit=5)
            self.assertEqual(len(products), 2)
            self.assertEqual(products[0].source_rank, 1)
            self.assertEqual(products[1].source_rank, 2)
            self.assertTrue(products[0].detail_url.startswith("https://item.taobao.com/"))
            # 截图与 html / json artifact 都应该落盘
            artifacts = executor.get_recent_artifact_names()
            self.assertTrue(any(name.endswith(".html") for name in artifacts))
            self.assertTrue(any(name.endswith(".json") for name in artifacts))

    def test_search_falls_back_to_secondary_selectors(self) -> None:
        """主选择器返回空，回退选择器返回 1 条 → 仍能拿到一个候选。"""

        with tempfile.TemporaryDirectory() as tmp:
            executor = _make_executor(Path(tmp))
            page = _FakePage(
                body_text="正常",
                listing_records_primary=[],  # primary 空
                listing_records_fallback=[
                    {
                        "title": "回退选择器命中的隔音窗 5+5夹胶",
                        "detail_url": "https://item.taobao.com/item.htm?id=333",
                        "price_text": "650元/㎡",
                        "sales_text": "",
                        "shop_name": "",
                    }
                ],
            )
            with _patch_open_context(executor, page):
                products = executor.search("隔音窗", limit=5)
            self.assertEqual(len(products), 1)
            self.assertEqual(products[0].title.startswith("回退选择器"), True)

    def test_search_aborts_on_risk_signal(self) -> None:
        """搜索页 body 文本里出现验证码关键词 → 应抛 ShoppingRiskDetectedError。"""

        with tempfile.TemporaryDirectory() as tmp:
            executor = _make_executor(Path(tmp))
            page = _FakePage(
                body_text="请完成验证 滑块 验证码",  # 触发 captcha
                listing_records_primary=[],
            )
            with _patch_open_context(executor, page):
                with self.assertRaises(ShoppingRiskDetectedError):
                    executor.search("隔音窗", limit=5)
            # 应该有 risk artifact 写出来
            self.assertTrue(any("risk" in name for name in executor.get_recent_artifact_names()))

    def test_fetch_detail_extracts_fields(self) -> None:
        """详情页：mock title/shop/price 选择器命中，应返回带字段的 ProductDetail。"""

        with tempfile.TemporaryDirectory() as tmp:
            executor = _make_executor(Path(tmp))
            # 用真实选择器里第一个，让 fake page 的 selector_text_map 命中
            title_selector = executor.selector_profile.detail.title_selectors[0]
            price_selector = executor.selector_profile.detail.price_selectors[0]
            shop_selector = executor.selector_profile.detail.shop_name_selectors[0]
            body_selector = executor.selector_profile.detail.body_selectors[0]

            page = _FakePage(
                body_text="详情页正文：四玻双夹胶单中空 108系统窗 四道密封 价格980元",
                selector_text_map={
                    title_selector: "四玻双夹胶单中空 高配隔音窗",
                    price_selector: "980元/㎡",
                    shop_selector: "YY高配门窗店",
                    body_selector: "详情页正文：四玻双夹胶单中空 108系统窗 四道密封 价格980元",
                },
                page_title_text="淘宝-四玻双夹胶单中空",
            )
            listing = ListingProduct(
                title="四玻双夹胶单中空 高配隔音窗",
                detail_url="https://item.taobao.com/item.htm?id=222",
                price_text=None,
                shop_name=None,
                source_rank=1,
            )
            with _patch_open_context(executor, page):
                detail = executor.fetch_detail(listing)
            self.assertEqual(detail.title, "四玻双夹胶单中空 高配隔音窗")
            self.assertEqual(detail.price_text, "980元/㎡")
            self.assertEqual(detail.shop_name, "YY高配门窗店")
            self.assertTrue(detail.detail_url.startswith("https://item.taobao.com/"))
            self.assertIn("四玻", detail.raw_spec_text or "")

    def test_fetch_detail_aborts_on_risk_signal(self) -> None:
        """详情页文本含 captcha 信号 → 中断。"""

        with tempfile.TemporaryDirectory() as tmp:
            executor = _make_executor(Path(tmp))
            page = _FakePage(body_text="请完成验证 滑块")
            listing = ListingProduct(
                title="无所谓",
                detail_url="https://item.taobao.com/item.htm?id=999",
                source_rank=1,
            )
            with _patch_open_context(executor, page):
                with self.assertRaises(ShoppingRiskDetectedError):
                    executor.fetch_detail(listing)

    def test_probe_search_query_payload_shape(self) -> None:
        """probe_search_query 应返回 selector_counts / records / analysis 等字段。"""

        with tempfile.TemporaryDirectory() as tmp:
            executor = _make_executor(Path(tmp))
            page = _FakePage(
                body_text="搜索结果页 正常",
                listing_records_primary=[
                    {
                        "title": "70系统平开窗 5+5夹胶",
                        "detail_url": "https://item.taobao.com/item.htm?id=1",
                        "price_text": "718元/㎡",
                        "sales_text": "",
                        "shop_name": "",
                    }
                ],
                selector_counts=[
                    {"selector": "div.Card--doubleCard", "count": 12},
                    {"selector": "div.Card--singleCard", "count": 0},
                ],
            )
            with _patch_open_context(executor, page):
                payload = executor.probe_search_query("隔音窗", wait_after_load_ms=10)
            self.assertEqual(payload["query"], "隔音窗")
            self.assertIn("selector_counts", payload)
            self.assertEqual(payload["records_count"], 1)
            self.assertIn("analysis", payload)
            self.assertIn("used_fallback", payload)

    def test_probe_search_query_marks_fallback_used(self) -> None:
        """主选择器空、回退选择器命中 → payload.used_fallback = True。"""

        with tempfile.TemporaryDirectory() as tmp:
            executor = _make_executor(Path(tmp))
            page = _FakePage(
                body_text="正常",
                listing_records_primary=[],
                listing_records_fallback=[
                    {
                        "title": "回退命中 5+5夹胶",
                        "detail_url": "https://item.taobao.com/item.htm?id=2",
                        "price_text": "",
                        "sales_text": "",
                        "shop_name": "",
                    }
                ],
            )
            with _patch_open_context(executor, page):
                payload = executor.probe_search_query("隔音窗", wait_after_load_ms=10)
            self.assertTrue(payload["used_fallback"])
            self.assertEqual(payload["records_count"], 1)

    def test_probe_detail_url_payload_shape(self) -> None:
        """probe_detail_url 应返回 title/shop/price 候选与 analysis。"""

        with tempfile.TemporaryDirectory() as tmp:
            executor = _make_executor(Path(tmp))
            title_selector = executor.selector_profile.detail.title_selectors[0]
            page = _FakePage(
                body_text="正文",
                selector_text_map={
                    title_selector: "70系统平开窗 5+5夹胶",
                },
            )
            with _patch_open_context(executor, page):
                payload = executor.probe_detail_url(
                    "https://item.taobao.com/item.htm?id=111",
                    wait_after_load_ms=10,
                )
            self.assertIn("title_candidates", payload)
            self.assertIn("shop_candidates", payload)
            self.assertIn("price_candidates", payload)
            self.assertIn("analysis", payload)
            self.assertTrue(any("70系统平开窗" in c["text"] for c in payload["title_candidates"]))

    def test_enforce_delay_triggers_wait_for_timeout(self) -> None:
        """enforce_delay=True 时，节流应至少触发一次 wait_for_timeout。"""

        with tempfile.TemporaryDirectory() as tmp:
            executor = _make_executor(Path(tmp), enforce_delay=True)
            page = _FakePage(
                body_text="正常",
                listing_records_primary=[
                    {
                        "title": "测试候选 5+5夹胶",
                        "detail_url": "https://item.taobao.com/item.htm?id=1",
                        "price_text": "",
                        "sales_text": "",
                        "shop_name": "",
                    }
                ],
            )
            with _patch_open_context(executor, page):
                executor.search("隔音窗", limit=5)
            # 至少一次 _paced_wait 应该走到 wait_for_timeout
            self.assertGreaterEqual(len(page.wait_calls), 1)

    def test_check_login_status_returns_payload(self) -> None:
        """check_login_status 应返回登录态 payload，且写出 artifact。"""

        with tempfile.TemporaryDirectory() as tmp:
            executor = _make_executor(Path(tmp))
            page = _FakePage(
                body_text="我的淘宝 退出",
                login_payload={
                    "is_logged_in": True,
                    "body_preview": "我的淘宝 退出",
                    "nickname_candidates": ["昵称X"],
                    "login_hint_present": False,
                },
            )
            with _patch_open_context(executor, page):
                payload = executor.check_login_status()
            self.assertTrue(payload["is_logged_in"])
            self.assertIn("login_check.json", "\n".join(executor.get_recent_artifact_names()))


if __name__ == "__main__":
    unittest.main()

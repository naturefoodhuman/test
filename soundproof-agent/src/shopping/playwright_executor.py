# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 17:30:00 CST

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from config import ShoppingRuntimeConfig
from security.politeness import compute_polite_delay
from security.url_guard import ensure_safe_readonly_url
from shopping.errors import ShoppingRiskDetectedError
from shopping.executor_interface import ShoppingExecutor
from shopping.extraction_utils import choose_best_body_text, choose_best_price_text, choose_best_shop_name, choose_best_title
from shopping.parser_rules import build_product_detail_from_text
from shopping.risk_detection import detect_page_risk
from shopping.schemas import ListingProduct, ProductDetail
from shopping.selector_loader import load_taobao_selector_profile
from shopping.selector_profiles import TaobaoSelectorProfile
from shopping.url_utils import canonicalize_detail_url


class TaobaoPlaywrightExecutor(ShoppingExecutor):
    """淘宝 Playwright 执行器。

    设计原则：
    1. 登录态复用依赖 persistent context；
    2. 所有真实页面内容都优先落盘，便于后续排查页面改版；
    3. 抽取先追求"够用且稳"，不追求一口气抓全所有字段；
    4. 选择器配置可外部覆盖，真实联调时可减少改代码频率；
    5. 优先使用主选择器，失败时自动回退到备选选择器。
    """

    SEARCH_URL_TEMPLATE = "https://s.taobao.com/search?q={query}"

    def __init__(self, runtime_config: ShoppingRuntimeConfig, project_root: str | Path) -> None:
        self.runtime_config = runtime_config
        self.project_root = Path(project_root)
        self.artifact_root = self.project_root / self.runtime_config.artifact_root
        self.profile_root = self.project_root / self.runtime_config.browser_profile_root / "taobao"
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.profile_root.mkdir(parents=True, exist_ok=True)
        self._current_run_id: str | None = None
        self._recent_artifacts: list[str] = []
        self.selector_profile: TaobaoSelectorProfile = load_taobao_selector_profile(
            self.project_root / self.runtime_config.selector_override_path
        )

    def start_run_context(self, run_id: str, search_query: str) -> None:
        """开始一次运行上下文。"""

        self._current_run_id = run_id
        self._recent_artifacts = []

    def end_run_context(self) -> None:
        """结束一次运行上下文。"""

        self._current_run_id = None

    def get_recent_artifact_names(self) -> list[str]:
        """返回当前运行收集到的 artifact 名称。"""

        return list(self._recent_artifacts)

    def ensure_session(self) -> bool:
        """判断淘宝 profile 目录是否已就绪。"""

        return self.profile_root.exists()

    def search(self, query: str, limit: int = 5) -> list[ListingProduct]:
        """执行淘宝搜索并抽取候选商品。"""

        with self._open_context() as context:
            page = context.pages[0] if context.pages else context.new_page()
            search_url = self.SEARCH_URL_TEMPLATE.format(query=quote_plus(query))
            page.goto(search_url, wait_until="domcontentloaded", timeout=60_000)
            self._paced_wait(page, multiplier=1.0, extra_seconds=0.5)

            html = page.content()
            self.save_debug_artifact(f"taobao_search_{self._slugify(query)}.html", html)
            self._assert_page_safe(page, stage="search", artifact_slug=self._slugify(query))
            try:
                screenshot_name = f"taobao_search_{self._slugify(query)}.png"
                page.screenshot(path=str(self.artifact_root / self._build_artifact_name(screenshot_name)), full_page=True)
                self._recent_artifacts.append(self._build_artifact_name(screenshot_name))
            except Exception:
                pass

            # 首先尝试主选择器，失败时回退
            records = page.evaluate(self._listing_extraction_script(primary=True))
            if not records:
                # 回退：尝试回退选择器
                records = page.evaluate(self._listing_extraction_script(primary=False))
            self.save_debug_artifact(
                f"taobao_search_{self._slugify(query)}.json",
                json.dumps(records, ensure_ascii=False, indent=2),
            )

        products: list[ListingProduct] = []
        for index, record in enumerate(records[:limit], start=1):
            title = str(record.get("title") or "").strip()
            detail_url = str(record.get("detail_url") or "").strip()
            if not title or not detail_url:
                continue
            try:
                safe_url = ensure_safe_readonly_url(canonicalize_detail_url(detail_url))
            except Exception:
                continue
            products.append(
                ListingProduct(
                    title=title,
                    price_text=record.get("price_text"),
                    sales_text=record.get("sales_text"),
                    shop_name=record.get("shop_name"),
                    detail_url=safe_url,
                    source_rank=index,
                )
            )
        return products

    def fetch_detail(self, product: ListingProduct) -> ProductDetail:
        """抓取商品详情页，并做一轮确定性结构化。"""

        if not product.detail_url:
            raise ValueError("商品缺少 detail_url，无法抓取详情页。")

        safe_url = ensure_safe_readonly_url(canonicalize_detail_url(product.detail_url))

        with self._open_context() as context:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(safe_url, wait_until="domcontentloaded", timeout=60_000)
            self._paced_wait(page, multiplier=1.0, extra_seconds=0.8)

            html = page.content()
            self._assert_page_safe(page, stage="detail", artifact_slug=self._slugify(product.title))

            # 使用增强的字段提取（带回退逻辑）
            title = self._extract_title_with_fallback(page) or product.title
            body_text = self._extract_body_text_with_fallback(page)
            price_text = self._extract_price_with_fallback(page) or product.price_text
            shop_name = self._extract_shop_name_with_fallback(page) or product.shop_name

            artifact_base = self._slugify(title or "detail")
            self.save_debug_artifact(f"taobao_detail_{artifact_base}.html", html)
            self.save_debug_artifact(f"taobao_detail_{artifact_base}.txt", body_text)
            try:
                screenshot_name = f"taobao_detail_{artifact_base}.png"
                page.screenshot(path=str(self.artifact_root / self._build_artifact_name(screenshot_name)), full_page=True)
                self._recent_artifacts.append(self._build_artifact_name(screenshot_name))
            except Exception:
                pass

        return build_product_detail_from_text(
            title=title,
            raw_text=body_text,
            price_text=price_text,
            shop_name=shop_name,
            detail_url=safe_url,
        )

    def save_debug_artifact(self, name: str, content: str) -> Path:
        """保存调试产物。"""

        final_name = self._build_artifact_name(name)
        file_path = self.artifact_root / final_name
        file_path.write_text(content, encoding="utf-8")
        self._recent_artifacts.append(final_name)
        return file_path

    def check_login_status(self) -> dict[str, Any]:
        """检查当前淘宝登录状态。"""

        with self._open_context() as context:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://www.taobao.com", wait_until="domcontentloaded", timeout=60_000)
            self._paced_wait(page, multiplier=0.8, extra_seconds=0.2)
            status = self._extract_login_status(page)
            html = page.content()
            self.save_debug_artifact("taobao_homepage_login_check.html", html)
            self.save_debug_artifact(
                "taobao_homepage_login_check.json",
                json.dumps(status, ensure_ascii=False, indent=2),
            )
            return status

    def open_login_window(self, keep_open_seconds: int = 180) -> dict[str, Any]:
        """打开淘宝首页并保留窗口一段时间，供用户手动扫码登录。"""

        with self._open_context() as context:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://www.taobao.com", wait_until="domcontentloaded", timeout=60_000)
            self._paced_wait(page, multiplier=0.8, extra_seconds=0.2)
            before_status = self._extract_login_status(page)
            self.save_debug_artifact(
                "taobao_login_window_before.json",
                json.dumps(before_status, ensure_ascii=False, indent=2),
            )
            page.wait_for_timeout(max(1, keep_open_seconds) * 1000)
            after_status = self._extract_login_status(page)
            self.save_debug_artifact(
                "taobao_login_window_after.json",
                json.dumps(after_status, ensure_ascii=False, indent=2),
            )
            return {
                "before": before_status,
                "after": after_status,
                "kept_open_seconds": keep_open_seconds,
            }

    def inspect_page_risk(self, url: str, wait_after_load_ms: int = 3000) -> dict[str, Any]:
        """打开任意页面并返回风险识别结果。"""

        safe_url = ensure_safe_readonly_url(canonicalize_detail_url(url))
        with self._open_context() as context:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(safe_url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(wait_after_load_ms)
            body_text = self._extract_body_text_with_fallback(page)
            report = detect_page_risk(body_text)
            payload = report.model_dump()
            payload["url"] = safe_url
            self.save_debug_artifact(
                f"risk_probe_{self._slugify(safe_url)}.json",
                json.dumps(payload, ensure_ascii=False, indent=2),
            )
            return payload

    def probe_search_query(self, query: str, wait_after_load_ms: int = 3000) -> dict[str, Any]:
        """探测搜索页的候选提取与选择器命中情况。"""

        search_url = self.SEARCH_URL_TEMPLATE.format(query=quote_plus(query))
        with self._open_context() as context:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(search_url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(wait_after_load_ms)

            body_text = self._extract_body_text_with_fallback(page)
            risk = detect_page_risk(body_text)
            html = page.content()

            # 探测主选择器和回退选择器
            primary_records = page.evaluate(self._listing_extraction_script(primary=True))
            if not primary_records:
                records = page.evaluate(self._listing_extraction_script(primary=False))
            else:
                records = primary_records

            selector_counts = page.evaluate(self._search_selector_probe_script(include_fallbacks=True))

            slug = self._slugify(query)
            payload = {
                "query": query,
                "search_url": search_url,
                "risk": risk.model_dump(),
                "selector_counts": selector_counts,
                "records_preview": records[:5],
                "records_count": len(records),
                "body_preview": body_text[:500],
                "body_length": len(body_text),
                "used_fallback": len(primary_records) == 0 and len(records) > 0,
            }
            from shopping.probe_analysis import analyze_search_probe
            payload["analysis"] = analyze_search_probe(payload)
            self.save_debug_artifact(
                f"search_probe_{slug}.html",
                html,
            )
            self.save_debug_artifact(
                f"search_probe_{slug}.json",
                json.dumps(payload, ensure_ascii=False, indent=2),
            )
            return payload

    def probe_detail_url(self, url: str, wait_after_load_ms: int = 3000) -> dict[str, Any]:
        """抓取详情页的原始候选信息，用于真实联调时排查选择器稳定性。"""

        safe_url = ensure_safe_readonly_url(canonicalize_detail_url(url))
        with self._open_context() as context:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(safe_url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(wait_after_load_ms)

            body_text = self._extract_body_text_with_fallback(page)
            risk = detect_page_risk(body_text)

            # 探测各字段选择器（包括主选择器和回退）
            title_candidates = self._collect_selector_hits(page, self.selector_profile.detail.title_selectors)
            shop_candidates = self._collect_selector_hits(page, self.selector_profile.detail.shop_name_selectors)
            price_candidates = self._collect_selector_hits(page, self.selector_profile.detail.price_selectors)

            # 如果主选择器未命中，探测回退选择器
            fallback_used = {}
            if not title_candidates:
                fb_hits = self._collect_selector_hits(page, self.selector_profile.detail.title_fallbacks)
                if fb_hits:
                    fallback_used["title"] = fb_hits
            if not shop_candidates:
                fb_hits = self._collect_selector_hits(page, self.selector_profile.detail.shop_name_fallbacks)
                if fb_hits:
                    fallback_used["shop_name"] = fb_hits

            payload = {
                "url": safe_url,
                "risk": risk.model_dump(),
                "title_candidates": title_candidates,
                "shop_candidates": shop_candidates,
                "price_candidates": price_candidates,
                "body_preview": body_text[:500],
                "body_length": len(body_text),
                "fallback_used": fallback_used,
            }
            from shopping.probe_analysis import analyze_detail_probe
            payload["analysis"] = analyze_detail_probe(payload)
            self.save_debug_artifact(
                f"detail_probe_{self._slugify(safe_url)}.json",
                json.dumps(payload, ensure_ascii=False, indent=2),
            )
            return payload

    def _assert_page_safe(self, page, *, stage: str, artifact_slug: str) -> None:
        """检查当前页面是否出现风险信号。"""

        report = detect_page_risk(self._extract_body_text_with_fallback(page))
        if report.detected:
            payload = report.model_dump()
            payload["stage"] = stage
            self.save_debug_artifact(
                f"{stage}_{artifact_slug}_risk.json",
                json.dumps(payload, ensure_ascii=False, indent=2),
            )
            raise ShoppingRiskDetectedError(
                f"页面出现风控/验证码信号：{report.risk_type}，命中 {report.signals}"
            )

    def _paced_wait(self, page, *, multiplier: float = 1.0, extra_seconds: float = 0.0) -> None:
        """根据配置决定是否执行保守等待。"""

        delay_seconds = compute_polite_delay(
            self.runtime_config.anti_bot.base_delay_seconds,
            multiplier=multiplier,
            extra_seconds=extra_seconds,
        )
        if self.runtime_config.anti_bot.enforce_delay:
            page.wait_for_timeout(int(delay_seconds * 1000))
        else:
            page.wait_for_timeout(max(1200, int(extra_seconds * 1000)))

    def _scroll_for_content(self, page, *, rounds: int = 2, wait_ms: int = 1000) -> None:
        """对当前页面做有限滚动，帮助加载更多列表/正文/评论。"""

        for _ in range(max(0, rounds)):
            try:
                page.evaluate("window.scrollBy(0, Math.max(800, window.innerHeight));")
                page.wait_for_timeout(wait_ms)
            except Exception:
                break

    def _open_context(self):
        """启动 persistent context。"""

        try:
            from playwright.sync_api import sync_playwright
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError(
                "未安装 Playwright，请在测试 Phase 1 真实抓取前执行 `uv sync --extra phase1`，然后安装 Chromium。"
            ) from exc

        class _ContextManager:
            def __init__(self, outer: TaobaoPlaywrightExecutor) -> None:
                self.outer = outer
                self.playwright = None
                self.context = None

            def __enter__(self):
                self.playwright = sync_playwright().start()
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.outer.profile_root),
                    headless=not self.outer.runtime_config.headed,
                    viewport={"width": 1440, "height": 960},
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-default-browser-check",
                    ],
                )
                return self.context

            def __exit__(self, exc_type, exc, tb):
                if self.context is not None:
                    self.context.close()
                if self.playwright is not None:
                    self.playwright.stop()

        return _ContextManager(self)

    def _build_artifact_name(self, name: str) -> str:
        """根据当前运行上下文构造 artifact 名称。"""

        if not self._current_run_id:
            return name
        return f"{self._current_run_id}_{name}"

    @staticmethod
    def _slugify(value: str) -> str:
        """把任意字符串转成安全文件名。"""

        compact = re.sub(r"\s+", "_", value).strip("_")
        compact = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "", compact)
        return compact[:80] or "artifact"

    @staticmethod
    def _collect_selector_hits(page, selectors: list[str]) -> list[dict[str, str]]:
        """收集一组选择器的命中结果，用于联调诊断。"""

        hits: list[dict[str, str]] = []
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                text = locator.inner_text(timeout=1_000).strip()
                if text:
                    hits.append({"selector": selector, "text": text[:160]})
            except Exception:
                continue
        return hits

    # ========== 增强的字段提取方法（带回退逻辑）==========

    def _extract_title_with_fallback(self, page) -> str | None:
        """从详情页提取标题，失败时回退到 page.title()。"""

        selectors = self.selector_profile.detail.title_selectors
        candidates = [item["text"] for item in self._collect_selector_hits(page, selectors)]

        # 如果主选择器失败，尝试回退
        if not candidates:
            fb_selectors = getattr(self.selector_profile.detail, "title_fallbacks", [])
            if fb_selectors:
                candidates = [item["text"] for item in self._collect_selector_hits(page, fb_selectors)]

        # 最终回退：使用 page.title()
        page_title = None
        try:
            page_title = page.title().strip()
        except Exception:
            page_title = None

        return choose_best_title(candidates, page_title=page_title)

    def _extract_shop_name_with_fallback(self, page) -> str | None:
        """从详情页提取店铺名，失败时从 body 正则匹配。"""

        selectors = self.selector_profile.detail.shop_name_selectors
        candidates = [item["text"] for item in self._collect_selector_hits(page, selectors)]

        # 如果主选择器失败，尝试回退
        if not candidates:
            fb_selectors = getattr(self.selector_profile.detail, "shop_name_fallbacks", [])
            if fb_selectors:
                candidates = [item["text"] for item in self._collect_selector_hits(page, fb_selectors)]

        body_text = self._extract_body_text_with_fallback(page)
        return choose_best_shop_name(candidates, body_text=body_text)

    def _extract_price_with_fallback(self, page) -> str | None:
        """从详情页提取价格文本，失败时从 body 正则匹配。"""

        selectors = self.selector_profile.detail.price_selectors
        candidates = [item["text"] for item in self._collect_selector_hits(page, selectors)]

        # 如果主选择器失败，尝试回退
        if not candidates:
            fb_selectors = getattr(self.selector_profile.detail, "price_fallbacks", [])
            if fb_selectors:
                candidates = [item["text"] for item in self._collect_selector_hits(page, fb_selectors)]

        body_text = self._extract_body_text_with_fallback(page)
        return choose_best_price_text(candidates, body_text=body_text)

    def _extract_body_text_with_fallback(self, page) -> str:
        """获取详情页正文文本，使用主选择器失败时回退。"""

        candidates: list[str] = []

        # 首先尝试主选择器
        for selector in self.selector_profile.detail.body_selectors:
            try:
                text = page.locator(selector).first.inner_text(timeout=2_000).strip()
                if text:
                    candidates.append(text)
            except Exception:
                continue

        # 如果主选择器未获取足够内容，尝试回退选择器
        if len(candidates) < 100 or not candidates:
            fb_selectors = getattr(self.selector_profile.detail, "body_fallback_selectors", [])
            for selector in fb_selectors:
                try:
                    text = page.locator(selector).first.inner_text(timeout=2_000).strip()
                    if text:
                        candidates.append(text)
                except Exception:
                    continue

        return choose_best_body_text(candidates)

    # ========== 原有方法（保留兼容性）==========

    def _extract_title(self, page) -> str | None:
        """从详情页提取标题（兼容旧接口）。"""
        return self._extract_title_with_fallback(page)

    def _extract_shop_name(self, page) -> str | None:
        """从详情页提取店铺名（兼容旧接口）。"""
        return self._extract_shop_name_with_fallback(page)

    def _extract_price_text(self, page) -> str | None:
        """从详情页提取价格文本（兼容旧接口）。"""
        return self._extract_price_with_fallback(page)

    def _extract_body_text(self, page) -> str:
        """获取详情页正文文本（兼容旧接口）。"""
        return self._extract_body_text_with_fallback(page)

    @staticmethod
    def _extract_login_status(page) -> dict[str, Any]:
        """从淘宝首页判断是否已登录。"""

        try:
            payload = page.evaluate(
                r"""
() => {
  const clean = (value) => (value || '').replace(/\s+/g, ' ').trim();
  const bodyText = clean(document.body ? document.body.innerText : '');
  const loginHints = ['亲，请登录', '登录', '请登录'];
  const logoutHints = ['退出', '已买到的宝贝', '我的淘宝'];

  const isLoggedIn = logoutHints.some((hint) => bodyText.includes(hint)) && !bodyText.includes('亲，请登录');
  const nicknameCandidates = Array.from(document.querySelectorAll('a, span, div'))
    .map((node) => clean(node.innerText))
    .filter((text) => text && text.length <= 24)
    .filter((text) => /会员|店铺|淘宝|天猫/.test(text) === false);

  return {
    is_logged_in: isLoggedIn,
    body_preview: bodyText.slice(0, 200),
    nickname_candidates: nicknameCandidates.slice(0, 10),
    login_hint_present: loginHints.some((hint) => bodyText.includes(hint)),
  };
}
                """
            )
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass
        return {
            "is_logged_in": False,
            "body_preview": "",
            "nickname_candidates": [],
            "login_hint_present": None,
        }

    def _search_selector_probe_script(self, include_fallbacks: bool = False) -> str:
        """返回搜索页选择器命中计数脚本。"""

        selectors = self.selector_profile.search.card_candidates
        if include_fallbacks:
            fb_selectors = getattr(self.selector_profile.search, "card_fallbacks", [])
            selectors = selectors + fb_selectors

        selectors_json = json.dumps(selectors, ensure_ascii=False)
        return f"""
() => {{
  const selectors = {selectors_json};
  return selectors.map((selector) => ({{
    selector,
    count: document.querySelectorAll(selector).length,
  }}));
}}
        """

    def _listing_extraction_script(self, primary: bool = True) -> str:
        """返回列表页提取脚本。

        Args:
            primary: True 使用主选择器，False 使用回退选择器
        """

        if primary:
            card_selectors = self.selector_profile.search.card_candidates
        else:
            card_selectors = getattr(self.selector_profile.search, "card_fallbacks", []) or self.selector_profile.search.card_candidates

        detail_patterns_json = json.dumps(self.selector_profile.search.detail_link_patterns, ensure_ascii=False)
        shop_signals_json = json.dumps(self.selector_profile.search.shop_name_text_signals, ensure_ascii=False)
        card_selectors_json = json.dumps(card_selectors, ensure_ascii=False)

        return f"""
() => {{
  const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
  const cardSelectors = {card_selectors_json};
  const detailLinkPatterns = {detail_patterns_json};
  const shopSignals = {shop_signals_json};
  const cards = Array.from(document.querySelectorAll(cardSelectors.join(',')));

  const parseCard = (node) => {{
    const textNodes = Array.from(node.querySelectorAll('a, div, span'))
      .map((el) => clean(el.innerText))
      .filter((text) => text.length >= 6);
    const title = textNodes.sort((a, b) => b.length - a.length)[0] || '';

    const anchors = Array.from(node.querySelectorAll('a[href]'));
    const detailAnchor = anchors.find((a) => {{
      const href = a.href || '';
      return detailLinkPatterns.some((pattern) => href.includes(pattern));
    }}) || anchors[0];

    const joinedText = clean(node.innerText);
    const priceMatch = joinedText.match(/\\d+(?:\\.\\d+)?\\s*元(?:\\/㎡|\\/平米|\\/平方|)/);
    const salesMatch = joinedText.match(/(?:已售|付款|人付款)[^\\n ]{{0,12}}/);
    const shopAnchor = anchors.find((a) => {{
      const txt = clean(a.innerText);
      return txt && txt.length <= 40 && shopSignals.some((signal) => txt.includes(signal));
    }});

    return {{
      title,
      detail_url: detailAnchor ? detailAnchor.href : '',
      price_text: priceMatch ? priceMatch[0] : '',
      sales_text: salesMatch ? salesMatch[0] : '',
      shop_name: shopAnchor ? clean(shopAnchor.innerText) : ''
    }};
  }};

  let items = cards.map(parseCard).filter((item) => item.title && item.detail_url);
  if (items.length === 0) {{
    items = Array.from(document.querySelectorAll('a[href]'))
      .map((anchor) => ({{
        title: clean(anchor.innerText),
        detail_url: anchor.href || '',
        price_text: '',
        sales_text: '',
        shop_name: ''
      }}))
      .filter((item) => item.title.length >= 8)
      .filter((item) => detailLinkPatterns.some((pattern) => item.detail_url.includes(pattern)));
  }}

  const unique = [];
  const seen = new Set();
  for (const item of items) {{
    const key = item.detail_url || item.title;
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(item);
  }}
  return unique.slice(0, 20);
}}
        """
# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 16:28:41 CST

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from security.url_guard import ensure_safe_readonly_url
from shopping.review_models import RawReview
from shopping.review_probe_analysis import analyze_review_probe
from shopping.risk_detection import detect_page_risk
from shopping.schemas import ProductDetail
from shopping.url_utils import canonicalize_detail_url


class ReviewFetcher(ABC):
    """评论抓取器抽象接口。"""

    @abstractmethod
    def fetch_reviews(self, product: ProductDetail, limit: int = 10) -> list[RawReview]:
        """抓取某个商品的评论。"""


class ReplayReviewFetcher(ReviewFetcher):
    """本地回放评论抓取器。"""

    def __init__(self, fixture_root: str | Path) -> None:
        self.fixture_root = Path(fixture_root)
        self.fixture_root.mkdir(parents=True, exist_ok=True)

    def fetch_reviews(self, product: ProductDetail, limit: int = 10) -> list[RawReview]:
        """按商品标题读取评论 fixture。"""

        safe_name = product.title.replace("/", "_").replace(" ", "_")
        file_path = self.fixture_root / f"reviews_{safe_name}.json"
        if not file_path.exists():
            return []
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        reviews = [RawReview.model_validate(item) for item in payload]
        return reviews[:limit]


class TaobaoPlaywrightReviewFetcher(ReviewFetcher):
    """淘宝评论抓取器骨架。"""

    def __init__(self, executor) -> None:
        self.executor = executor

    def fetch_reviews(self, product: ProductDetail, limit: int = 10) -> list[RawReview]:
        """抓取商品评论。"""

        payload = self.probe_reviews(product, limit=limit)
        reviews = [RawReview.model_validate(item) for item in payload.get("reviews", [])]
        return reviews[:limit]

    def probe_reviews(self, product: ProductDetail, limit: int = 10) -> dict:
        """抓取并分析评论区域，用于联调。"""

        if not product.detail_url:
            payload = {
                "detail_url": None,
                "risk": {"detected": False},
                "reviews": [],
                "review_count": 0,
                "with_images": 0,
                "anonymous_count": 0,
                "average_length": 0,
                "selector_counts": [],
            }
            payload["analysis"] = analyze_review_probe(payload)
            return payload

        safe_url = ensure_safe_readonly_url(canonicalize_detail_url(product.detail_url))

        with self.executor._open_context() as context:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(safe_url, wait_until="domcontentloaded", timeout=60_000)
            self.executor._paced_wait(page, multiplier=0.8, extra_seconds=0.3)

            risk = detect_page_risk(self.executor._extract_body_text(page))
            if risk.detected:
                payload = {
                    "detail_url": safe_url,
                    "risk": risk.model_dump(),
                    "reviews": [],
                    "review_count": 0,
                    "with_images": 0,
                    "anonymous_count": 0,
                    "average_length": 0,
                    "selector_counts": [],
                }
                payload["analysis"] = analyze_review_probe(payload)
                self.executor.save_debug_artifact(
                    f"review_probe_{self.executor._slugify(product.title)}_risk.json",
                    json.dumps(payload, ensure_ascii=False, indent=2),
                )
                return payload

            for selector in self.executor.selector_profile.review.review_tab_selectors:
                try:
                    page.locator(selector).first.click(timeout=2_000)
                    page.wait_for_timeout(2_000)
                    break
                except Exception:
                    continue

            self.executor._scroll_for_content(page, rounds=2, wait_ms=1200)
            selector_counts = page.evaluate(self._review_selector_probe_script())
            reviews_payload = page.evaluate(self._review_extraction_script())
            review_count = len(reviews_payload)
            with_images = sum(1 for item in reviews_payload if int(item.get("image_count", 0) or 0) > 0)
            anonymous_count = sum(1 for item in reviews_payload if item.get("is_anonymous"))
            average_length = round(
                sum(len(str(item.get("content") or "")) for item in reviews_payload) / review_count,
                2,
            ) if review_count else 0

            payload = {
                "detail_url": safe_url,
                "risk": risk.model_dump(),
                "reviews": reviews_payload[:limit],
                "review_count": review_count,
                "with_images": with_images,
                "anonymous_count": anonymous_count,
                "average_length": average_length,
                "selector_counts": selector_counts,
            }
            payload["analysis"] = analyze_review_probe(payload)
            self.executor.save_debug_artifact(
                f"reviews_{self.executor._slugify(product.title)}.json",
                json.dumps(payload, ensure_ascii=False, indent=2),
            )
            return payload

    def _review_selector_probe_script(self) -> str:
        """返回评论选择器命中统计脚本。"""

        selectors_json = json.dumps(self.executor.selector_profile.review.review_container_selectors, ensure_ascii=False)
        return f"""
() => {{
  const selectors = {selectors_json};
  return selectors.map((selector) => ({{
    selector,
    count: document.querySelectorAll(selector).length,
  }}));
}}
        """

    def _review_extraction_script(self) -> str:
        """返回评论抽取脚本。"""

        container_selectors_json = json.dumps(self.executor.selector_profile.review.review_container_selectors, ensure_ascii=False)
        text_signals_json = json.dumps(self.executor.selector_profile.review.review_text_signals, ensure_ascii=False)
        return f"""
() => {{
  const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
  const containerSelectors = {container_selectors_json};
  const textSignals = {text_signals_json};
  const blocks = Array.from(document.querySelectorAll(containerSelectors.join(',')));
  const reviewCandidates = blocks
    .map((node) => {{
      const text = clean(node.innerText);
      if (!text || text.length < 8) return null;
      const imageCount = node.querySelectorAll('img').length;
      const ratingMatch = text.match(/([1-5])分|评分\\s*([1-5])/);
      return {{
        content: text.slice(0, 300),
        image_count: imageCount,
        rating: ratingMatch ? Number(ratingMatch[1] || ratingMatch[2]) : null,
        is_anonymous: text.includes('匿名'),
      }};
    }})
    .filter(Boolean)
    .filter((item) => textSignals.some((signal) => item.content.includes(signal)));

  const unique = [];
  const seen = new Set();
  for (const item of reviewCandidates) {{
    const key = item.content;
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(item);
  }}
  return unique.slice(0, 30);
}}
        """

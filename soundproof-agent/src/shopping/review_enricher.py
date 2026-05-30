# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 21:32:14 CST

from __future__ import annotations

from shopping.review_fetcher import ReviewFetcher
from shopping.review_pipeline import ReviewSignalExtractor
from shopping.schemas import ProductDetail, ShoppingSearchIntent


class ProductReviewEnricher:
    """商品评论增强器。

    设计目标：
    1. 评论只作为第二阶段增强，不阻断主链；
    2. 只对前若干个候选补抓评论，控制成本与风险；
    3. 把评论信息压缩成几个稳定字段塞回 ProductDetail，供排序/总结/报告复用。
    """

    def __init__(self, review_fetcher: ReviewFetcher, extractor: ReviewSignalExtractor | None = None) -> None:
        self.review_fetcher = review_fetcher
        self.extractor = extractor or ReviewSignalExtractor()

    def enrich(self, *, intent: ShoppingSearchIntent, product: ProductDetail, limit: int = 8) -> ProductDetail:
        """对单个商品做评论增强。"""

        reviews = self.review_fetcher.fetch_reviews(product, limit=limit)
        if not reviews:
            return product

        summary = self.extractor.summarize(reviews, intent=intent, product=product)
        payload = product.model_dump()
        payload["review_sample_count"] = summary.total_reviews
        payload["review_effective_count"] = summary.effective_reviews
        payload["review_highlights"] = [*summary.highlights, *summary.lowlights][:4]
        payload["review_risk_flags"] = summary.risk_notes
        return ProductDetail.model_validate(payload)

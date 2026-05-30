# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 21:13:05 CST

from __future__ import annotations

import re

from shopping.review_models import RawReview, ReviewAuditSummary, ReviewJudgement
from shopping.schemas import ProductDetail, ShoppingSearchIntent


class ReviewSignalExtractor:
    """评论信号提取器。

    这里先用规则法做第一版“有效评论识别”和“疑似刷评过滤”。
    后续如果评论抓取真的进入主链，再叠加 LLM 复核层。
    """

    GENERIC_PRAISE = {
        "很好",
        "不错",
        "满意",
        "好评",
        "非常好",
        "值得购买",
        "物美价廉",
        "推荐购买",
    }

    PRODUCT_SPEC_KEYWORDS = [
        "夹胶",
        "中空",
        "三道密封",
        "四道密封",
        "断桥铝",
        "平开窗",
        "内窗",
        "玻璃",
        "五金",
        "安装",
        "测量",
        "隔音",
        "低频",
        "地铁",
        "临街",
    ]

    NEGATIVE_SIGNALS = [
        "不隔音",
        "没效果",
        "漏风",
        "漏水",
        "噪音还是大",
        "变形",
        "虚标",
        "翻车",
        "开裂",
        "脱胶",
    ]

    def judge(self, review: RawReview, *, intent: ShoppingSearchIntent, product: ProductDetail) -> ReviewJudgement:
        """判断评论是否有效，以及是否疑似刷评。"""

        text = self._normalize(review.content)
        reasons: list[str] = []
        extracted_signals: list[str] = []
        score = 0.0
        suspected_brushed = False

        if len(text) >= 18:
            score += 0.25
            reasons.append("评论长度较充分")
        else:
            reasons.append("评论较短")

        if review.image_count > 0:
            score += 0.1
            reasons.append("带图片评论")

        spec_hits = self._extract_spec_hits(text, intent=intent, product=product)
        if spec_hits:
            score += 0.4
            extracted_signals.extend(spec_hits)
            reasons.append("包含产品/场景相关关键词")

        negative_hits = [signal for signal in self.NEGATIVE_SIGNALS if signal in text]
        if negative_hits:
            score += 0.25
            extracted_signals.extend(negative_hits)
            reasons.append("包含明确负面体验，通常属于有效评论")

        if self._looks_like_generic_praise(text):
            score -= 0.2
            reasons.append("内容接近通用好评模板")

        if len(text) < 10 and review.rating in (4, 5):
            suspected_brushed = True
            score -= 0.25
            reasons.append("短评且高分，疑似模板式好评")

        if not spec_hits and not negative_hits and len(text) < 18:
            suspected_brushed = True
            score -= 0.2
            reasons.append("缺少产品细节且文本过短")

        confidence_score = max(0.0, min(1.0, round(score, 4)))
        effective = confidence_score >= 0.25 and not (suspected_brushed and confidence_score < 0.35)

        return ReviewJudgement(
            effective=effective,
            suspected_brushed=suspected_brushed,
            confidence_score=confidence_score,
            reasons=reasons,
            extracted_signals=sorted(set(extracted_signals)),
        )

    def summarize(
        self,
        reviews: list[RawReview],
        *,
        intent: ShoppingSearchIntent,
        product: ProductDetail,
    ) -> ReviewAuditSummary:
        """对一组评论做审查汇总。"""

        highlights: list[str] = []
        lowlights: list[str] = []
        risk_notes: list[str] = []
        effective_count = 0
        brushed_count = 0

        for review in reviews:
            judgement = self.judge(review, intent=intent, product=product)
            text = self._normalize(review.content)

            if judgement.effective:
                effective_count += 1
                if any(signal in text for signal in self.NEGATIVE_SIGNALS):
                    if len(lowlights) < 3:
                        lowlights.append(text[:80])
                else:
                    if len(highlights) < 3:
                        highlights.append(text[:80])
            elif judgement.suspected_brushed:
                brushed_count += 1

        neutral_count = max(0, len(reviews) - effective_count - brushed_count)
        if brushed_count > 0:
            risk_notes.append(f"疑似刷评/模板化评论 {brushed_count} 条")
        if effective_count == 0 and reviews:
            risk_notes.append("有效评论不足，评论参考价值偏弱")
        if any("漏风" in item or "不隔音" in item for item in lowlights):
            risk_notes.append("评论中出现隔音或密封负面反馈，需要重点复核")

        return ReviewAuditSummary(
            total_reviews=len(reviews),
            effective_reviews=effective_count,
            suspected_brushed_reviews=brushed_count,
            neutral_reviews=neutral_count,
            highlights=highlights,
            lowlights=lowlights,
            risk_notes=risk_notes,
        )

    @staticmethod
    def _normalize(text: str) -> str:
        """统一评论文本。"""

        return re.sub(r"\s+", " ", text or "").strip()

    def _looks_like_generic_praise(self, text: str) -> bool:
        """是否像通用好评模板。"""

        if not text:
            return True
        if text in self.GENERIC_PRAISE:
            return True
        return len(text) <= 12 and any(word in text for word in self.GENERIC_PRAISE)

    def _extract_spec_hits(self, text: str, *, intent: ShoppingSearchIntent, product: ProductDetail) -> list[str]:
        """提取评论里命中的规格与场景信号。"""

        candidates = list(self.PRODUCT_SPEC_KEYWORDS)
        candidates.extend(intent.primary_keywords)
        candidates.extend(product.extracted_keywords)
        candidates.extend([product.glass_spec or "", product.frame_spec or "", product.seal_spec or ""])
        hits = [item for item in candidates if item and item in text]
        return sorted(set(hits))

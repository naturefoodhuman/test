# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 23:55:38 CST

from __future__ import annotations

from shopping.price_utils import parse_price_value
from shopping.schemas import ProductDetail, ShoppingSearchIntent


class IntentProductRanker:
    """基于购物意图的确定性商品排序器。

    设计目标：
    1. 在进入 LLM 总结前，先用规则做一轮“方向正确”的排序；
    2. 避免 LLM 面对一堆候选时，被明显不合适的商品干扰；
    3. 把排序理由保存在对象里，便于后续前端展示或调试。
    """

    def rank(self, intent: ShoppingSearchIntent, products: list[ProductDetail]) -> list[ProductDetail]:
        """给商品打分并排序。"""

        annotated = [self._score_product(intent, product) for product in products]
        return sorted(
            annotated,
            key=lambda item: (item.ranking_score if item.ranking_score is not None else -999.0),
            reverse=True,
        )

    def _score_product(self, intent: ShoppingSearchIntent, product: ProductDetail) -> ProductDetail:
        """对单个商品打分。"""

        score = 0.0
        reasons: list[str] = []

        title_text = product.title or ""
        raw_text = product.raw_spec_text or ""
        searchable_text = " ".join(
            [
                title_text,
                product.glass_spec or "",
                product.frame_spec or "",
                product.seal_spec or "",
                product.hardware_keyword or "",
                raw_text,
            ]
        )

        # 方案类型匹配
        if intent.solution_type == "replace_window":
            if any(keyword in searchable_text for keyword in ["系统窗", "平开窗", "断桥铝"]):
                score += 1.5
                reasons.append("符合整窗更换路线")
        elif intent.solution_type == "add_inner_window":
            if "内窗" in searchable_text:
                score += 1.8
                reasons.append("符合加装内窗路线")

        # 低频场景优先夹胶和密封
        if any(note for note in [intent.scene, *intent.notes] if "低频" in note) or "low" in intent.scene.lower():
            if "夹胶" in searchable_text or "PVB" in searchable_text or "SGP" in searchable_text:
                score += 2.5
                reasons.append("低频场景下夹胶结构加分")
            if any(keyword in searchable_text for keyword in ["三道密封", "四道密封", "EPDM", "三元乙丙"]):
                score += 1.2
                reasons.append("密封配置较强")
            if "推拉窗" in searchable_text:
                score -= 1.5
                reasons.append("低频场景下推拉窗一般不占优")

        # 高配场景更看重多玻/双夹胶
        if intent.budget_level == "high":
            if any(keyword in searchable_text for keyword in ["四玻", "双夹胶", "高配"]):
                score += 1.5
                reasons.append("高预算场景下高配结构加分")

        # 性价比场景，价格过高会被轻度惩罚
        price_value = parse_price_value(product.price_text)
        if intent.budget_level == "low":
            if price_value is not None:
                if price_value <= 800:
                    score += 1.0
                    reasons.append("低预算场景下价格较友好")
                elif price_value > 1200:
                    score -= 1.0
                    reasons.append("低预算场景下价格偏高")
        elif intent.budget_level == "medium":
            if price_value is not None and price_value <= 1000:
                score += 0.6
                reasons.append("中预算场景下价格可接受")

        # 风险标记惩罚
        if product.risk_flags:
            score -= min(1.5, 0.4 * len(product.risk_flags))
            reasons.append("存在结构化风险标记")

        payload = product.model_dump()
        payload["ranking_score"] = round(score, 4)
        payload["ranking_reasons"] = reasons
        return ProductDetail.model_validate(payload)

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 02:58:44 CST

from __future__ import annotations

from shopping.schemas import ListingProduct, RejectedListingProduct, ShoppingSearchIntent


class IntentListingFilter:
    """候选商品过滤器。

    目标：
    1. 在进入详情页抓取前，尽量剔除明显不属于“窗产品”的噪声候选；
    2. 保留过滤逻辑在规则层，便于后续根据真实淘宝结果快速调整；
    3. 即使过滤过严，也保留兜底机制，避免把候选清空。
    """

    ACCESSORY_KEYWORDS = [
        "窗帘",
        "密封条",
        "隔音棉",
        "静音舱",
        "白噪音",
        "耳塞",
        "贴膜",
        "胶条",
        "风扇",
        "空调罩",
    ]

    WINDOW_SIGNAL_KEYWORDS = [
        "窗",
        "系统窗",
        "平开窗",
        "内窗",
        "断桥铝",
        "门窗",
    ]

    def analyze(self, intent: ShoppingSearchIntent, products: list[ListingProduct]) -> tuple[list[ListingProduct], list[RejectedListingProduct]]:
        """根据购物意图过滤列表页候选，并返回被过滤原因。"""

        kept: list[ListingProduct] = []
        rejected: list[RejectedListingProduct] = []

        for product in products:
            title = product.title.strip()
            if not title:
                rejected.append(
                    RejectedListingProduct(
                        title="",
                        detail_url=product.detail_url,
                        source_rank=product.source_rank,
                        reason="标题为空",
                    )
                )
                continue

            reject_reason = self._get_noise_reason(title, intent)
            if reject_reason is not None:
                rejected.append(
                    RejectedListingProduct(
                        title=title,
                        detail_url=product.detail_url,
                        source_rank=product.source_rank,
                        reason=reject_reason,
                    )
                )
                continue
            kept.append(product)

        if not kept:
            # 兜底：如果全部被过滤掉，至少返回前两个原始候选，避免工作流中断。
            return products[:2], rejected
        return kept, rejected

    def filter(self, intent: ShoppingSearchIntent, products: list[ListingProduct]) -> list[ListingProduct]:
        """兼容旧调用，只返回保留候选。"""

        kept, _rejected = self.analyze(intent, products)
        return kept

    def _get_noise_reason(self, title: str, intent: ShoppingSearchIntent) -> str | None:
        """给出被过滤原因；若保留则返回 None。"""

        accessory_hits = [keyword for keyword in self.ACCESSORY_KEYWORDS if keyword in title]
        if accessory_hits:
            return f"命中配件/非窗产品关键词：{'、'.join(accessory_hits)}"

        if intent.solution_type == "replace_window":
            has_window_signal = any(keyword in title for keyword in self.WINDOW_SIGNAL_KEYWORDS)
            if not has_window_signal:
                return "整窗更换场景下未识别到明显窗产品信号"

        negative_hits = [keyword for keyword in intent.negative_keywords if keyword and keyword in title]
        if negative_hits:
            return f"命中负向关键词：{'、'.join(negative_hits)}"

        return None

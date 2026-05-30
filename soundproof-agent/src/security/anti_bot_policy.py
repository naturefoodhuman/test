# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:55:19 CST

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AntiBotDecision:
    """反爬风险决策。"""

    allowed: bool
    suggested_delay_seconds: float
    reasons: list[str]


class ShoppingAntiBotPolicy:
    """购物平台反爬与封号风险控制策略。"""

    def __init__(
        self,
        *,
        max_detail_pages_per_run: int = 5,
        max_searches_per_hour: int = 20,
        max_review_fetches_per_run: int = 3,
        base_delay_seconds: float = 2.5,
    ) -> None:
        self.max_detail_pages_per_run = max_detail_pages_per_run
        self.max_searches_per_hour = max_searches_per_hour
        self.max_review_fetches_per_run = max_review_fetches_per_run
        self.base_delay_seconds = base_delay_seconds

    def evaluate_search(self, *, searches_in_last_hour: int) -> AntiBotDecision:
        """评估一次搜索是否应继续。"""

        reasons: list[str] = []
        allowed = True
        delay = self.base_delay_seconds

        if searches_in_last_hour >= self.max_searches_per_hour:
            allowed = False
            reasons.append("最近一小时搜索次数过多，应停止自动抓取并等待人工恢复")
        elif searches_in_last_hour >= int(self.max_searches_per_hour * 0.7):
            delay += 2.0
            reasons.append("搜索频率偏高，建议显著放慢节奏")

        return AntiBotDecision(allowed=allowed, suggested_delay_seconds=delay, reasons=reasons)

    def evaluate_detail_batch(self, *, requested_detail_pages: int) -> AntiBotDecision:
        """评估一批详情页抓取是否应继续。"""

        reasons: list[str] = []
        allowed = True
        delay = self.base_delay_seconds

        if requested_detail_pages > self.max_detail_pages_per_run:
            allowed = False
            reasons.append("单次详情页抓取过多，建议缩减到安全范围内")
        elif requested_detail_pages >= max(3, self.max_detail_pages_per_run - 1):
            delay += 1.5
            reasons.append("详情页抓取数量较高，建议逐页慢速执行")

        return AntiBotDecision(allowed=allowed, suggested_delay_seconds=delay, reasons=reasons)

    def evaluate_review_batch(self, *, requested_review_fetches: int) -> AntiBotDecision:
        """评估评论抓取批次是否应继续。"""

        reasons: list[str] = []
        allowed = True
        delay = self.base_delay_seconds

        if requested_review_fetches > self.max_review_fetches_per_run:
            allowed = False
            reasons.append("单次评论增强商品数过多，建议只保留前几个候选做评论审查")
        elif requested_review_fetches >= max(2, self.max_review_fetches_per_run):
            delay += 1.0
            reasons.append("评论抓取数量较高，建议按候选顺序慢速补抓")

        return AntiBotDecision(allowed=allowed, suggested_delay_seconds=delay, reasons=reasons)

    def should_stop_on_captcha(self) -> AntiBotDecision:
        """遇到验证码/滑块时的统一策略。"""

        return AntiBotDecision(
            allowed=False,
            suggested_delay_seconds=0.0,
            reasons=["出现验证码或风控页面，应立即停止自动执行并切换人工接管"],
        )

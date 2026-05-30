# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:05:58 CST

from __future__ import annotations

from pydantic import BaseModel, Field


class PageRiskReport(BaseModel):
    """页面风险识别结果。"""

    detected: bool = False
    risk_type: str | None = None
    signals: list[str] = Field(default_factory=list)
    preview: str = ""


RISK_RULES: list[tuple[str, list[str]]] = [
    ("captcha", ["验证码", "滑块", "请完成验证", "请拖动滑块", "security check"]),
    ("access_limited", ["访问受限", "访问异常", "稍后再试", "系统繁忙", "访问过于频繁"]),
    ("login_required", ["请登录后继续", "登录后查看", "亲，请登录"]),
]


def detect_page_risk(text: str) -> PageRiskReport:
    """从页面文本中识别风控/验证码/访问受限信号。"""

    normalized = (text or "").strip()
    compact = " ".join(normalized.split())

    for risk_type, signals in RISK_RULES:
        matched = [signal for signal in signals if signal.lower() in compact.lower()]
        if matched:
            return PageRiskReport(
                detected=True,
                risk_type=risk_type,
                signals=matched,
                preview=compact[:300],
            )

    return PageRiskReport(detected=False, preview=compact[:300])

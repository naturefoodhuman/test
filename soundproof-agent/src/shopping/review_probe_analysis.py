# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 16:28:41 CST

from __future__ import annotations

from typing import Any


def analyze_review_probe(payload: dict[str, Any]) -> dict[str, Any]:
    """分析评论探针结果并给出建议。"""

    suggestions: list[str] = []
    risk = payload.get("risk", {}) or {}
    review_count = int(payload.get("review_count", 0) or 0)
    with_images = int(payload.get("with_images", 0) or 0)
    anonymous_count = int(payload.get("anonymous_count", 0) or 0)
    avg_length = float(payload.get("average_length", 0) or 0)
    selector_counts = payload.get("selector_counts", []) or []

    if risk.get("detected"):
        suggestions.append("评论区域命中风控/验证码，先停止自动抓取评论并切人工接管。")

    positive_selectors = [item for item in selector_counts if int(item.get("count", 0) or 0) > 0]
    if not positive_selectors:
        suggestions.append("评论容器选择器全部未命中，优先检查评论区域结构。")

    if review_count == 0:
        suggestions.append("未抓到评论，优先检查评论 tab 选择器和评论容器规则。")
    elif review_count < 3:
        suggestions.append("评论数量较少，建议继续向下滚动或补充评论容器选择器。")

    if review_count > 0 and avg_length < 12:
        suggestions.append("评论平均长度偏短，可能抓到了模板评论或无效节点。")

    if review_count > 0 and with_images == 0:
        suggestions.append("当前评论样本中没有带图评论，可考虑增加滚动后再抓。")

    if review_count > 0 and anonymous_count == review_count:
        suggestions.append("当前样本全部匿名，建议继续抓取更多评论以提升参考价值。")

    if review_count >= 3 and not risk.get("detected"):
        suggestions.append("评论探针结果基本可用，可继续接评论增强链路。")

    readiness = "ready" if review_count >= 3 and not risk.get("detected") else "needs_fix"
    return {
        "readiness": readiness,
        "suggestions": suggestions,
        "review_count": review_count,
        "with_images": with_images,
        "anonymous_count": anonymous_count,
        "average_length": avg_length,
        "positive_selector_count": len(positive_selectors),
    }

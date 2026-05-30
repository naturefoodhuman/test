# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 15:18:42 CST

from __future__ import annotations

from typing import Any


def analyze_full_probe(
    *,
    search_probe: dict[str, Any] | None = None,
    detail_probe: dict[str, Any] | None = None,
    review_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """把搜索页、详情页、评论区探针结果汇总成一份联调建议。

    目标：
    - 在首次真实联调时，尽量把“先看哪一层问题”说清楚；
    - 减少开发者来回切换多个 JSON 的成本；
    - 为 CLI / API / Web 提供统一的联调判断口径。
    """

    readiness_chain: list[str] = []
    next_actions: list[str] = []
    blocking_issues: list[str] = []

    if search_probe is not None:
        search_analysis = search_probe.get("analysis", {}) or {}
        readiness_chain.append(f"search:{search_analysis.get('readiness', 'unknown')}")
        next_actions.extend(search_analysis.get("suggestions", []))
        if search_analysis.get("readiness") == "needs_fix":
            blocking_issues.append("搜索页探针未通过")

    if detail_probe is not None:
        detail_analysis = detail_probe.get("analysis", {}) or {}
        readiness_chain.append(f"detail:{detail_analysis.get('readiness', 'unknown')}")
        next_actions.extend(detail_analysis.get("suggestions", []))
        if detail_analysis.get("readiness") == "needs_fix":
            blocking_issues.append("详情页探针未通过")

    if review_probe is not None:
        review_analysis = review_probe.get("analysis", {}) or {}
        readiness_chain.append(f"review:{review_analysis.get('readiness', 'unknown')}")
        next_actions.extend(review_analysis.get("suggestions", []))
        if review_analysis.get("readiness") == "needs_fix":
            blocking_issues.append("评论探针未通过")

    deduplicated_actions: list[str] = []
    for item in next_actions:
        normalized = item.strip()
        if normalized and normalized not in deduplicated_actions:
            deduplicated_actions.append(normalized)

    overall_readiness = "ready"
    if blocking_issues:
        overall_readiness = "needs_fix"

    return {
        "overall_readiness": overall_readiness,
        "readiness_chain": readiness_chain,
        "blocking_issues": blocking_issues,
        "next_actions": deduplicated_actions,
    }

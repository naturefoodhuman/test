# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 02:20:18 CST

from __future__ import annotations

from statistics import mean
from typing import Any

from shopping.cache_models import ShoppingRunCache


def build_history_summary(runs: list[ShoppingRunCache]) -> dict[str, Any]:
    """对最近若干次运行做摘要分析。

    目的：
    - 给 CLI / API / Web 一个轻量的总体视图；
    - 让开发者一眼看出最近是否有大量失败/跳过；
    - 不做复杂 BI，只提供联调期最需要的统计。
    """

    if not runs:
        return {
            "run_count": 0,
            "avg_candidate_count": 0.0,
            "avg_effective_review_count": 0.0,
            "step_status_breakdown": {},
            "top_risk_notes": [],
        }

    candidate_counts = [len([entry for entry in run.entries if entry.detail is not None]) for run in runs]
    effective_review_counts = [
        sum(entry.detail.review_effective_count for entry in run.entries if entry.detail is not None)
        for run in runs
    ]

    step_status_breakdown: dict[str, int] = {}
    top_risk_notes: list[str] = []

    for run in runs:
        for step in run.step_traces:
            key = f"{step.step}:{step.status}"
            step_status_breakdown[key] = step_status_breakdown.get(key, 0) + 1
        if run.summary is not None:
            for note in run.summary.risk_points:
                if note not in top_risk_notes and len(top_risk_notes) < 8:
                    top_risk_notes.append(note)

    return {
        "run_count": len(runs),
        "avg_candidate_count": round(mean(candidate_counts), 2),
        "avg_effective_review_count": round(mean(effective_review_counts), 2),
        "step_status_breakdown": step_status_breakdown,
        "top_risk_notes": top_risk_notes,
    }

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 03:20:12 CST

from __future__ import annotations

from typing import Any

from shopping.cache_models import ShoppingRunCache


def compare_runs(left: ShoppingRunCache, right: ShoppingRunCache) -> dict[str, Any]:
    """比较两次运行的差异。

    目的：
    - 联调过程中快速观察“改动前后”差异；
    - 尤其适合 selector override 或提取策略调整后的效果回归；
    - 输出以 JSON 友好为主，便于 CLI / API / Web 直接复用。
    """

    left_snapshot = left.to_snapshot()
    right_snapshot = right.to_snapshot()

    left_titles = [item.title for item in left_snapshot.detailed_products]
    right_titles = [item.title for item in right_snapshot.detailed_products]

    left_risks = set(left_snapshot.comparison_summary.risk_points if left_snapshot.comparison_summary else [])
    right_risks = set(right_snapshot.comparison_summary.risk_points if right_snapshot.comparison_summary else [])

    return {
        "left_run_id": left.run_id,
        "right_run_id": right.run_id,
        "search_query_changed": left.search_query != right.search_query,
        "recommended_option_changed": _safe_recommended(left) != _safe_recommended(right),
        "summary_reason_changed": _safe_reason(left) != _safe_reason(right),
        "candidate_count": {
            "left": len(left_snapshot.detailed_products),
            "right": len(right_snapshot.detailed_products),
            "delta": len(right_snapshot.detailed_products) - len(left_snapshot.detailed_products),
        },
        "filtered_out_count": {
            "left": len(left_snapshot.filtered_out_products),
            "right": len(right_snapshot.filtered_out_products),
            "delta": len(right_snapshot.filtered_out_products) - len(left_snapshot.filtered_out_products),
        },
        "artifact_count": {
            "left": len(left_snapshot.artifact_names),
            "right": len(right_snapshot.artifact_names),
            "delta": len(right_snapshot.artifact_names) - len(left_snapshot.artifact_names),
        },
        "candidate_titles": {
            "left_only": sorted(set(left_titles) - set(right_titles)),
            "right_only": sorted(set(right_titles) - set(left_titles)),
            "common": sorted(set(left_titles) & set(right_titles)),
        },
        "risk_points": {
            "left_only": sorted(left_risks - right_risks),
            "right_only": sorted(right_risks - left_risks),
            "common": sorted(left_risks & right_risks),
        },
        "step_durations": _compare_step_durations(left.step_traces, right.step_traces),
    }


def _safe_recommended(run_cache: ShoppingRunCache) -> str | None:
    return run_cache.summary.recommended_option if run_cache.summary else None


def _safe_reason(run_cache: ShoppingRunCache) -> str | None:
    return run_cache.summary.reason_summary if run_cache.summary else None


def _compare_step_durations(left_steps, right_steps) -> list[dict[str, Any]]:
    left_map = {item.step: item.duration_ms for item in left_steps}
    right_map = {item.step: item.duration_ms for item in right_steps}
    step_names = sorted(set(left_map) | set(right_map))
    return [
        {
            "step": name,
            "left_duration_ms": left_map.get(name),
            "right_duration_ms": right_map.get(name),
            "delta_ms": (right_map.get(name, 0) - left_map.get(name, 0)) if name in left_map and name in right_map else None,
        }
        for name in step_names
    ]

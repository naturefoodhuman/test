# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 01:18:32 CST

from __future__ import annotations

from pathlib import Path
from typing import Any

from shopping.artifact_inspector import list_artifacts
from shopping.selector_manager import build_selector_override_diff


def build_runtime_diagnostics(
    *,
    profile_manager,
    cache_store,
    artifact_limit: int = 20,
    selector_override_path: str | Path | None = None,
    selector_profile: Any | None = None,
) -> dict[str, Any]:
    """构建运行时诊断信息。"""

    recent_events = cache_store.summarize_recent_events(3600)
    recent_artifacts = list_artifacts(profile_manager.artifact_root)[:artifact_limit]
    latest_run_id = cache_store.latest_run_id()

    selector_override_exists = False
    selector_override_path_str = None
    if selector_override_path is not None:
        selector_override = Path(selector_override_path)
        selector_override_path_str = str(selector_override)
        selector_override_exists = selector_override.exists()

    selector_summary = None
    if selector_profile is not None:
        selector_summary = {
            "search_card_candidates": len(selector_profile.search.card_candidates),
            "detail_title_selectors": len(selector_profile.detail.title_selectors),
            "detail_shop_selectors": len(selector_profile.detail.shop_name_selectors),
            "detail_price_selectors": len(selector_profile.detail.price_selectors),
            "review_tab_selectors": len(selector_profile.review.review_tab_selectors),
        }

    selector_override_diff = build_selector_override_diff(selector_override_path) if selector_override_path else {"exists": False, "changed_fields": []}

    return {
        "profile_root": str(profile_manager.profile_root),
        "artifact_root": str(profile_manager.artifact_root),
        "cache_db_path": str(profile_manager.cache_db_path),
        "latest_run_id": latest_run_id,
        "recent_event_stats": recent_events,
        "recent_artifacts": recent_artifacts,
        "selector_override_path": selector_override_path_str,
        "selector_override_exists": selector_override_exists,
        "selector_summary": selector_summary,
        "selector_override_diff": selector_override_diff,
    }

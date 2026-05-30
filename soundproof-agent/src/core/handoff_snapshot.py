# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:44:06 CST

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.model_router import load_model_router
from shopping.diagnostics import build_runtime_diagnostics
from shopping.factory import build_shopping_runtime_bundle


def build_handoff_snapshot(project_root: str | Path, artifact_limit: int = 20) -> dict[str, Any]:
    """构建给下一个 Agent 的运行快照。

    目标：
    - 让接手者一眼看到当前运行时状态；
    - 减少重新摸索目录、路由、最近运行和 artifact 的成本；
    - 作为 CLI/API 的共用能力。
    """

    root = Path(project_root).resolve()
    bundle = build_shopping_runtime_bundle(root)
    router = load_model_router(root / 'model_router.yaml')
    diagnostics = build_runtime_diagnostics(
        profile_manager=bundle.profile_manager,
        cache_store=bundle.cache_store,
        artifact_limit=artifact_limit,
        selector_override_path=bundle.project_root / bundle.config.phase1.shopping.selector_override_path,
        selector_profile=getattr(bundle, "selector_profile", None),
    )

    return {
        'project_root': str(root),
        'phase': 'phase1',
        'router_status': router.status,
        'shopping_summary_model': router.get_primary('shopping_summary'),
        'shopping_field_model': router.get_primary('shopping_field_normalizer'),
        'diagnostics': diagnostics,
    }

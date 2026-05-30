# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 15:02:22 CST
# 最后更新（北京时间，精确到秒）：2026-05-30 14:30:00 CST

from __future__ import annotations

from functools import wraps
from pathlib import Path
from typing import Any, Callable

from api.schemas import (
    DetailOnceRequest,
    FullProbeRequest,
    LiveRunRequest,
    ProbeDetailRequest,
    ReplayRunRequest,
    ReviewProbeRequest,
    SearchOnceRequest,
    SearchProbeRequest,
    SelectorBackupActionRequest,
    SelectorOverrideSaveRequest,
)
from core.handoff_snapshot import build_handoff_snapshot
from shopping.app_service import ShoppingApplicationService
from shopping.artifact_inspector import artifact_exists, list_artifacts, read_artifact_text
from shopping.diagnostics import build_runtime_diagnostics
from shopping.factory import build_shopping_runtime_bundle
from shopping.intent_builder import ConsultationContext, ShoppingIntentBuilder
from shopping.preflight import run_phase1_preflight
from shopping.replay_executor import ReplayShoppingExecutor
from shopping.schemas import ListingProduct
from shopping.selector_loader import dump_default_selector_profile_yaml
from shopping.selector_manager import (
    backup_selector_override,
    build_selector_override_diff,
    list_selector_override_backups,
    read_selector_override_backup,
    read_selector_override_text,
    reset_selector_override_to_default,
    restore_selector_override_backup,
    validate_selector_override,
    write_selector_override_text,
)


# API tag 分组（统一在 FastAPI / OpenAPI 文档里组织）。
TAG_SYSTEM = "system"
TAG_INTENT = "shopping/intent"
TAG_REPLAY = "shopping/replay"
TAG_LIVE = "shopping/live"
TAG_PROBE = "shopping/probe"
TAG_HISTORY = "shopping/history"
TAG_SELECTORS = "shopping/selectors"
TAG_ARTIFACTS = "shopping/artifacts"


def create_app(project_root: str | Path = "."):
    """创建 FastAPI 应用。"""

    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import PlainTextResponse
    except ModuleNotFoundError as exc:  # pragma: no cover - 依赖型逻辑
        raise RuntimeError("未安装 FastAPI，请执行 `uv sync --extra web`。") from exc

    from shopping.errors import ShoppingExecutionError, ShoppingRiskDetectedError
    from web.routes import create_web_router

    root = Path(project_root).resolve()
    runtime_bundle = build_shopping_runtime_bundle(root)
    replay_service = ShoppingApplicationService(
        executor=ReplayShoppingExecutor(root / "tests" / "fixtures"),
        cache_store=runtime_bundle.cache_store,
        summary_service=None,
        field_normalizer_service=None,
    )
    live_service = ShoppingApplicationService(
        executor=__build_live_executor(runtime_bundle),
        cache_store=runtime_bundle.cache_store,
        summary_service=runtime_bundle.summary_service,
        field_normalizer_service=runtime_bundle.field_normalizer_service,
        anti_bot_policy=runtime_bundle.anti_bot_policy,
        review_enricher=runtime_bundle.review_enricher,
        review_top_n=runtime_bundle.config.phase1.shopping.reviews.top_n,
        enforce_delay=runtime_bundle.config.phase1.shopping.anti_bot.enforce_delay,
    )

    app = FastAPI(
        title="Soundproof Agent API",
        version="0.1.0",
        description=(
            "隔音窗购物 Agent 的 HTTP 接口。\n\n"
            "分组：\n"
            "- `shopping/intent`：购物意图预览\n"
            "- `shopping/replay`：离线回放运行（不联网）\n"
            "- `shopping/live`：真实淘宝执行（需登录 + Playwright）\n"
            "- `shopping/probe`：联调期探针（搜索/详情/评论/全链路）\n"
            "- `shopping/history`：历史 run 查询/对比/分析/导出\n"
            "- `shopping/selectors`：选择器配置查询/覆盖/恢复\n"
            "- `shopping/artifacts`：调试产物读写\n"
            "- `system`：健康检查 / 诊断 / handoff / preflight"
        ),
        openapi_tags=[
            {"name": TAG_SYSTEM, "description": "健康检查、诊断、handoff、preflight"},
            {"name": TAG_INTENT, "description": "把咨询上下文翻译为购物意图（预览不抓取）"},
            {"name": TAG_REPLAY, "description": "用本地 fixture 回放完整购物链路（不联网，CI 友好）"},
            {"name": TAG_LIVE, "description": "真实淘宝执行：search / detail / live-run"},
            {"name": TAG_PROBE, "description": "联调期探针：搜索 / 详情 / 评论 / 全链路"},
            {"name": TAG_HISTORY, "description": "历史 run 查询 / 对比 / 分析 / 报告导出 / 归档"},
            {"name": TAG_SELECTORS, "description": "选择器配置：默认 / override / 备份 / 校验"},
            {"name": TAG_ARTIFACTS, "description": "调试产物读取（HTML/JSON/PNG）"},
        ],
    )
    app.include_router(create_web_router(root))

    def _map_to_http_exception(exc: Exception) -> HTTPException:
        """把购物执行异常统一映射为 HTTPException。"""

        if isinstance(exc, ShoppingRiskDetectedError):
            return HTTPException(status_code=409, detail={"error_type": "risk_detected", "message": str(exc)})
        if isinstance(exc, ShoppingExecutionError):
            return HTTPException(status_code=400, detail={"error_type": "execution_error", "message": str(exc)})
        if isinstance(exc, RuntimeError):
            # 例如 Playwright 未安装、依赖缺失
            return HTTPException(status_code=503, detail={"error_type": "runtime_error", "message": str(exc)})
        if isinstance(exc, ValueError):
            return HTTPException(status_code=400, detail={"error_type": "value_error", "message": str(exc)})
        return HTTPException(status_code=500, detail={"error_type": "internal_error", "message": str(exc)})

    def handle_shopping_errors(func: Callable[..., Any]) -> Callable[..., Any]:
        """装饰器：把购物相关异常统一转 HTTPException。"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as exc:  # noqa: BLE001 - 显式聚合所有非 HTTPException 异常
                raise _map_to_http_exception(exc) from exc

        return wrapper

    @app.get("/health", tags=[TAG_SYSTEM], summary="健康检查")
    def health() -> dict:
        return {
            "status": "ok",
            "phase": "phase1",
            "project_root": str(root),
        }

    @app.get("/api/handoff", tags=[TAG_SYSTEM], summary="导出 handoff 快照")
    def handoff(artifact_limit: int = 20) -> dict:
        return build_handoff_snapshot(root, artifact_limit=artifact_limit)

    @app.get("/api/diagnostics", tags=[TAG_SYSTEM], summary="运行时诊断")
    def diagnostics(artifact_limit: int = 20) -> dict:
        return build_runtime_diagnostics(
            profile_manager=runtime_bundle.profile_manager,
            cache_store=runtime_bundle.cache_store,
            artifact_limit=artifact_limit,
            selector_override_path=runtime_bundle.project_root / runtime_bundle.config.phase1.shopping.selector_override_path,
            selector_profile=runtime_bundle.selector_profile,
        )

    @app.get("/api/router", tags=[TAG_SYSTEM], summary="读取模型路由")
    def get_router() -> dict:
        return runtime_bundle.router.model_dump()

    @app.get("/api/preflight", tags=[TAG_SYSTEM], summary="Phase 1 预检查")
    def get_preflight() -> dict:
        return run_phase1_preflight(root, runtime_bundle.config.phase1.shopping)

    @app.get("/api/selectors/default", tags=[TAG_SELECTORS], summary="读取默认选择器配置")
    def default_selectors() -> dict:
        return runtime_bundle.selector_profile.model_dump()

    @app.get("/api/selectors/default.yaml", response_class=PlainTextResponse, tags=[TAG_SELECTORS], summary="读取默认选择器 YAML 文本")
    def default_selectors_yaml() -> str:
        return dump_default_selector_profile_yaml()

    @app.get("/api/selectors/override", tags=[TAG_SELECTORS], summary="读取 override 文本")
    def selector_override_text() -> dict:
        content = read_selector_override_text(root / runtime_bundle.config.phase1.shopping.selector_override_path)
        return {"content": content}

    @app.get("/api/selectors/override/validate", tags=[TAG_SELECTORS], summary="校验 override")
    def selector_override_validate() -> dict:
        return validate_selector_override(root / runtime_bundle.config.phase1.shopping.selector_override_path)

    @app.get("/api/selectors/override/diff", tags=[TAG_SELECTORS], summary="override 与默认值差异")
    def selector_override_diff() -> dict:
        path = root / runtime_bundle.config.phase1.shopping.selector_override_path
        return build_selector_override_diff(path)

    @app.post("/api/selectors/override", tags=[TAG_SELECTORS], summary="保存 override（可选自动备份）")
    def save_selector_override(payload: SelectorOverrideSaveRequest) -> dict:
        path = root / runtime_bundle.config.phase1.shopping.selector_override_path
        if payload.backup:
            backup_selector_override(path)
        write_selector_override_text(path, payload.content)
        return validate_selector_override(path)

    @app.post("/api/selectors/override/reset", tags=[TAG_SELECTORS], summary="把 override 重置为默认")
    def selector_override_reset(backup: bool = True) -> dict:
        path = root / runtime_bundle.config.phase1.shopping.selector_override_path
        if backup:
            backup_selector_override(path)
        output = reset_selector_override_to_default(path)
        return {"output_path": str(output), "validation": validate_selector_override(output)}

    @app.get("/api/selectors/override/backups", tags=[TAG_SELECTORS], summary="列出 override 备份")
    def selector_override_backups(limit: int = 20) -> dict:
        path = root / runtime_bundle.config.phase1.shopping.selector_override_path
        return {"items": list_selector_override_backups(path, limit=limit)}

    @app.get(
        "/api/selectors/override/backups/{backup_name}",
        response_class=PlainTextResponse,
        tags=[TAG_SELECTORS],
        summary="读取单个 override 备份内容",
    )
    def selector_override_backup_content(backup_name: str) -> str:
        path = root / runtime_bundle.config.phase1.shopping.selector_override_path
        content = read_selector_override_backup(path, backup_name)
        if content is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "backup not found"})
        return content

    @app.post("/api/selectors/override/backups/restore", tags=[TAG_SELECTORS], summary="恢复某个备份为当前 override")
    def selector_override_restore(payload: SelectorBackupActionRequest) -> dict:
        path = root / runtime_bundle.config.phase1.shopping.selector_override_path
        restored = restore_selector_override_backup(path, payload.backup_name)
        if restored is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "backup not found"})
        return validate_selector_override(path)

    @app.get("/api/shopping/intent/preview", tags=[TAG_INTENT], summary="预览购物意图（不抓取）")
    def preview_intent(
        scene: str = "高架低频卧室",
        budget: int = 8000,
        noise_source: str = "traffic",
        frequency_profile: str = "low",
        preferred_solution: str = "replace_window",
    ) -> dict:
        context = ConsultationContext(
            scene=scene,
            budget=budget,
            noise_source=noise_source,
            frequency_profile=frequency_profile,
            preferred_solution=preferred_solution,
            room_type="卧室",
        )
        return ShoppingIntentBuilder().build(context).model_dump()

    @app.post("/api/shopping/replay-run", tags=[TAG_REPLAY], summary="本地 fixture 回放完整购物链路")
    @handle_shopping_errors
    def replay_run(payload: ReplayRunRequest) -> dict:
        snapshot = replay_service.run_from_consultation_context(payload.to_consultation_context(), limit=payload.limit)
        return snapshot.model_dump()

    @app.post("/api/shopping/probe-search", tags=[TAG_PROBE], summary="搜索页探针")
    @handle_shopping_errors
    def probe_search(payload: SearchProbeRequest) -> dict:
        return live_service.executor.probe_search_query(payload.query, wait_after_load_ms=payload.wait_after_load_ms)

    @app.post("/api/shopping/probe-detail", tags=[TAG_PROBE], summary="详情页探针")
    @handle_shopping_errors
    def probe_detail(payload: ProbeDetailRequest) -> dict:
        return live_service.executor.probe_detail_url(payload.detail_url, wait_after_load_ms=payload.wait_after_load_ms)

    @app.post("/api/shopping/probe-reviews", tags=[TAG_PROBE], summary="评论探针")
    @handle_shopping_errors
    def probe_reviews(payload: ReviewProbeRequest) -> dict:
        result = live_service.probe_reviews_for_detail(
            title=payload.title,
            detail_url=payload.detail_url,
            limit=payload.limit,
        )
        if result is None:
            raise HTTPException(
                status_code=400,
                detail={"error_type": "review_probe_unavailable", "message": "review enricher 未配置或 fetcher 缺少 probe_reviews 实现"},
            )
        return result

    @app.post("/api/shopping/probe-full", tags=[TAG_PROBE], summary="全链路联调探针")
    @handle_shopping_errors
    def probe_full(payload: FullProbeRequest) -> dict:
        return live_service.probe_full_candidate(
            query=payload.query,
            title=payload.title,
            detail_url=payload.detail_url,
            wait_after_load_ms=payload.wait_after_load_ms,
            review_limit=payload.review_limit,
        )

    @app.post("/api/shopping/search-once", tags=[TAG_LIVE], summary="真实淘宝搜索一次")
    @handle_shopping_errors
    def search_once(payload: SearchOnceRequest) -> dict:
        products = live_service.search_once(payload.query, limit=payload.limit)
        return {"items": [item.model_dump() for item in products]}

    @app.post("/api/shopping/detail-once", tags=[TAG_LIVE], summary="真实淘宝详情抓取一次")
    @handle_shopping_errors
    def detail_once(payload: DetailOnceRequest) -> dict:
        listing = ListingProduct(
            title=payload.title,
            detail_url=payload.detail_url,
            price_text=payload.price_text,
            shop_name=payload.shop_name,
        )
        detail = live_service.detail_once(listing, normalize_with_llm=payload.normalize_with_llm)
        return detail.model_dump()

    @app.post("/api/shopping/live-run", tags=[TAG_LIVE], summary="真实淘宝完整链路运行")
    @handle_shopping_errors
    def live_run(payload: LiveRunRequest) -> dict:
        snapshot = live_service.run_from_consultation_context(payload.to_consultation_context(), limit=payload.limit)
        return snapshot.model_dump()

    @app.get("/api/shopping/history-summary", tags=[TAG_HISTORY], summary="历史 run 汇总")
    def history_summary(limit: int = 20) -> dict:
        return replay_service.history_summary(limit=limit)

    @app.get("/api/shopping/events", tags=[TAG_HISTORY], summary="执行事件日志")
    def event_log(limit: int = 50) -> dict:
        return {"items": replay_service.recent_events(limit=limit)}

    @app.get("/api/shopping/event-stats", tags=[TAG_HISTORY], summary="执行事件统计")
    def event_stats(within_seconds: int = 3600) -> dict:
        return {"items": replay_service.recent_event_stats(within_seconds=within_seconds)}

    @app.get("/api/shopping/runs", tags=[TAG_HISTORY], summary="列出所有历史 run")
    def list_runs() -> dict:
        return {"items": replay_service.list_history()}

    @app.get("/api/shopping/runs/latest", tags=[TAG_HISTORY], summary="读取最近一次 run")
    def latest_run() -> dict:
        run_id = runtime_bundle.cache_store.latest_run_id()
        if run_id is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "no runs yet"})
        result = replay_service.get_history(run_id)
        if result is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "run not found"})
        return result

    @app.get("/api/shopping/runs/latest/analysis", tags=[TAG_HISTORY], summary="最近一次 run 的分析")
    def latest_run_analysis() -> dict:
        payload = replay_service.analyze_latest_run()
        if payload is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "no runs yet"})
        return payload

    @app.get(
        "/api/shopping/runs/latest/report",
        response_class=PlainTextResponse,
        tags=[TAG_HISTORY],
        summary="最近一次 run 的 Markdown 报告",
    )
    def latest_report() -> str:
        report = replay_service.build_latest_report()
        if report is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "no runs yet"})
        return report

    @app.post("/api/shopping/runs/latest/archive", tags=[TAG_HISTORY], summary="导出最近一次 run 的 zip")
    def latest_archive() -> dict:
        result = replay_service.export_latest_archive(root / "runtime" / "exports" / "archives")
        if result is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "no runs yet"})
        return result

    @app.get("/api/shopping/runs/compare/latest", tags=[TAG_HISTORY], summary="比较最近两次 run")
    def compare_latest_runs() -> dict:
        payload = replay_service.compare_latest_two_runs()
        if payload is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "not enough runs"})
        return payload

    @app.get("/api/shopping/runs/{run_id}", tags=[TAG_HISTORY], summary="读取某次 run")
    def get_run(run_id: str) -> dict:
        result = replay_service.get_history(run_id)
        if result is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "run not found"})
        return result

    @app.get("/api/shopping/runs/{run_id}/analysis", tags=[TAG_HISTORY], summary="某次 run 的分析")
    def run_analysis(run_id: str) -> dict:
        payload = replay_service.analyze_history_run(run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "run not found"})
        return payload

    @app.get(
        "/api/shopping/runs/{run_id}/report",
        response_class=PlainTextResponse,
        tags=[TAG_HISTORY],
        summary="某次 run 的 Markdown 报告",
    )
    def get_run_report(run_id: str) -> str:
        report = replay_service.build_history_report(run_id)
        if report is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "run not found"})
        return report

    @app.get("/api/shopping/runs/{run_id}/artifact-manifest", tags=[TAG_HISTORY], summary="某次 run 的 artifact manifest")
    def get_run_artifact_manifest(run_id: str) -> dict:
        return {"items": replay_service.build_artifact_manifest(run_id)}

    @app.get("/api/shopping/runs/{run_id}/artifacts", tags=[TAG_HISTORY], summary="某次 run 的 artifact 文件清单")
    def get_run_artifacts(run_id: str) -> dict:
        return {"items": replay_service.list_run_artifacts(run_id)}

    @app.post("/api/shopping/runs/{run_id}/archive", tags=[TAG_HISTORY], summary="导出某次 run 的 zip")
    def run_archive(run_id: str) -> dict:
        result = replay_service.export_run_archive(run_id, root / "runtime" / "exports" / "archives")
        if result is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "run not found"})
        return result

    @app.get("/api/shopping/runs/compare", tags=[TAG_HISTORY], summary="比较任意两次 run")
    def compare_runs(left_run_id: str, right_run_id: str) -> dict:
        payload = replay_service.compare_history_runs(left_run_id, right_run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "run not found"})
        return payload

    @app.get("/api/artifacts", tags=[TAG_ARTIFACTS], summary="列出 artifact")
    def get_artifacts(prefix: str | None = None) -> dict:
        return {"items": list_artifacts(runtime_bundle.profile_manager.artifact_root, prefix=prefix)}

    @app.get("/api/artifacts/{name}/exists", tags=[TAG_ARTIFACTS], summary="判断 artifact 是否存在")
    def get_artifact_exists(name: str) -> dict:
        exists = artifact_exists(runtime_bundle.profile_manager.artifact_root, name)
        return {"name": name, "exists": exists}

    @app.get(
        "/api/artifacts/{name}",
        response_class=PlainTextResponse,
        tags=[TAG_ARTIFACTS],
        summary="读取 artifact 文本内容",
    )
    def get_artifact(name: str) -> str:
        content = read_artifact_text(runtime_bundle.profile_manager.artifact_root, name)
        if content is None:
            raise HTTPException(status_code=404, detail={"error_type": "not_found", "message": "artifact not found"})
        return content

    return app


def __build_live_executor(runtime_bundle):
    from shopping.playwright_executor import TaobaoPlaywrightExecutor

    return TaobaoPlaywrightExecutor(runtime_bundle.config.phase1.shopping, runtime_bundle.project_root)

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 16:02:44 CST

from __future__ import annotations

from pathlib import Path

from core.handoff_snapshot import build_handoff_snapshot
from shopping.app_service import ShoppingApplicationService
from shopping.artifact_inspector import artifact_exists, read_artifact_text
from shopping.diagnostics import build_runtime_diagnostics
from shopping.factory import build_shopping_runtime_bundle
from shopping.intent_builder import ConsultationContext
from shopping.replay_executor import ReplayShoppingExecutor
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


def create_web_router(project_root: str | Path = "."):
    """创建 Web 路由。"""

    try:
        from fastapi import APIRouter, Form, HTTPException, Request
        from fastapi.responses import HTMLResponse, RedirectResponse
        from fastapi.templating import Jinja2Templates
    except ModuleNotFoundError as exc:  # pragma: no cover - 依赖型逻辑
        raise RuntimeError("未安装 FastAPI/Jinja2，请执行 `uv sync --extra web`。") from exc

    root = Path(project_root).resolve()
    templates = Jinja2Templates(directory=str(root / "src" / "web" / "templates"))
    router = APIRouter()

    def _build_runtime():
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
        return runtime_bundle, replay_service, live_service

    def _selector_status(runtime_bundle):
        return build_runtime_diagnostics(
            profile_manager=runtime_bundle.profile_manager,
            cache_store=runtime_bundle.cache_store,
            artifact_limit=5,
            selector_override_path=runtime_bundle.project_root / runtime_bundle.config.phase1.shopping.selector_override_path,
            selector_profile=runtime_bundle.selector_profile,
        )

    def _build_dashboard_context():
        runtime_bundle, replay_service, _live_service = _build_runtime()
        diagnostics = build_handoff_snapshot(root, artifact_limit=10)
        runs = replay_service.list_history_summaries(limit=15)
        latest_report = replay_service.build_latest_report()
        latest_analysis = replay_service.analyze_latest_run()
        event_stats = replay_service.recent_event_stats(within_seconds=3600)
        recent_events = replay_service.recent_events(limit=12)
        selector_status = _selector_status(runtime_bundle)
        selector_path = runtime_bundle.project_root / runtime_bundle.config.phase1.shopping.selector_override_path
        selector_override_content = read_selector_override_text(selector_path)
        selector_override_validation = validate_selector_override(selector_path)
        selector_backups = list_selector_override_backups(selector_path, limit=10)
        selector_override_diff = build_selector_override_diff(selector_path)
        history_summary = replay_service.history_summary(limit=20)
        compare_latest = replay_service.compare_latest_two_runs()
        default_selector_yaml = dump_default_selector_profile_yaml()
        return {
            "project_root": str(root),
            "diagnostics": diagnostics,
            "runs": runs,
            "latest_report": latest_report,
            "latest_analysis": latest_analysis,
            "event_stats": event_stats,
            "recent_events": recent_events,
            "selector_status": selector_status,
            "selector_override_content": selector_override_content,
            "selector_override_validation": selector_override_validation,
            "selector_backups": selector_backups,
            "selector_override_diff": selector_override_diff,
            "history_summary": history_summary,
            "compare_latest": compare_latest,
            "default_selector_yaml": default_selector_yaml,
        }

    def _render_tools(request: Request, *, search_probe_result=None, detail_probe_result=None, review_probe_result=None, full_probe_result=None, save_message=None, backup_preview=None):
        runtime_bundle, _replay_service, _live_service = _build_runtime()
        selector_path = runtime_bundle.project_root / runtime_bundle.config.phase1.shopping.selector_override_path
        selector_status = _selector_status(runtime_bundle)
        selector_override_content = read_selector_override_text(selector_path)
        selector_override_validation = validate_selector_override(selector_path)
        selector_backups = list_selector_override_backups(selector_path, limit=10)
        selector_override_diff = build_selector_override_diff(selector_path)
        return templates.TemplateResponse(
            request,
            "tools.html",
            {
                "selector_status": selector_status,
                "search_probe_result": search_probe_result,
                "detail_probe_result": detail_probe_result,
                "review_probe_result": review_probe_result,
                "full_probe_result": full_probe_result,
                "selector_override_content": selector_override_content,
                "selector_override_validation": selector_override_validation,
                "selector_backups": selector_backups,
                "selector_override_diff": selector_override_diff,
                "save_message": save_message,
                "backup_preview": backup_preview,
                "default_selector_yaml": dump_default_selector_profile_yaml(),
            },
        )

    @router.get("/", response_class=HTMLResponse)
    def dashboard(request: Request):
        return templates.TemplateResponse(request, "dashboard.html", _build_dashboard_context())

    @router.get("/events", response_class=HTMLResponse)
    def event_log_page(request: Request):
        _runtime_bundle, replay_service, _live_service = _build_runtime()
        events = replay_service.recent_events(limit=100)
        return templates.TemplateResponse(request, "event_log.html", {"events": events})

    @router.post("/compare/latest", response_class=HTMLResponse)
    def compare_latest_redirect():
        return RedirectResponse(url="/compare/latest", status_code=303)

    @router.post("/compare/run-form", response_class=HTMLResponse)
    def compare_run_form(left_run_id: str = Form(...), right_run_id: str = Form(...)):
        return RedirectResponse(url=f"/compare?left_run_id={left_run_id}&right_run_id={right_run_id}", status_code=303)

    @router.get("/tools", response_class=HTMLResponse)
    def tools_page(request: Request):
        return _render_tools(request)

    @router.post("/tools/probe-full", response_class=HTMLResponse)
    def tools_probe_full(
        request: Request,
        query: str = Form(...),
        title: str = Form(...),
        detail_url: str = Form(...),
        wait_after_load_ms: int = Form(3000),
        review_limit: int = Form(10),
    ):
        _runtime_bundle, _replay_service, live_service = _build_runtime()
        result = live_service.probe_full_candidate(
            query=query,
            title=title,
            detail_url=detail_url,
            wait_after_load_ms=wait_after_load_ms,
            review_limit=review_limit,
        )
        return _render_tools(request, full_probe_result=result)

    @router.post("/tools/probe-search", response_class=HTMLResponse)
    def tools_probe_search(
        request: Request,
        query: str = Form(...),
        wait_after_load_ms: int = Form(3000),
    ):
        _runtime_bundle, _replay_service, live_service = _build_runtime()
        result = live_service.executor.probe_search_query(query, wait_after_load_ms=wait_after_load_ms)
        return _render_tools(request, search_probe_result=result)

    @router.post("/tools/probe-detail", response_class=HTMLResponse)
    def tools_probe_detail(
        request: Request,
        detail_url: str = Form(...),
        wait_after_load_ms: int = Form(3000),
    ):
        _runtime_bundle, _replay_service, live_service = _build_runtime()
        result = live_service.executor.probe_detail_url(detail_url, wait_after_load_ms=wait_after_load_ms)
        return _render_tools(request, detail_probe_result=result)

    @router.post("/tools/probe-reviews", response_class=HTMLResponse)
    def tools_probe_reviews(
        request: Request,
        title: str = Form(...),
        detail_url: str = Form(...),
        limit: int = Form(10),
    ):
        _runtime_bundle, _replay_service, live_service = _build_runtime()
        result = live_service.probe_reviews_for_detail(title=title, detail_url=detail_url, limit=limit)
        if result is None:
            raise HTTPException(status_code=400, detail="review probe not available")
        return _render_tools(request, review_probe_result=result)

    @router.post("/tools/save-selector-override", response_class=HTMLResponse)
    def tools_save_selector_override(
        request: Request,
        selector_override_content: str = Form(...),
    ):
        runtime_bundle, _replay_service, _live_service = _build_runtime()
        selector_path = runtime_bundle.project_root / runtime_bundle.config.phase1.shopping.selector_override_path
        backup_selector_override(selector_path)
        write_selector_override_text(selector_path, selector_override_content)
        return _render_tools(request, save_message=f"已保存到 {selector_path}")

    @router.post("/tools/reset-selector-override", response_class=HTMLResponse)
    def tools_reset_selector_override(
        request: Request,
        backup_before_reset: bool = Form(True),
    ):
        runtime_bundle, _replay_service, _live_service = _build_runtime()
        selector_path = runtime_bundle.project_root / runtime_bundle.config.phase1.shopping.selector_override_path
        if backup_before_reset:
            backup_selector_override(selector_path)
        reset_selector_override_to_default(selector_path)
        return _render_tools(request, save_message=f"已重置为默认模板：{selector_path}")

    @router.post("/tools/restore-selector-override", response_class=HTMLResponse)
    def tools_restore_selector_override(
        request: Request,
        backup_name: str = Form(...),
    ):
        runtime_bundle, _replay_service, _live_service = _build_runtime()
        selector_path = runtime_bundle.project_root / runtime_bundle.config.phase1.shopping.selector_override_path
        restored = restore_selector_override_backup(selector_path, backup_name)
        if restored is None:
            raise HTTPException(status_code=404, detail="backup not found")
        return _render_tools(request, save_message=f"已从备份恢复：{backup_name}")

    @router.post("/tools/preview-selector-backup", response_class=HTMLResponse)
    def tools_preview_selector_backup(
        request: Request,
        backup_name: str = Form(...),
    ):
        runtime_bundle, _replay_service, _live_service = _build_runtime()
        selector_path = runtime_bundle.project_root / runtime_bundle.config.phase1.shopping.selector_override_path
        content = read_selector_override_backup(selector_path, backup_name)
        if content is None:
            raise HTTPException(status_code=404, detail="backup not found")
        return _render_tools(request, backup_preview={"name": backup_name, "content": content})

    @router.post("/replay", response_class=HTMLResponse)
    def replay_run(
        request: Request,
        scene: str = Form("高架低频卧室"),
        budget: int = Form(8000),
        noise_source: str = Form("traffic"),
        frequency_profile: str = Form("low"),
        preferred_solution: str = Form("replace_window"),
        limit: int = Form(5),
    ):
        _runtime_bundle, replay_service, _live_service = _build_runtime()
        context = ConsultationContext(
            scene=scene,
            budget=budget,
            noise_source=noise_source,
            frequency_profile=frequency_profile,
            preferred_solution=preferred_solution,
            room_type="卧室",
        )
        snapshot = replay_service.run_from_consultation_context(context, limit=limit)
        return RedirectResponse(url=f"/runs/{snapshot.run_id}", status_code=303)

    @router.get("/runs/latest", response_class=HTMLResponse)
    def latest_run_redirect():
        runtime_bundle, _replay_service, _live_service = _build_runtime()
        run_id = runtime_bundle.cache_store.latest_run_id()
        if run_id is None:
            raise HTTPException(status_code=404, detail="no runs yet")
        return RedirectResponse(url=f"/runs/{run_id}", status_code=302)

    @router.get("/runs/latest/analysis", response_class=HTMLResponse)
    def latest_run_analysis(request: Request):
        _runtime_bundle, replay_service, _live_service = _build_runtime()
        payload = replay_service.analyze_latest_run()
        if payload is None:
            raise HTTPException(status_code=404, detail="no runs yet")
        return templates.TemplateResponse(request, "run_analysis.html", {"analysis": payload})

    @router.get("/compare/latest", response_class=HTMLResponse)
    def compare_latest(request: Request):
        _runtime_bundle, replay_service, _live_service = _build_runtime()
        payload = replay_service.compare_latest_two_runs()
        if payload is None:
            raise HTTPException(status_code=404, detail="not enough runs")
        return templates.TemplateResponse(request, "compare_runs.html", {"comparison": payload})

    @router.get("/compare", response_class=HTMLResponse)
    def compare_specific(request: Request, left_run_id: str, right_run_id: str):
        _runtime_bundle, replay_service, _live_service = _build_runtime()
        payload = replay_service.compare_history_runs(left_run_id, right_run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="run not found")
        return templates.TemplateResponse(request, "compare_runs.html", {"comparison": payload})

    @router.get("/runs/{run_id}/analysis", response_class=HTMLResponse)
    def run_analysis_page(request: Request, run_id: str):
        _runtime_bundle, replay_service, _live_service = _build_runtime()
        payload = replay_service.analyze_history_run(run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="run not found")
        return templates.TemplateResponse(request, "run_analysis.html", {"analysis": payload})

    @router.get("/runs/{run_id}", response_class=HTMLResponse)
    def run_detail(request: Request, run_id: str):
        _runtime_bundle, replay_service, _live_service = _build_runtime()
        run_payload = replay_service.get_history(run_id)
        if run_payload is None:
            raise HTTPException(status_code=404, detail="run not found")
        report_text = replay_service.build_history_report(run_id)
        artifact_names = replay_service.list_run_artifacts(run_id)
        artifact_manifest = replay_service.build_artifact_manifest(run_id)
        return templates.TemplateResponse(
            request,
            "run_detail.html",
            {
                "run_id": run_id,
                "run_payload": run_payload,
                "report_text": report_text,
                "artifact_names": artifact_names,
                "artifact_manifest": artifact_manifest,
                "artifact_count": len(artifact_manifest),
                "step_traces": run_payload.get("step_traces", []),
                "workflow_notes": run_payload.get("workflow_notes", []),
            },
        )

    @router.post("/runs/{run_id}/archive", response_class=HTMLResponse)
    def archive_run(run_id: str):
        _runtime_bundle, replay_service, _live_service = _build_runtime()
        result = replay_service.export_run_archive(run_id, root / "runtime" / "exports" / "archives")
        if result is None:
            raise HTTPException(status_code=404, detail="run not found")
        return RedirectResponse(url=f"/runs/{run_id}", status_code=303)

    @router.get("/runs/{run_id}/artifacts", response_class=HTMLResponse)
    def run_artifacts_page(request: Request, run_id: str):
        _runtime_bundle, replay_service, _live_service = _build_runtime()
        run_payload = replay_service.get_history(run_id)
        if run_payload is None:
            raise HTTPException(status_code=404, detail="run not found")
        artifact_manifest = replay_service.build_artifact_manifest(run_id)
        return templates.TemplateResponse(
            request,
            "artifact_manifest.html",
            {
                "run_id": run_id,
                "artifact_manifest": artifact_manifest,
            },
        )

    @router.get("/artifacts/{name}", response_class=HTMLResponse)
    def artifact_preview(request: Request, name: str):
        runtime_bundle, _replay_service, _live_service = _build_runtime()
        exists = artifact_exists(runtime_bundle.profile_manager.artifact_root, name)
        if not exists:
            raise HTTPException(status_code=404, detail="artifact not found")
        content = read_artifact_text(runtime_bundle.profile_manager.artifact_root, name)
        if content is None:
            raise HTTPException(status_code=404, detail="artifact not found")
        return templates.TemplateResponse(
            request,
            "artifact_detail.html",
            {
                "artifact_name": name,
                "content": content,
            },
        )

    return router


def __build_live_executor(runtime_bundle):
    from shopping.playwright_executor import TaobaoPlaywrightExecutor

    return TaobaoPlaywrightExecutor(runtime_bundle.config.phase1.shopping, runtime_bundle.project_root)

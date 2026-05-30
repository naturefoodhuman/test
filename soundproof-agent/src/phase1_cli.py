# 创建该文件的LLM大模型：Arena.ai Agent Mode（早期版本）
# 修改该文件的LLM大模型：Claude Sonnet 4.5 (via Arena.ai Agent Mode)
# 最后修改时间（北京时间，精确到秒）：2026-05-30 17:12:00 CST
#
# 修改记录：
# - 2026-05-30 17:12 Claude Sonnet 4.5: _summarize_login_status 扩展 SSO cookie 候选
#   清单（增加 lgc / dnk / lid / _tb_token_ / aui / sgcookie），让 CLI 输出能正确
#   反映淘宝当前版本的登录态判定依据。

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print

from core.handoff_snapshot import build_handoff_snapshot
from core.model_router import load_model_router
from shopping.app_service import ShoppingApplicationService
from shopping.artifact_inspector import list_artifacts, read_artifact_text
from shopping.diagnostics import build_runtime_diagnostics
from shopping.selector_loader import export_default_selector_profile
from shopping.selector_manager import backup_selector_override, build_selector_override_diff, list_selector_override_backups, read_selector_override_backup, read_selector_override_text, reset_selector_override_to_default, restore_selector_override_backup, validate_selector_override, write_selector_override_text
from shopping.factory import build_shopping_runtime_bundle
from shopping.intent_builder import ConsultationContext, ShoppingIntentBuilder
from shopping.playwright_executor import TaobaoPlaywrightExecutor
from shopping.preflight import run_phase1_preflight
from shopping.replay_executor import ReplayShoppingExecutor
from shopping.schemas import ListingProduct, ProductComparisonSummary, ShoppingSearchIntent

app = typer.Typer(help="Phase 1 淘宝购物主链路命令行工具。")


class _ReplaySummaryService:
    """回放演示用假总结服务。"""

    def summarize(self, *, intent: ShoppingSearchIntent, products):
        recommended = products[0].title if products else "无候选商品"
        return ProductComparisonSummary(
            recommended_option=recommended,
            reason_summary=f"回放模式：基于场景“{intent.scene}”优先推荐首个候选。",
            risk_points=["回放模式不代表真实淘宝抓取结果"],
            search_refinement=["进入真实抓取前请先完成淘宝登录态配置"],
        )


def _build_replay_service(root: Path, config_path: str | Path) -> tuple[ShoppingApplicationService, ConsultationContext, int]:
    """构建回放服务。"""

    runtime_bundle = build_shopping_runtime_bundle(root, config_path)
    replay_service = ShoppingApplicationService(
        executor=ReplayShoppingExecutor(root / "tests" / "fixtures"),
        cache_store=runtime_bundle.cache_store,
        summary_service=_ReplaySummaryService(),
        field_normalizer_service=None,
    )
    consultation_context = ConsultationContext(
        scene="高架低频卧室",
        budget=8000,
        noise_source="traffic",
        frequency_profile="low",
        preferred_solution="replace_window",
        room_type="卧室",
        notes=["夜间搅拌车明显", "优先看性价比"],
    )
    return replay_service, consultation_context, runtime_bundle.config.phase1.shopping.default_search_limit


def _build_live_service(root: Path, config_path: str | Path) -> tuple[ShoppingApplicationService, object]:
    """构建真实运行服务。"""

    runtime_bundle = build_shopping_runtime_bundle(root, config_path)
    live_service = ShoppingApplicationService(
        executor=TaobaoPlaywrightExecutor(runtime_bundle.config.phase1.shopping, root),
        cache_store=runtime_bundle.cache_store,
        summary_service=runtime_bundle.summary_service,
        field_normalizer_service=runtime_bundle.field_normalizer_service,
        anti_bot_policy=runtime_bundle.anti_bot_policy,
        review_enricher=runtime_bundle.review_enricher,
        review_top_n=runtime_bundle.config.phase1.shopping.reviews.top_n,
        enforce_delay=runtime_bundle.config.phase1.shopping.anti_bot.enforce_delay,
    )
    return live_service, runtime_bundle


@app.command("init-runtime")
def init_runtime(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """初始化 Phase 1 运行目录与 SQLite 缓存。"""

    root = Path(project_root).resolve()
    runtime_bundle = build_shopping_runtime_bundle(root, config_path)
    print(
        json.dumps(
            {
                "profile_root": str(runtime_bundle.profile_manager.profile_root),
                "artifact_root": str(runtime_bundle.profile_manager.artifact_root),
                "cache_db_path": str(runtime_bundle.profile_manager.cache_db_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


@app.command("preflight")
def preflight(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """执行 Phase 1 预检查。"""

    root = Path(project_root).resolve()
    runtime_bundle = build_shopping_runtime_bundle(root, config_path)
    result = run_phase1_preflight(root, runtime_bundle.config.phase1.shopping)
    print(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("show-selector-override")
def show_selector_override(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """显示当前 selector override 文件内容。"""

    root = Path(project_root).resolve()
    _live_service, bundle = _build_live_service(root, config_path)
    content = read_selector_override_text(bundle.project_root / bundle.config.phase1.shopping.selector_override_path)
    if content is None:
        raise typer.Exit(code=1)
    print(content)


@app.command("validate-selector-override")
def validate_selector_override_cmd(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """校验当前 selector override 文件。"""

    root = Path(project_root).resolve()
    _live_service, bundle = _build_live_service(root, config_path)
    result = validate_selector_override(bundle.project_root / bundle.config.phase1.shopping.selector_override_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("export-selector-template")
def export_selector_template(
    output_path: str = typer.Option("runtime/selector_overrides.yaml", help="导出路径"),
    project_root: str = ".",
) -> None:
    """导出默认选择器覆盖模板。"""

    root = Path(project_root).resolve()
    path = export_default_selector_profile(root / output_path)
    print(json.dumps({"output_path": str(path)}, ensure_ascii=False, indent=2))


@app.command("selector-status")
def selector_status(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """查看当前选择器覆盖文件与选择器摘要。"""

    root = Path(project_root).resolve()
    _live_service, bundle = _build_live_service(root, config_path)
    payload = build_runtime_diagnostics(
        profile_manager=bundle.profile_manager,
        cache_store=bundle.cache_store,
        artifact_limit=5,
        selector_override_path=bundle.project_root / bundle.config.phase1.shopping.selector_override_path,
        selector_profile=bundle.selector_profile,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("save-selector-override")
def save_selector_override(
    content_file: str = typer.Option(..., help="包含 selector override YAML 内容的文件路径"),
    backup_existing: bool = typer.Option(True, help="保存前是否先备份现有 override 文件"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """从文件保存 selector override。"""

    root = Path(project_root).resolve()
    _live_service, bundle = _build_live_service(root, config_path)
    selector_path = bundle.project_root / bundle.config.phase1.shopping.selector_override_path
    content = Path(content_file).read_text(encoding="utf-8")
    if backup_existing:
        from shopping.selector_manager import backup_selector_override
        backup_selector_override(selector_path)
    write_selector_override_text(selector_path, content)
    result = validate_selector_override(selector_path)
    print(json.dumps({"selector_path": str(selector_path), "validation": result}, ensure_ascii=False, indent=2))


@app.command("preview-selector-backup")
def preview_selector_backup(
    backup_name: str = typer.Option(..., help="备份文件名"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """预览某个 selector 备份文件。"""

    root = Path(project_root).resolve()
    _live_service, bundle = _build_live_service(root, config_path)
    selector_path = bundle.project_root / bundle.config.phase1.shopping.selector_override_path
    content = read_selector_override_backup(selector_path, backup_name)
    if content is None:
        raise typer.Exit(code=1)
    print(content)


@app.command("restore-selector-backup")
def restore_selector_backup(
    backup_name: str = typer.Option(..., help="备份文件名"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """从备份恢复 selector override 文件。"""

    root = Path(project_root).resolve()
    _live_service, bundle = _build_live_service(root, config_path)
    selector_path = bundle.project_root / bundle.config.phase1.shopping.selector_override_path
    restored = restore_selector_override_backup(selector_path, backup_name)
    if restored is None:
        raise typer.Exit(code=1)
    result = validate_selector_override(selector_path)
    print(json.dumps({"restored_path": str(restored), "validation": result}, ensure_ascii=False, indent=2))


@app.command("list-selector-backups")
def list_selector_backups(
    limit: int = typer.Option(20, help="最多显示多少个备份"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """列出 selector override 备份文件。"""

    root = Path(project_root).resolve()
    _live_service, bundle = _build_live_service(root, config_path)
    selector_path = bundle.project_root / bundle.config.phase1.shopping.selector_override_path
    items = list_selector_override_backups(selector_path, limit=limit)
    print(json.dumps(items, ensure_ascii=False, indent=2))


@app.command("reset-selector-override")
def reset_selector_override(
    backup_existing: bool = typer.Option(True, help="重置前是否备份现有 override"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """把当前 selector override 重置为默认模板。"""

    root = Path(project_root).resolve()
    _live_service, bundle = _build_live_service(root, config_path)
    selector_path = bundle.project_root / bundle.config.phase1.shopping.selector_override_path
    if backup_existing:
        backup_selector_override(selector_path)
    output = reset_selector_override_to_default(selector_path)
    validation = validate_selector_override(output)
    print(json.dumps({"output_path": str(output), "validation": validation}, ensure_ascii=False, indent=2))


@app.command("selector-diff")
def selector_diff(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """查看当前 override 相比默认配置的差异。"""

    root = Path(project_root).resolve()
    _live_service, bundle = _build_live_service(root, config_path)
    selector_path = bundle.project_root / bundle.config.phase1.shopping.selector_override_path
    result = build_selector_override_diff(selector_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("show-selector-profile")
def show_selector_profile() -> None:
    """显示当前淘宝选择器配置。"""

    from shopping.selector_profiles import TAOBAO_SELECTOR_PROFILE

    print(json.dumps(TAOBAO_SELECTOR_PROFILE.model_dump(), ensure_ascii=False, indent=2))


@app.command("handoff-snapshot")
def handoff_snapshot(
    artifact_limit: int = typer.Option(20, help="最多输出多少个最近产物"),
    project_root: str = ".",
) -> None:
    """输出当前可供下一个 Agent 接手的运行快照。"""

    root = Path(project_root).resolve()
    payload = build_handoff_snapshot(root, artifact_limit=artifact_limit)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("preview-intent")
def preview_intent(
    scene: str = typer.Option("高架低频卧室", help="用户场景摘要"),
    budget: int = typer.Option(8000, help="预算，单位元"),
    noise_source: str = typer.Option("traffic", help="traffic/rail/hvac/mixed/unknown"),
    frequency_profile: str = typer.Option("low", help="low/mid_high/full_band/unknown"),
    preferred_solution: str = typer.Option("replace_window", help="replace_window/add_inner_window/both_possible"),
) -> None:
    """预览从咨询上下文生成的购物意图。"""

    context = ConsultationContext(
        scene=scene,
        budget=budget,
        noise_source=noise_source,
        frequency_profile=frequency_profile,
        preferred_solution=preferred_solution,
        room_type="卧室",
    )
    intent = ShoppingIntentBuilder().build(context)
    print(json.dumps(intent.model_dump(), ensure_ascii=False, indent=2))


@app.command("replay-demo")
def replay_demo(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """使用本地 fixtures 运行一遍离线购物流程。"""

    root = Path(project_root).resolve()
    replay_service, consultation_context, limit = _build_replay_service(root, config_path)
    snapshot = replay_service.run_from_consultation_context(consultation_context, limit=limit)
    print(json.dumps(snapshot.model_dump(), ensure_ascii=False, indent=2))


@app.command("probe-search-query")
def probe_search_query(
    query: str = typer.Option(..., help="要探测的搜索词"),
    wait_after_load_ms: int = typer.Option(3000, help="页面加载后额外等待毫秒数"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """探测搜索页候选提取与选择器命中情况。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    payload = live_service.executor.probe_search_query(query, wait_after_load_ms=wait_after_load_ms)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("probe-full")
def probe_full(
    query: str = typer.Option(..., help="搜索词"),
    title: str = typer.Option(..., help="商品标题"),
    detail_url: str = typer.Option(..., help="商品详情页 URL"),
    wait_after_load_ms: int = typer.Option(3000, help="页面加载后额外等待毫秒数"),
    review_limit: int = typer.Option(10, help="评论探针最大样本数"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """对搜索页、详情页、评论区做一轮完整联调探针。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    payload = live_service.probe_full_candidate(
        query=query,
        title=title,
        detail_url=detail_url,
        wait_after_load_ms=wait_after_load_ms,
        review_limit=review_limit,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("probe-reviews")
def probe_reviews(
    title: str = typer.Option(..., help="商品标题"),
    detail_url: str = typer.Option(..., help="商品详情页 URL"),
    limit: int = typer.Option(10, help="最多抓多少条评论样本"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """对某个详情页执行评论探针。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    payload = live_service.probe_reviews_for_detail(title=title, detail_url=detail_url, limit=limit)
    if payload is None:
        raise typer.Exit(code=1)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("probe-detail-url")
def probe_detail_url(
    detail_url: str = typer.Option(..., help="要探测的详情页 URL"),
    wait_after_load_ms: int = typer.Option(3000, help="页面加载后额外等待毫秒数"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """探测详情页选择器命中情况和风险情况。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    payload = live_service.executor.probe_detail_url(detail_url, wait_after_load_ms=wait_after_load_ms)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("inspect-page-risk")
def inspect_page_risk(
    url: str = typer.Option(..., help="要检查的页面 URL"),
    wait_after_load_ms: int = typer.Option(3000, help="页面加载后额外等待毫秒数"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """打开指定页面并输出风险识别结果。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    result = live_service.executor.inspect_page_risk(url=url, wait_after_load_ms=wait_after_load_ms)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _summarize_login_status(status: dict) -> str:
    """把登录态判定结果整理成人类一眼可见的摘要。

    2026-05-30 第五次更新：扩展 SSO cookie 候选清单。
    淘宝当前版本（2025+）SSO cookie 不再用 _nk_/unb，主要靠 tracknick/lgc/_tb_token_。
    """

    is_logged_in = status.get("is_logged_in", False)
    confidence = status.get("confidence", "unknown")
    signals = status.get("signals") or []
    cookie_keys = status.get("cookie_keys") or []
    # 列出 cookie 候选中实际命中的，比单独列 _nk_/unb 信息量更大
    sso_nick_candidates = {"tracknick", "_nk_", "lgc", "dnk", "lid"}
    sso_token_candidates = {"_tb_token_", "unb", "aui", "sgcookie"}
    hit_nick = [k for k in cookie_keys if k in sso_nick_candidates]
    hit_token = [k for k in cookie_keys if k in sso_token_candidates]
    label = "✅ 已登录" if is_logged_in else "❌ 未登录"
    return (
        f"{label}（confidence={confidence}）\n"
        f"  - 命中信号：{', '.join(signals) if signals else '无'}\n"
        f"  - 昵称类 SSO Cookie：{', '.join(hit_nick) if hit_nick else '无'}\n"
        f"  - Token 类 SSO Cookie：{', '.join(hit_token) if hit_token else '无'}\n"
        f"  - 当前 URL：{status.get('url') or '(unknown)'}"
    )


@app.command("check-login")
def check_login(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """检查当前淘宝登录状态。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    result = live_service.executor.check_login_status()
    print(_summarize_login_status(result))
    print("\n完整 JSON：")
    print(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("open-login-window")
def open_login_window(
    keep_open_seconds: int = typer.Option(240, help="保持窗口打开的秒数，供人工扫码登录"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """打开淘宝登录页（login.taobao.com）并保留窗口供人工扫码。

    流程（2026-05-30 第四次重写）：
    1. 先打开 https://www.taobao.com 拿到 before 快照；
    2. 若已登录则直接走"刷新 + 写 after"短路径；
    3. 否则跳到 https://login.taobao.com 让淘宝弹出二维码；
    4. 用户扫码登录后，淘宝会自动跳转，脚本通过轮询 URL 检测；
    5. 检测到跳转后显式 goto i.taobao.com/my_taobao 触发 sso Cookie 完整写入；
    6. 最后回到首页拿 after 快照。
    """

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    result = live_service.executor.open_login_window(keep_open_seconds=keep_open_seconds)
    flow = result.get("login_flow", "unknown")
    detected_at = result.get("login_detected_at_seconds")
    print(f"登录流程：{flow}")
    if detected_at is not None:
        print(f"在第 {detected_at} 秒检测到跳转出 login.taobao.com")
    print("\nafter 快照：")
    print(_summarize_login_status(result.get("after", {})))
    print("\n完整 JSON：")
    print(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("search-once")
def search_once(
    query: str = typer.Option(..., help="淘宝搜索词"),
    limit: int = typer.Option(5, help="最多返回几个候选商品"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """真实淘宝搜索一次，并输出列表页候选。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    products = live_service.search_once(query=query, limit=limit)
    print(json.dumps([item.model_dump() for item in products], ensure_ascii=False, indent=2))


@app.command("detail-once")
def detail_once(
    title: str = typer.Option(..., help="商品标题，用于构造临时 ListingProduct"),
    detail_url: str = typer.Option(..., help="商品详情页 URL"),
    price_text: str | None = typer.Option(None, help="可选：从列表页已知的价格文本"),
    shop_name: str | None = typer.Option(None, help="可选：从列表页已知的店铺名"),
    normalize_with_llm: bool = typer.Option(True, help="是否用字段补归纳模型补全详情字段"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """真实抓取一个详情页，并输出标准化详情结构。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    listing = ListingProduct(
        title=title,
        detail_url=detail_url,
        price_text=price_text,
        shop_name=shop_name,
    )
    detail = live_service.detail_once(listing, normalize_with_llm=normalize_with_llm)
    print(json.dumps(detail.model_dump(), ensure_ascii=False, indent=2))


@app.command("live-demo")
def live_demo(
    scene: str = typer.Option("高架低频卧室", help="用户场景摘要"),
    budget: int = typer.Option(8000, help="预算，单位元"),
    noise_source: str = typer.Option("traffic", help="traffic/rail/hvac/mixed/unknown"),
    frequency_profile: str = typer.Option("low", help="low/mid_high/full_band/unknown"),
    preferred_solution: str = typer.Option("replace_window", help="replace_window/add_inner_window/both_possible"),
    limit: int = typer.Option(5, help="抓取候选商品数量"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """跑一次真实购物工作流（会访问淘宝并调用本地模型做总结）。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    consultation_context = ConsultationContext(
        scene=scene,
        budget=budget,
        noise_source=noise_source,
        frequency_profile=frequency_profile,
        preferred_solution=preferred_solution,
        room_type="卧室",
    )
    snapshot = live_service.run_from_consultation_context(consultation_context, limit=limit)
    print(json.dumps(snapshot.model_dump(), ensure_ascii=False, indent=2))


@app.command("diagnostics")
def diagnostics(
    artifact_limit: int = typer.Option(20, help="最多显示多少个最近产物"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """输出运行时诊断信息。"""

    root = Path(project_root).resolve()
    _live_service, bundle = _build_live_service(root, config_path)
    payload = build_runtime_diagnostics(
        profile_manager=bundle.profile_manager,
        cache_store=bundle.cache_store,
        artifact_limit=artifact_limit,
        selector_override_path=bundle.project_root / bundle.config.phase1.shopping.selector_override_path,
        selector_profile=bundle.selector_profile,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("history-summary")
def history_summary(
    limit: int = typer.Option(20, help="统计最近多少次运行"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """查看最近若干次运行的总体摘要。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    summary = live_service.history_summary(limit=limit)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


@app.command("show-event-log")
def show_event_log(
    limit: int = typer.Option(20, help="最多显示多少条事件日志"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """查看最近的事件日志。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    events = live_service.recent_events(limit=limit)
    print(json.dumps(events, ensure_ascii=False, indent=2))


@app.command("show-event-stats")
def show_event_stats(
    within_seconds: int = typer.Option(3600, help="统计最近多少秒内的事件"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """查看最近一段时间的执行事件统计。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    stats = live_service.recent_event_stats(within_seconds=within_seconds)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


@app.command("show-run-artifacts")
def show_run_artifacts(
    run_id: str = typer.Option(..., help="运行 ID"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """查看某次运行关联的 artifact 文件。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    items = live_service.list_run_artifacts(run_id)
    print(json.dumps(items, ensure_ascii=False, indent=2))


@app.command("export-latest-archive")
def export_latest_archive(
    output_root: str = typer.Option("runtime/exports/archives", help="导出根目录"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """导出最近一次运行的 zip 档案。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    result = live_service.export_latest_archive(root / output_root)
    if result is None:
        raise typer.Exit(code=1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("export-run-archive")
def export_run_archive(
    run_id: str = typer.Option(..., help="运行 ID"),
    output_root: str = typer.Option("runtime/exports/archives", help="导出根目录"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """导出指定运行的 zip 档案。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    result = live_service.export_run_archive(run_id, root / output_root)
    if result is None:
        raise typer.Exit(code=1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("export-latest-bundle")
def export_latest_bundle(
    output_dir: str = typer.Option("runtime/exports/latest", help="导出目录"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """导出最近一次运行的完整 bundle。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    result = live_service.export_latest_bundle(root / output_dir)
    if result is None:
        raise typer.Exit(code=1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("export-run-bundle")
def export_run_bundle(
    run_id: str = typer.Option(..., help="运行 ID"),
    output_dir: str = typer.Option("runtime/exports/manual", help="导出目录"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """导出指定运行的完整 bundle。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    result = live_service.export_run_bundle(run_id, root / output_dir / run_id)
    if result is None:
        raise typer.Exit(code=1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("compare-runs")
def compare_runs_cmd(
    left_run_id: str = typer.Option(..., help="左侧运行 ID"),
    right_run_id: str = typer.Option(..., help="右侧运行 ID"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """比较两次运行的差异。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    payload = live_service.compare_history_runs(left_run_id, right_run_id)
    if payload is None:
        raise typer.Exit(code=1)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("compare-latest-runs")
def compare_latest_runs_cmd(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """比较最近两次运行的差异。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    payload = live_service.compare_latest_two_runs()
    if payload is None:
        raise typer.Exit(code=1)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("list-history")
def list_history(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """列出购物历史运行。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    print(json.dumps(live_service.list_history(), ensure_ascii=False, indent=2))


@app.command("show-history")
def show_history(run_id: str = typer.Option(..., help="运行 ID"), project_root: str = ".", config_path: str = "config.yaml") -> None:
    """查看某次购物历史详情。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    result = live_service.get_history(run_id)
    if result is None:
        raise typer.Exit(code=1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("analyze-run")
def analyze_run(
    run_id: str = typer.Option(..., help="运行 ID"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """分析某次历史运行并给出建议。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    payload = live_service.analyze_history_run(run_id)
    if payload is None:
        raise typer.Exit(code=1)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("analyze-latest-run")
def analyze_latest_run(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """分析最近一次历史运行。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    payload = live_service.analyze_latest_run()
    if payload is None:
        raise typer.Exit(code=1)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


@app.command("show-latest-history")
def show_latest_history(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """查看最近一次购物历史。"""

    root = Path(project_root).resolve()
    _live_service, bundle = _build_live_service(root, config_path)
    run_id = bundle.cache_store.latest_run_id()
    if run_id is None:
        raise typer.Exit(code=1)
    result = bundle.cache_store.get_run(run_id)
    if result is None:
        raise typer.Exit(code=1)
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


@app.command("list-artifacts")
def artifacts(
    prefix: str | None = typer.Option(None, help="按文件名前缀过滤，如 taobao_search_"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """列出调试产物文件。"""

    root = Path(project_root).resolve()
    bundle = build_shopping_runtime_bundle(root, config_path)
    items = list_artifacts(bundle.profile_manager.artifact_root, prefix=prefix)
    print(json.dumps(items, ensure_ascii=False, indent=2))


@app.command("show-artifact")
def show_artifact(
    name: str = typer.Option(..., help="产物文件名"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """显示某个文本产物内容。"""

    root = Path(project_root).resolve()
    bundle = build_shopping_runtime_bundle(root, config_path)
    content = read_artifact_text(bundle.profile_manager.artifact_root, name)
    if content is None:
        raise typer.Exit(code=1)
    print(content)


@app.command("export-latest-report")
def export_latest_report(
    output_path: str | None = typer.Option(None, help="可选：导出 Markdown 文件路径"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """导出最近一次购物历史的 Markdown 报告。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    report = live_service.build_latest_report()
    if report is None:
        raise typer.Exit(code=1)
    if output_path:
        path = Path(output_path)
        path.write_text(report, encoding="utf-8")
        print(f"已导出：{path}")
        return
    print(report)


@app.command("export-history-report")
def export_history_report(
    run_id: str = typer.Option(..., help="运行 ID"),
    output_path: str | None = typer.Option(None, help="可选：导出 Markdown 文件路径"),
    project_root: str = ".",
    config_path: str = "config.yaml",
) -> None:
    """导出指定历史运行的 Markdown 报告。"""

    root = Path(project_root).resolve()
    live_service, _bundle = _build_live_service(root, config_path)
    report = live_service.build_history_report(run_id)
    if report is None:
        raise typer.Exit(code=1)
    if output_path:
        path = Path(output_path)
        path.write_text(report, encoding="utf-8")
        print(f"已导出：{path}")
        return
    print(report)


@app.command("show-router")
def show_router(project_root: str = ".") -> None:
    """显示当前最终模型路由。"""

    root = Path(project_root).resolve()
    router = load_model_router(root / "model_router.yaml")
    print(json.dumps(router.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()

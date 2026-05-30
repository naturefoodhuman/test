<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-28 22:55:19 CST
最后更新（北京时间，精确到秒）：2026-05-30 14:55:00 CST
-->

# 开发待办（Backlog）

> 阶段划分（2026-05-30 用户拍板后重排，依据 ADR-009 / ADR-012）：
> - **Phase 1A**：✅ 代码稳定化已完成，**等待用户在 Mac 上启动联调**。
> - **Phase 1B**（待启动）：咨询主链路补齐（A/B/E 专家 + F 协调员）。
> - **Phase 1C**（待启动）：咨询主链 ↔ 购物主链 整合闭环。
> - **V1.5**：知识库 / RAG / 视频管线。

---

## Phase 1A 收尾（代码稳定化）✅ 已完成

### P0：联调启动判据（ADR-008）— 全部满足

- [x] **P1 项 1**：把真实 `search-once` / `detail-once` / `live-demo` 真正变成 API 接口 → `src/api/app.py` 已有 `/api/shopping/search-once` / `/detail-once` / `/live-run`，并加了统一异常映射装饰器 `handle_shopping_errors` 与 OpenAPI tag 分组（system / intent / replay / live / probe / history / selectors / artifacts）。
- [x] **P1 项 2**：Markdown 报告 CLI / API / Web 统一导出 → 三处都走 `ShoppingApplicationService.build_history_report` / `build_latest_report`，底层都是 `ShoppingReportBuilder.build_markdown`。
- [x] **P1 项 3**：`anti_bot_policy.enforce_delay` 接入 `playwright_executor` 节流点 → 已在 `_paced_wait` 中调用 `compute_polite_delay`，并在 `search` / `fetch_detail` / `check_login_status` / `open_login_window` 上接入；dry-run 测试 `test_enforce_delay_triggers_wait_for_timeout` 验证。
- [x] **P1 项 4**：`risk_detection` 接入执行器中断分支 → `_assert_page_safe` 在 `search` / `fetch_detail` 主链路调用，命中风险时抛 `ShoppingRiskDetectedError`；dry-run 测试 `test_search_aborts_on_risk_signal` / `test_fetch_detail_aborts_on_risk_signal` 验证。
- [x] **P1 项 5**：`playwright_executor` dry-run 端到端测试 → `tests/test_playwright_executor_dry.py`（10 项测试）：覆盖搜索、回退选择器、风险中断、详情抽取、探针、节流、登录态。
- [x] **P1 项 6**：`docs/phase1_real_test_checklist.md` 打磨 → 扩成 10 节版本：环境准备 / 登录态 / 探针先行 / 真实搜索 / 真实详情 / 真实完整链路 / 风控处理 / artifact 回传 / 补丁应用 / 联调通过判据。
- [x] **P1 项 7**：`scripts/make_patch.py` 与补丁机制（ADR-013）→ 已上轮实装。

### P0.5：联调首轮进度（2026-05-30 第五次更新）

- [x] 用户：`pip3 install playwright && python -m playwright install chromium` ✅
- [x] 用户：`uv run python src/phase1_cli.py open-login-window --keep-open-seconds 240`，扫码登录 ✅ **已登录成功**（2026-05-30 第二次回传 artifact 显示 `is_logged_in: true`，cookie 含 tracknick / lgc / dnk / _tb_token_ 等 SSO cookie）
- [ ] 用户：跑探针 `probe-search-query` / `probe-detail-url` ← **下一步**
- [ ] 用户：跑真实 `search-once` / `detail-once` / `live-demo`
- [ ] 用户：把 `runtime/artifacts/<run_id>/` 与终端输出回传 Agent
- [ ] Agent：根据真实页面修正 `selector_profiles.py` / `extraction_utils.py` / `filtering.py`
- [x] Agent：每次修正打包 zip 补丁（ADR-013）✅ 已建立流程

> **当前状态**：用户已登录成功。第五次补丁修了两个 UX bug（登录态判定 signals 混淆 + CLI 摘要 cookie 候选不全）+ 加了 reload 重试 + 新增 `.gitignore` + 升级文件头规范。下一步推进**探针阶段**。

### P0.5：联调首轮（需用户在 Mac 上配合）

- [ ] 用户：`pip3 install playwright && python -m playwright install chromium`
- [ ] 用户：`uv run python src/phase1_cli.py open-login-window --keep-open-seconds 240`，扫码登录
- [ ] 用户：`uv run python src/phase1_cli.py search-once --query "隔音窗 夹胶中空 系统窗 性价比"`
- [ ] 用户：把 `runtime/artifacts/<run_id>/` 与终端输出回传 Agent
- [ ] Agent：根据真实页面修正 `selector_profiles.py` / `extraction_utils.py` / `filtering.py`
- [ ] Agent：每次修正打包 zip 补丁（ADR-013）

---

## Phase 1B 待启动（咨询主链路补齐，ADR-009）

> **前置依赖**：Phase 1A 联调通过且选择器在真页上稳定。

### P1B-1：基础设施
- [ ] 抽象基类 `src/experts/base.py: BaseExpert`（统一输入 / 输出 schema / 异常 / 重试）。
- [ ] 新增模块目录：`src/experts/` `src/coordinator/`。
- [ ] 槽位 schema：`src/coordinator/slots.py`（噪音类型 / 时段 / 房间 / 楼层 / 预算 / 窗户尺寸 / 特殊需求）。

### P1B-2：F 协调员状态机
- [ ] `src/coordinator/state_machine.py`：IDLE → 意图分析 → (追问 | 调度 | 快捷) → 等待 → 整合。
- [ ] 并行调度策略：A+B 并行（B 等 A 结果时串行）。
- [ ] 异常处理：格式错误自动重试一次 / 超时通知用户 / 失败降级为纯 prompt。

### P1B-3：A 噪音分析专家
- [ ] `src/experts/noise_analyst.py`：纯 prompt，输出 JSON（噪音类型 / 频率 / 声压级 / 建议隔声量 dB）。
- [ ] 评测复用 `eval_cases/noise_analysis_cases.json`。

### P1B-4：B 材料顾问专家（先纯 prompt，RAG 推到 V1.5）
- [ ] `src/experts/material_advisor.py`：输入 A 输出 + 用户预算 + 楼层，输出 JSON（玻璃结构 / 型材 / 密封方案 / 预期降噪 / 推理过程）。

### P1B-5：E 施工验收专家
- [ ] `src/experts/installation_guide.py`：纯 prompt，输出 JSON（准备清单 / 步骤 / 验收 / 坑点）。

### P1B-6：测试与文档
- [ ] 每个专家至少 3 个单元测试用例。
- [ ] 更新 V1 需求文档 md / docx：把 §4.1 / §4.2 / §4.3 / §4.5 的"V1 实际实现现状"段从 ⛔ 升级到 ✅。

---

## Phase 1C 待启动（整合闭环）

- [ ] B 专家输出 → `intent_builder` 直接消费（不再依赖手写 consultation context）。
- [ ] CLI 增加 `full-mode` 命令：用户用自然语言描述噪音 → A/B 并行 → B 结果 → D 购物 → 报告。
- [ ] API 增加 `/v1/full-mode` 端点。

---

## V1.5 待启动（ADR-012，知识库 / RAG / 视频管线）

> **前置依赖**：V1（Phase 1A + 1B + 1C）全部交付。

### V1.5-1：知识库基础
- [ ] 选型：ChromaDB（默认） / FAISS（fallback）。
- [ ] `src/knowledge/store.py`：抽象存储接口。
- [ ] `src/knowledge/document.py: KnowledgeDocument`（来源 / 质量分 / 多维度评分 / 标签）。
- [ ] 嵌入封装：`src/knowledge/embeddings.py`（`qwen3-embedding:8b` + `bge-m3:latest` fallback）。

### V1.5-2：质量评分插件化
- [ ] `src/knowledge/scoring/base.py`：评分接口。
- [ ] 六维度评分实现：权威 / 专业 / 时效 / 社区可信 / 信息密度 / 重复度。

### V1.5-3：手动入库 10~20 篇
- [ ] `knowledge_base/`：建立资料目录。
- [ ] watchdog 监控 + 热加载。

### V1.5-4：B 专家 RAG 化
- [ ] `src/experts/material_advisor.py` 升级：检索 → 拼接上下文 → LLM → 输出附 `knowledge_sources` 字段。
- [ ] `knowledge_references` 表（按原 V1 §5.2）。

### V1.5-5：视频管线（最低优先）
- [ ] 字幕下载（you-get / yt-dlp）。
- [ ] Whisper.cpp 离线转写（无字幕兜底）。
- [ ] LLM 摘要 + 自动评分 → 人工审核 → 切片入库。

---

## V2+ 已明确推迟项

- 看板暗黑模式 / 卡片浮层
- WebSocket 流式更新 / 专家健康监控
- 拼多多主链
- 加购 / 收藏 / 下单 / 付款（永久不做，V1+V1.5 禁区）
- Spectroid 图片识别
- 纯 AI 浏览器代理主链
- 商业模型自动 escalation（ADR-011：仅用户主动触发）

---

## 文档维护（持续）

- [ ] 每轮收尾按 `ONBOARDING_CHECKLIST.md` 第 6 步操作。
- [ ] V1 需求文档 md/docx 仅在 ADR-010 列出的 4 种情况下同步。
- [ ] 实机测试开始后，每轮改动必须打 zip 补丁（ADR-013）。

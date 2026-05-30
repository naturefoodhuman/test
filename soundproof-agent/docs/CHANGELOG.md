<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-30 11:50:00 CST
-->

# 变更日志（CHANGELOG）

> 用途：按"轮次（每次会话）"记录代码、文档、决策变更。
> 接手 Agent 只看本文件即可知道最近发生了什么；细节再去 `AGENT_HANDOFF.md` / `CURRENT_STATE.md`。
> 写入顺序：**最新在最上**。

约定：
- 一轮 = 一次完整的 Agent 会话；意外中止后由新 Agent 继续，算新一轮。
- 每轮条目至少包含：日期、Agent 名、动机、改了什么、测试状态、对项目需求文档（V1 docx）的影响。

---

## 2026-05-30（第三次）— Arena.ai Agent Mode（Phase 1A 收尾轮）

### 动机
用户指令"请继续推进开发"。按 BACKLOG.md Phase 1A 收尾推进，目标是凑齐 ADR-008 4 项联调启动判据后通知用户开始联调。

### 改了什么
- **新增 `tests/test_playwright_executor_dry.py`**（10 项 dry-run 测试，覆盖：搜索抽取、回退选择器、风险中断、详情抽取、详情风险中断、搜索/详情探针 payload 形状、`used_fallback` 标记、enforce_delay 节流、登录态检查）。这是 ADR-008 第 3 项判据的核心证据。
- **新增 `tests/test_api_app.py`**（12 项 FastAPI 测试，覆盖：health、handoff、preflight、intent preview、replay 端到端、history 接口族、404 映射、artifact 缺失、selector default yaml、OpenAPI tags、异常映射 RuntimeError→503、ValueError→400）。
- **重构 `src/api/app.py`**：
  - 新增 `handle_shopping_errors` 装饰器，把 `ShoppingRiskDetectedError`→409、`ShoppingExecutionError`→400、`RuntimeError`→503、`ValueError`→400、其他→500 统一映射，error response 都带 `error_type` 字段；
  - 给每个 endpoint 加 `tags=[...]` 与 `summary=...`；
  - 注册 8 个 `openapi_tags` 分组：`system` / `shopping/intent` / `shopping/replay` / `shopping/live` / `shopping/probe` / `shopping/history` / `shopping/selectors` / `shopping/artifacts`。
- **重写 `docs/phase1_real_test_checklist.md`** 为"用户照做即可"10 节版：环境准备 / 登录态 / 探针先行 / 真实搜索 / 真实详情 / 真实完整链路 / 风控处理 / artifact 回传 / 补丁应用 / 联调成功判据。明确告诉用户什么时候停步回传给 Agent。
- **更新 `docs/BACKLOG.md`**：Phase 1A 7 项全部勾选 ✅；P0.5 联调首轮清单明确"需要用户在 Mac 上配合"；底部加联调通知。

### 测试状态
- `PYTHONPATH=src python3 -m unittest discover -s tests` → **91 项全部通过**（69 → 91，本轮新增 22 项）。
- API 测试在临时项目根下端到端跑通 `/api/shopping/replay-run` → `/api/shopping/runs/latest/report`，验证 CLI/API/Web 三处报告统一函数。

### 对 V1 项目需求文档的影响
- 不触发 ADR-010 同步条件（属于"实现细节调整 + 测试增加"）。md / docx 不动。
- §4.4 D 购物参谋的实际现状从代码层面已通过 dry-run + API 测试，可信度大幅提升。

### ADR-008 联调启动判据达成情况
| 判据 | 状态 | 证据 |
|---|---|---|
| 1. P1 列表基本完成 | ✅ | API + 报告统一 + anti-bot 接入 + risk 接入，全部完成 |
| 2. 测试覆盖率不再下降，无失败 | ✅ | 91/91 通过，比上轮 +22 |
| 3. playwright_executor 在 mock 数据上端到端通过 | ✅ | `tests/test_playwright_executor_dry.py` 10 项全过 |
| 4. 联调清单打磨 | ✅ | `phase1_real_test_checklist.md` 已 10 节"用户照做即可" |

**结论：可以通知用户启动真实淘宝联调（OQ-001 流程）**。详细步骤见 `docs/phase1_real_test_checklist.md`。

### 给下一位 Agent / 用户的下一步
1. **用户在 Mac 上跑联调** —— 按 `phase1_real_test_checklist.md` 从第 1 步开始。
2. **Agent 下轮主要工作** ——
   - 如果用户已经跑了联调并回传了 artifact，按真页结果修选择器（最高杠杆）；
   - 修完每次都打 zip 补丁（ADR-013），文件清单含 `selector_profiles.py` / `extraction_utils.py` / `filtering.py` 等；
   - 联调稳定后启动 Phase 1B（咨询主链路 A/B/E + F 协调员）。
3. 如果用户暂时还未启动联调，Agent 可以提前做：
   - 评论真实抓取在 mock 数据上 dry-run（补一组 review_fetcher 测试）；
   - Phase 1B 的 `BaseExpert` 接口骨架（不实装 prompt，只定型）；
   - Web 页面联调工具上加"应用补丁/上传 artifact"的辅助按钮（非必需）。

---

## 2026-05-30（第二次）— Arena.ai Agent Mode（用户决策落地轮）

### 动机
用户答复了 5 条开放问题（OQ-001 ~ OQ-005），并新增"实机测试期 zip 补丁交付机制"要求。

### 改了什么
- **新增 6 条 ADR**（DECISIONS.md ADR-008 ~ ADR-013）：
  - ADR-008 真实淘宝联调启动判据
  - ADR-009 V1 范围扩容：补齐咨询主链路（supersedes ADR-002）
  - ADR-010 V1 需求文档按需同步（partially supersedes ADR-006）
  - ADR-011 商业 escalation 仅手动触发
  - ADR-012 V1.5 范围（知识库 / RAG / 视频管线）
  - ADR-013 实机测试期 zip 补丁交付机制
- **5 条 OQ 全部关闭**：`OPEN_QUESTIONS.md` 移到"已关闭"段，含用户原话与落地动作。
- **`docs/BACKLOG.md` 重排**：Phase 1A 收尾 → 1B 待启动 → 1C 待启动 → V1.5 待启动 → V2+ 永久禁区。
- **V1 需求文档同步**（触发 ADR-010 第 (d) 种情况）：md 镜像把咨询专家章节从 ⛔/🚫 升级为 ⏳ (Phase 1B 计划中)；知识库章节升级为 ⏳ (V1.5)；§9 实施路线图按新阶段重排；docx 已用脚本同步。
- **新增 `scripts/make_patch.py`**：实机测试期补丁打包工具，支持 `--auto` / `--files` / `--since-commit` / `--dry-run`。
- **升级 `scripts/sync_v1_docx.py`**：清理逻辑改用"已知章节边界集合"，更稳健。
- **`docs/ONBOARDING_CHECKLIST.md`** 第 6 步按 ADR-010 / ADR-013 重写；新增第 8 步（实机测试期专属）。
- **`docs/AGENT_HANDOFF.md`**：新增第 12 节本轮记录；§11 强提示按 ADR-010 调整。
- **`docs/CURRENT_STATE.md`**：刷新当前阶段与本轮新增能力。

### 测试状态
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` → **69 项全部通过**（无代码模块改动，仅文档 + 脚本）。
- `sync_v1_docx.py` 验证：连续 3 跑幂等。
- `make_patch.py --dry-run --auto` 验证：自动收集 12 个改动文件，排除规则正确。

### 对 V1 项目需求文档的影响
- 触发了 ADR-010 第 (d) 种情况（V1 范围伸缩），md + docx 已同步：
  - §1.2 / §2.1 / §2.2 / §4.1 / §4.2 / §4.3 / §4.5 / §4.6 / §9 / §10：相关"V1 暂不做咨询专家 / 知识库"的标注从 ⛔/🚫 升级为 ⏳ (Phase 1B / V1.5 计划中)；
  - §7 模型路由的 escalation 描述更新为"仅手动触发"；
  - §9 实施路线图重排为 Phase 0 / 1A / 1B / 1C / V1.5 / V2+；
  - 新增 ADR 索引段（md 末尾）。

### 给下一位 Agent 的提示
1. 当前 OPEN_QUESTIONS.md 无未关闭项。
2. 下轮重点是 Phase 1A 收尾 7 项（BACKLOG.md P0）。
3. 实机测试一启动，每轮收尾必须 `python3 scripts/make_patch.py --auto --desc "..."` 打补丁。

---

## 2026-05-30 — Arena.ai Agent Mode（文档同步轮）

### 动机
用户要求把 `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.docx` 的内容与当前实际代码状态同步，并补齐"意外中止后另一个 Agent 能接手"所需的维护文档体系。

### 改了什么
- **新增** `docs/CHANGELOG.md`（本文件）：按轮次的变更日志。
- **新增** `docs/DECISIONS.md`：架构与选型决策日志（ADR 风格）。
- **新增** `docs/ONBOARDING_CHECKLIST.md`：接手 Agent 30 分钟上手清单。
- **新增** `docs/OPEN_QUESTIONS.md`：等待用户确认/决策的开放问题清单。
- **新增** `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.md`：docx 的 Markdown 镜像，后续以 md 为事实源，docx 定期同步。
- **更新** `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.docx`：在每节末尾追加 `【V1 实际实现现状（2026-05-30 同步）】` 子段，标注 已实现 / 部分实现 / 未实现 / V1 暂不做。
- **更新** `docs/AGENT_HANDOFF.md`：第 10 节追加本轮记录；第 4 节文档目录追加新增的 4 份维护文档。
- **更新** `docs/CURRENT_STATE.md`：刷新"当前最重要结论"中文档体系完整度状态。

### 测试状态
- 执行 `PYTHONPATH=src python3 -m unittest discover -s tests -v`：**69 项全部通过**（与上轮一致，无代码改动）。

### 对 V1 项目需求文档的影响
- 文档形态保留：原 docx 结构、章节顺序、正文一字不动。
- 每章追加"实际实现现状"段，覆盖以下关键差异：
  - **3.1 架构原则** 中"Claude Code 作为开发助手"已被推翻 → V1 实际实现：开发流程改由 **Arena.ai Agent Mode** 主导，不使用 Claude Code（依据 `model_router.yaml: routes.project_development`）。
  - **2.1 欢迎菜单** Slash Command / **2.2 完整工作流** / **2.3 看板暗黑模式** 等会话主链路功能 → V1 实际仅落地"购物子链路"。
  - **4.4 D 购物参谋** 的"加购/收藏/下单/付款" → 明确 **V1 暂不做**。
  - **4.6 知识库 / 4.7 看板** → V1 仅落地最小开发态 Web 页面，未做向量库、专家健康监控、暗黑模式。
  - **9. 实施路线图** 的 Phase 1~5 → V1 实际是"购物主链 MVP"先于知识库/施工/视频管线。
- 详细对照见 docx 各章追加段与本 md 镜像。

### 给下一位 Agent 的提示
1. 下一轮如果有任何代码 / 选择器 / 选型变更，必须同步更新：
   - `CHANGELOG.md`（追加本轮条目，最新在最上）
   - `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.md` 对应章节的"实际实现现状"段
   - `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.docx`（同步 md 改动）
   - `AGENT_HANDOFF.md` / `CURRENT_STATE.md` / `BACKLOG.md`（按需）
2. 若决策被推翻，请在 `DECISIONS.md` 追加新条目并标注被替换的旧条目编号。
3. 用户尚未答复的事项一律登记到 `OPEN_QUESTIONS.md`，不要凭空假设。

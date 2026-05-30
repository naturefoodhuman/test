<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-30 11:50:00 CST
-->

# 架构与选型决策日志（ADR）

> 用途：每一个"会反复影响后续开发"的关键决策都登记在此。
> 接手 Agent 在动手大改之前，先来此查阅理由，再决定是否颠覆。
> 格式参考 Architecture Decision Record，简化版。

> 状态字段含义：`accepted`（生效中）/ `superseded`（已被取代）/ `proposed`（待用户确认）。

---

## ADR-001 开发流程主导：使用 Arena.ai Agent Mode，不使用 Claude Code

- **日期**：2026-05-27（由 `model_router.yaml` 推断为定稿时间）
- **状态**：accepted
- **决策**：所有规划、开发、测试、文档由 Arena.ai Agent Mode 主导；Claude Code 不参与此项目。
- **理由**：
  - 在 Arena.ai Agent Mode 中使用统一的多模型路由（Claude / ChatGPT / Gemini / Grok / Qwen / Kimi 等）效率更高。
  - 与原 V1 项目需求文档 §3.1 "Claude Code 作为开发阶段代码生成助手" 直接冲突 → 推翻原文。
- **影响**：
  - V1 需求文档 §3.1 / §8.1 中所有 Claude Code 相关条目作废。
  - `model_router.yaml: routes.project_development.primary = arena-ai-agent-mode`。
- **回滚条件**：除非用户明确要求改回 Claude Code，否则不变。

---

## ADR-002 V1 范围切片：先做"购物子链路 MVP"

- **日期**：2026-05-27 ~ 2026-05-28
- **状态**：superseded by ADR-009（2026-05-30 由用户拍板将咨询主链路纳入 V1）
- **决策**：V1 范围限定为 **"咨询上下文 → 购物意图 → 搜索 → 详情提取 → 排序 → 对比总结 → Markdown 报告"** 一条链。
- **明确不做（V1）**：
  - 加购 / 收藏 / 下单 / 付款
  - Spectroid 图片识别
  - 拼多多主链并行开发
  - 纯 AI 浏览器代理主链（V1 用确定性 Playwright + 选择器）
  - 知识库 RAG（B 专家暂不做向量化）
  - 看板暗黑模式 / WebSocket 流式 / 专家健康监控
  - 视频处理管线（字幕 + Whisper + 自动评分）
- **理由**：
  - 用户原话："V1 暂不做加购/收藏/付款，只做到搜索 + 详情提取 + 决策建议"。
  - 购物链稳定性优先，避免炫技。
- **影响**：
  - V1 需求文档 §2 / §4.4 / §4.6 / §4.7 / §9 中相关条目标注为"V1 暂不做"或"V2+"。
  - 测试覆盖只覆盖购物子链路（69 项测试）。

---

## ADR-003 模型路由：本地优先，按角色分配三档模型

- **日期**：2026-05-27（Phase 0 评测后定稿）
- **状态**：accepted
- **决策**：
  - 协调员 / 噪音分析 / 方案顾问：`qwen3.6:35b-a3b-q8_0`
  - 购物推理 / 购物总结：`qwen3-coder-next:q4_K_M`
  - 字段补归纳 / 轻量 fallback：`qwen3:14b`
  - 嵌入：`qwen3-embedding:8b`（备用 `bge-m3:latest`）
  - 商业兜底：`deepseek-chat`（仅 escalation）
- **理由**：
  - Phase 0 两轮评测结论；详见 `docs/phase0_final_analysis.md`。
- **影响**：
  - 与原 V1 需求文档 §3.2 "qwen3:14b 担任 A/B/D/E 全部专家"不同，已升级为分档路由。
- **回滚条件**：若 `qwen3-coder-next:q4_K_M` 在真实购物总结上质量退化，回退到 `qwen3.6:35b-a3b-q8_0`。

---

## ADR-004 浏览器执行器：确定性 Playwright，AI 代理不做主链

- **日期**：2026-05-28
- **状态**：accepted
- **决策**：使用 Playwright + 选择器配置（含主选择器与回退选择器）作为购物主链浏览器执行器；LLM 仅做字段归纳与总结，不让 LLM 直接驱动浏览器。
- **理由**：
  - 淘宝反爬严格，AI 代理的不可控行为容易触发风控。
  - 选择器变动可通过 YAML override 快速修正，无需重训。
- **影响**：
  - `src/shopping/playwright_executor.py` 是当前最脆弱模块，但执行路径可预测。
  - `model_router.yaml: routes.shopping_executor.primary = deterministic_playwright`。

---

## ADR-005 反爬策略：慢、少、可中断、可人工接管

- **日期**：2026-05-28
- **状态**：accepted
- **决策**：
  - 每次运行限速（`config.yaml: phase1.shopping.anti_bot`）。
  - 检测验证码 / 访问受限页面 → 立即停链（`src/shopping/risk_detection.py`）。
  - 默认 headed 模式 + 登录态复用（`browser_profile_root`），不做无头硬撞。
  - 评论抓取是"Top 候选第二阶段增强"，不全量抓。
- **影响**：抓取成功率优先于吞吐率。

---

## ADR-006 文档体系：md 为事实源，docx 同步导出

- **日期**：2026-05-30（本轮）
- **状态**：partially superseded by ADR-010（同步频率由"每轮"改为"按需"）
- **决策**：项目需求文档以 `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.md` 为事实源，docx 同步更新。其他维护文档（CHANGELOG / DECISIONS / HANDOFF / CURRENT_STATE / BACKLOG / OPEN_QUESTIONS / ONBOARDING_CHECKLIST）保持 md。
- **理由**：
  - docx 在 Agent 工具链中读写不便，diff 不直观。
  - md 易 grep、易自动化、易跨工具协作。
- **影响**：
  - 用户最初要求只更新 docx，本决策做了扩展（已经用户在 2026-05-30 确认）。
  - 未来若 md 与 docx 不一致，以 md 为准。
  - 同步触发频率见 ADR-010。

---

## ADR-007 选择器配置中心化 + YAML override + 回退选择器

- **日期**：2026-05-28 ~ 2026-05-29
- **状态**：accepted
- **决策**：
  - 主选择器写在 `src/shopping/selector_profiles.py`。
  - 联调期通过 `runtime/selector_overrides.yaml` 热覆盖。
  - 主选择器失败时自动回退（探针结果标记 `used_fallback`）。
- **影响**：联调改选择器无需改代码、无需重启大量流程。

---

## ADR-008 真实淘宝联调启动判据

- **日期**：2026-05-30
- **状态**：accepted
- **来源**：OQ-001 用户答复（「在你觉得代码比较稳了的时候告诉我」）。
- **决策**：Agent 不再被动等用户开启联调；以下 4 项**同时满足**时，Agent 主动通知用户启动真实淘宝联调：
  1. P1 列表（API / Web / Markdown 报告统一导出 / anti-bot 真正接入执行链）基本完成。
  2. 测试覆盖率不再下降，且无未修复的失败用例。
  3. `playwright_executor` 在 `replay-demo` + 4 种探针的 mock 数据上端到端通过。
  4. `docs/phase1_real_test_checklist.md` 已经打磨到"用户照做即可产 artifact"的程度。
- **影响**：
  - 在 4 项满足前，Agent 不申请用户做联调；持续做"非联调项"。
  - 4 项满足后，Agent 在该轮 CHANGELOG 与回复中**明确标注**"建议启动真实联调"。
- **回滚条件**：若 4 项满足后联调首跑暴露大面积选择器问题 → 重新进入"代码稳定化"轮次，并降级 status 到 "联调挂起"。

---

## ADR-009 V1 范围扩容：补齐咨询主链路（A/B/E + 协调员）

- **日期**：2026-05-30
- **状态**：accepted（**supersedes ADR-002**）
- **来源**：OQ-002 用户答复（「V1 要补齐咨询主链路」）。
- **决策**：V1 范围从"仅购物子链路"扩展为：
  - **Phase 1A（当前进行中）**：淘宝购物主链路 MVP。
  - **Phase 1B（待启动，需 OQ-001 联调通过后开始）**：咨询主链路补齐——
    - F 协调员状态机（IDLE → 意图分析 → 追问/调度/快捷 → 等待 → 整合）；
    - A 噪音分析专家（纯 prompt）；
    - B 材料顾问专家（**先纯 prompt，不含 RAG**，RAG 在 V1.5 由 ADR-012 承接）；
    - E 施工验收专家（纯 prompt）；
    - 抽象基类 `BaseExpert` 落地（原 V1 §10）。
  - **Phase 1C（最后整合）**：把咨询主链路结果接入购物主链路（A/B 输出 → intent_builder 输入），形成原 V1 §2.2 完整方案模式的最小闭环。
- **模型路由**：按 ADR-003，A/B/E 与协调员统一用 `qwen3.6:35b-a3b-q8_0`（fallback `qwen3:14b`）。
- **明确不在 Phase 1B 做的**：
  - 看板暗黑模式 / WebSocket 流式 / 专家健康监控（V2+）；
  - RAG / 知识库（V1.5）；
  - 加购 / 收藏 / 下单 / 付款（永远在 V1 之外，沿用 ADR-002 的 V1 禁区清单）。
- **影响**：
  - V1 时间线延长；
  - 新增模块目录：`src/experts/`（A/B/E + 基类）、`src/coordinator/`（状态机）。
  - V1 需求文档 md / docx 的"实际实现现状"段相关章节需要从 ⛔/🚫 升级到 ⏳（计划中，Phase 1B）。

---

## ADR-010 V1 需求文档同步频率：按需，而非每轮

- **日期**：2026-05-30
- **状态**：accepted（**partially supersedes ADR-006**）
- **来源**：OQ-003 用户答复（「有需求/架构变化时才改」）。
- **决策**：md 镜像 `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.md` 和对应 docx **仅在以下情况才更新**：
  1. 用户提出新需求 / 删除需求 / 修改既有需求；
  2. 架构层面变化（新增/删除/边界改写）；
  3. 模型路由 / 选型决策变化；
  4. V1 范围伸缩（Phase 切片调整、ADR-009 这类）。
- **不触发同步的情况**（仅入 `CHANGELOG.md`）：
  - 实现细节调整 / 选择器修正 / 测试增加 / Bug 修复 / 文档微调。
- **影响**：
  - `ONBOARDING_CHECKLIST.md` 第 6 步、`AGENT_HANDOFF.md` §11"强提示"已对应调整。
  - 减少 docx 同步噪声，降低误改风险。

---

## ADR-011 商业模型 escalation：默认禁用，仅用户主动触发

- **日期**：2026-05-30
- **状态**：accepted
- **来源**：OQ-004 用户答复（「暂不启用，触发逻辑是我主动提出时」）。
- **决策**：
  - 保留 `model_router.yaml: escalation: deepseek-chat` 配置，但不实装任何自动触发逻辑。
  - 在 CLI / API 层预留 `--use-cloud-escalation` 开关（默认 false），用户主动传时才走商业 API。
  - **前置条件**：实装该开关前必须先做 `src/security/model_guard.py` 模块，强制剥离 Cookie / Token / PII / 完整商品链接 / 截图（沿用原 V1 §6.2 红线）。
- **影响**：
  - 当前阶段不引入商业 API key 管理。
  - 节省成本，避免数据出境合规风险。
  - 当用户主动要求"用 DeepSeek 重试这一步"时，Agent 才推进 model_guard 实装。

---

## ADR-012 V1.5 范围：知识库 + RAG + 视频处理管线

- **日期**：2026-05-30
- **状态**：accepted（待启动；前置依赖 V1 联调通过 + Phase 1B 完成）
- **来源**：OQ-005 用户答复（「进入 V1.5」）。
- **决策**：V1.5 单独立项，内容：
  - 向量库：ChromaDB / FAISS（选型在 V1.5 启动时定，倾向 ChromaDB——本地轻量、社区活跃）。
  - 嵌入模型：`qwen3-embedding:8b`（fallback `bge-m3:latest`，已在 model_router.yaml）。
  - 初期手动入库 10~20 篇 markdown（隔音窗国标 / 论文摘要 / 高赞社区帖）。
  - 文档质量评分：按原 V1 §4.6 六维度（权威 / 专业 / 时效 / 社区可信 / 信息密度 / 重复度），实现成插件化接口。
  - watchdog 监控知识库目录，文件变更后自动重建向量索引。
  - **B 材料顾问 RAG 化**：从 Phase 1B 的纯 prompt 升级为 RAG 增强；输出附知识源引用。
  - 视频管线（you-get/yt-dlp 字幕 / Whisper.cpp 转写 / LLM 摘要 / 自动评分 / 人工审核 / 切片入库）放 V1.5 末期，最低优先。
- **明确不在 V1.5 做的**：加购 / 收藏 / 下单 / 付款（永远 V1+V1.5 禁区）。
- **影响**：
  - 新增模块目录：`src/knowledge/`。
  - 新增 `knowledge_base/` 资料目录（已在原 V1 §8.2 设计中）。
- **回滚条件**：若 ChromaDB 在 macOS M1 上性能不可接受，回退到 FAISS。

---

## ADR-013 实机测试期补丁交付机制

- **日期**：2026-05-30
- **状态**：accepted
- **来源**：用户 2026-05-30 要求（「当我开始在 Mac 上实机测试时，以后修改项目文件后你都要在 workspace 打包一份 zip 格式的补丁供我下载」）。
- **决策**：
  - **触发时机**：从用户在 Mac 上首次实机测试（执行 `open-login-window` / `search-once` / `live-demo` 之一）起，**每轮**只要改了项目文件，就必须打包 zip 补丁。
  - **打包路径**：`patches/patch_<YYYYMMDD_HHMMSS>_<short_desc>.zip`，放在 workspace 根（`/home/user/test/patches/`）。
  - **打包内容**：本轮**实际有改动**的项目文件（不含运行时产物 `runtime/`、`__pycache__/`、`.git/`）。zip 内目录从 `soundproof-agent/` 开始，便于用户直接覆盖。
  - **每个补丁必须附带**：
    - `PATCH_NOTES.md`（zip 内）：列出本补丁包含哪些文件、解决什么问题、回滚方式、应用前置条件（如是否需要重装依赖）。
    - 在用户消息回复中明确给出 zip 路径和"覆盖到 `/Users/naturist/MusicProject/Shopping-Agent/soundproof-agent/`"的提示。
  - **打包工具**：`scripts/make_patch.py`（本轮新增）。
- **影响**：
  - 用户应用补丁路径固定：`/Users/naturist/MusicProject/Shopping-Agent/soundproof-agent/`。
  - 在用户尚未启动实机测试前，本机制不强制启用（但 Agent 可以已经开始为机制做准备）。
- **回滚**：用户保留 git；若补丁出问题，`git restore` 即可。

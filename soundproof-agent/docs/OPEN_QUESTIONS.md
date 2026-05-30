<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-30 11:50:00 CST
最后更新（北京时间，精确到秒）：2026-05-30 13:20:00 CST
-->

# 待用户确认的开放问题

> 用途：所有"需要用户拍板才能继续"的问题集中在此。
> 接手 Agent 看到这里的问题，**不要替用户做决定**；可以列出选项、写出影响，但等用户答复。
> 用户答复后，把该条目移到"已关闭"，并在 `DECISIONS.md` 追加对应 ADR。

> 状态：`open` / `answered` / `closed`。

---

## 当前未关闭（open）

（暂无。所有 V1 启动期关键问题均已由用户在 2026-05-30 答复，见下方"已关闭"。）

> 接手 Agent 注意：用户的每轮反馈中如果出现新的需求变更 / 范围调整 / 待澄清点，请在这里**新增 OQ-00X** 条目，**不要**自行假设。

---

## 已关闭（closed）

### OQ-001 真实淘宝联调何时启动？ — status: closed @ 2026-05-30

- **用户答复**：「在你觉得代码比较稳了的时候告诉我，就可以开始淘宝联调。」
- **落地动作**：
  - 由 Agent 在每轮收尾时评估"代码稳定度"，达到下面 4 项时主动通知用户启动联调：
    1. P1 列表（API / Web / Markdown 报告统一导出 / anti-bot 真正接入执行链）基本完成；
    2. 测试覆盖率不再下降，且无未修复的失败用例；
    3. `playwright_executor` 在 `replay-demo` / 4 种探针的 mock 数据上端到端通过；
    4. 已经把"真实联调清单"（`docs/phase1_real_test_checklist.md`）打磨完毕，用户跟着照做就能产出 artifact。
  - 在此之前，Agent 持续做"非联调项"工作。
- **关联**：写入 `DECISIONS.md` ADR-008。

### OQ-002 V1 是否要补齐咨询主链路？ — status: closed @ 2026-05-30

- **用户答复**：「V1 要补齐咨询主链路（A/B/E 专家 + 协调员）。」
- **落地动作**：
  - V1 范围扩容：在购物子链路稳定（OQ-001 联调通过）后，启动 **Phase 1B：咨询主链路补齐**。
  - 包括：F 协调员状态机（IDLE → 意图分析 → 追问/调度/快捷 → 等待 → 整合）、A 噪音分析专家、B 材料顾问专家（先纯 prompt，不含 RAG，RAG 推到 V1.5）、E 施工验收专家。
  - 模型路由按 ADR-003：协调员/噪音分析/方案顾问统一用 `qwen3.6:35b-a3b-q8_0`。
  - 由 ADR-002（V1 范围切片）做 superseded → 新 ADR-009 承接。
- **关联**：写入 `DECISIONS.md` ADR-009，并把 ADR-002 标 `superseded by ADR-009`。
- **新增 Backlog**：见 `BACKLOG.md` 新增 P1.5 / P2 段。

### OQ-003 项目需求文档 docx 的同步频率？ — status: closed @ 2026-05-30

- **用户答复**：「有需求/架构变化时才改。」
- **落地动作**：
  - md 镜像 `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.md`：**仅在出现以下任一情况时才动**——
    1. 用户提出新需求 / 删除需求 / 修改既有需求；
    2. 架构层面变化（新增模块、删除模块、模块边界改写）；
    3. 模型路由 / 选型决策变化；
    4. V1 范围伸缩（Phase 切片调整）。
  - 普通的"实现细节调整 / 选择器修正 / 测试增加"不再同步到该 docx，只进 `CHANGELOG.md`。
  - `scripts/sync_v1_docx.py` 仅在 md 改动时才跑。
  - `ONBOARDING_CHECKLIST.md` 第 6 步、`AGENT_HANDOFF.md` §11"强提示"已据此调整。
- **关联**：写入 `DECISIONS.md` ADR-010，覆写 ADR-006 的"每轮同步"为"按需同步"。

### OQ-004 商业模型 escalation 是否启用？ — status: closed @ 2026-05-30

- **用户答复**：「暂不启用，触发逻辑是我主动提出时。」
- **落地动作**：
  - 保持 `model_router.yaml` 中 `escalation: deepseek-chat` 配置存在但默认 `enabled: false`。
  - **不实装**任何"本地连续失败 N 次 → 自动 escalation"逻辑。
  - 在 API / CLI 层预留 `--use-cloud-escalation` 开关（false 默认），用户主动传时才走商业 API。
  - 实装前需先做 `model_guard` 模块（保留原 V1 §6.2 红线：剥离 Cookie / Token / PII / 完整商品链接）。
- **关联**：写入 `DECISIONS.md` ADR-011。

### OQ-005 知识库 / 视频管线 — status: closed @ 2026-05-30

- **用户答复**：「进入 V1.5。」
- **落地动作**：
  - V1 不做知识库 / RAG / 视频管线。
  - V1.5 单独立项，依赖：V1（含咨询主链路 + 联调通过）。
  - V1.5 范围：ChromaDB / FAISS 选型、嵌入用 `qwen3-embedding:8b`、初期手动入库 10~20 篇 markdown、文档质量评分插件化骨架、watchdog 热加载；视频管线（you-get/yt-dlp + Whisper）放 V1.5 末期，最低优先。
- **关联**：写入 `DECISIONS.md` ADR-012；`BACKLOG.md` 新增 V1.5 段。

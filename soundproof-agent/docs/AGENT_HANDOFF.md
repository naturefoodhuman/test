<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-29 17:30:00 CST
-->

# Agent Handoff 文档

> 目的：当当前会话意外中止，由另一个 Agent 接续开发时，能在最短时间内恢复上下文并继续推进。

## 1. 项目一句话说明

这是一个 **本地优先部署的隔音窗专家咨询与购物辅助系统**，当前重点是 **淘宝购物主链路 MVP**：

- 从咨询上下文生成购物意图
- 到淘宝搜索候选商品
- 抽取详情页信息
- 做商品排序与对比总结
- 输出可分享的 Markdown 报告

---

## 2. 当前开发阶段

### 当前阶段
- **Phase 1：淘宝购物主链路开发**

### Phase 0 已完成
- 已完成两轮模型评测
- 已定稿模型路由

### 当前模型路由
- 协调员 / 噪音分析 / 方案顾问：`qwen3.6:35b-a3b-q8_0`
- 购物推理 / 购物总结：`qwen3-coder-next:q4_K_M`
- 字段补归纳 / 轻量 fallback：`qwen3:14b`

---

## 3. 当前代码状态摘要

### 本轮新增/增强的能力（2026-05-29 本轮开发）

1. **探针分析增强**
   - 搜索页探针增加质量分析（广告比例、标题平均长度、价格覆盖率、价格区间）
   - 详情页探针增加字段优先级分析
   - 增加 quality_score 评分（0-1）
   - 增加 priority_fixes 优先级修复建议

2. **选择器回退逻辑增强**
   - 列表页：主选择器失败时自动回退到备选选择器
   - 详情页：标题/店铺名/价格/正文都有回退策略
   - 探针结果中标记 used_fallback 和 fallback_used

3. **提取工具函数增强**
   - 店铺名提取增加 body 文本正则回退
   - 价格提取增加多种格式支持和 body 回退
   - 正文提取增加最小长度要求和回退选择器

4. **测试覆盖补全**
   - 新增 17 项测试用例（总计 69 项，之前 52 项）
   - 覆盖探针分析、提取工具回退逻辑

### 已落地能力（累积）

1. **咨询上下文 → 购物意图**
2. **购物意图 → 搜索词**
3. **列表页候选过滤**
4. **详情页确定性字段提取**（含回退逻辑）
5. **LLM 字段补归纳**
6. **确定性排序**
7. **LLM 对比总结**
8. **SQLite 缓存**
9. **历史记录查询**
10. **Markdown 报告导出**
11. **评论规则审查骨架**
12. **评论增强链路（回放模式已接入，真实抓取器骨架已建）**
13. **反爬风险策略骨架**
14. **执行事件统计**
15. **页面风险识别（验证码/访问受限）**
16. **URL 白名单与危险路径拦截**
17. **详情页 URL 规范化**
18. **选择器配置中心化**
19. **选择器回退策略**
20. **handoff 运行快照导出**
21. **运行级 artifact 与 report 关联**
22. **搜索页探针 / 详情页探针**（含回退探测）
23. **CLI + API 骨架**
24. **淘宝 Playwright 执行器 MVP（未实机验证）**
25. **延时策略函数与可配置节流开关**
26. **探针分析增强**（质量分析、优先级修复建议）

### 当前最接近的里程碑

> **第一次真实淘宝联调**

---

## 4. 关键目录说明

### 核心运行目录
- `src/shopping/`：购物模块核心逻辑
- `src/core/`：模型路由、handoff 快照等核心基础设施
- `src/api/`：FastAPI 骨架
- `src/security/`：反爬、URL 风险、节流策略
- `src/phase1_cli.py`：当前最常用命令入口

### 文档目录
- `docs/phase1_progress.md`：Phase 1 当前进度
- `docs/phase1_real_test_checklist.md`：真实淘宝联调清单
- `docs/phase1_review_and_risk_plan.md`：评论与反爬策略
- `docs/SEARCH_PROBE_GUIDE.md`：搜索页探针说明
- `docs/DETAIL_PROBE_GUIDE.md`：详情页探针说明
- `docs/api_plan.md`：API 规划
- `docs/COMMUNITY_REFERENCE_POLICY.md`：社区参考强制原则
- `docs/COMMUNITY_WATCHLIST.md`：社区对标观察清单
- `docs/REAL_PAGE_NOTES.md`：真实页面联调记录
- `docs/SELECTOR_STRATEGY.md`：选择器策略说明
- `docs/ARCHITECTURE_MAP.md`：架构与模块映射
- `docs/RUNBOOK.md`：常用命令与运行手册
- `docs/BACKLOG.md`：按优先级排列的下一步任务
- `docs/CURRENT_STATE.md`：本轮最新状态快照
- `docs/CHANGELOG.md`：按轮次变更日志（最新在最上）
- `docs/DECISIONS.md`：架构与选型决策日志（ADR 风格）
- `docs/ONBOARDING_CHECKLIST.md`：接手 Agent 30 分钟上手清单
- `docs/OPEN_QUESTIONS.md`：等待用户拍板的开放问题清单
- `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.md`：项目需求文档 V1 的 md 镜像（事实源，docx 每轮同步导出）
- `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.docx`：项目需求文档 V1 的 docx 版（每轮由 `scripts/sync_v1_docx.py` 同步）

### 测试目录
- `tests/`：单元测试（69 项）
- `tests/fixtures/`：回放执行器与评论回放数据

---

## 5. 当前最重要的未完成项

### P0（最高优先级）
1. 在真实淘宝页面上验证 Playwright 执行器
2. 修正列表页候选提取脚本
3. 修正详情页标题/店铺/价格/正文提取
4. 验证登录态复用是否稳定
5. 把验证码 / 风控页识别真正接到执行器中断逻辑的真实分支验证里

### P1
1. 把真实 `search-once` / `detail-once` / `live-demo` 变成 API 接口后的稳定版
2. 让真实评论抓取进入第二阶段候选增强链路
3. 将 anti-bot policy 的节流真正接入执行链
4. 将 Markdown 报告从 CLI / API / Web 统一导出

### P2
1. Web 页面
2. 会话管理
3. 看板与流式更新

---

## 6. 当前明确不要做的事

V1 暂不做：

- 加购
- 收藏
- 下单
- 付款
- Spectroid 图片识别
- 拼多多主链并行开发
- 纯 AI 浏览器代理主链

---

## 7. 当前开发原则

1. **本地模型优先**
2. **购物链路优先稳定，不优先炫技**
3. **确定性浏览器执行优先，LLM 负责理解与归纳**
4. **评论只作为第二阶段增强，不先全量抓**
5. **反爬策略以保守、少量、可中断、可人工接管为原则**
6. **每轮开发都要更新 handoff 文档**
7. **每轮开发都应检查社区与官方最佳实践文档**
8. **选择器优先使用主选择器，失败时自动回退**
9. **探针分析给出具体优先级修复建议**

---

## 8. 新 Agent 接手时的建议动作顺序

### 第一步：快速理解状态
依次阅读：

1. `README.md`
2. `docs/CURRENT_STATE.md`
3. `docs/phase1_progress.md`
4. `docs/BACKLOG.md`

### 第二步：确认代码还能跑
执行：

```bash
pip3 install httpx pydantic pyyaml rich typer playwright
cd soundproof-agent
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

预期结果：69 项测试全部通过

### 第三步：看命令入口
优先看：

- `src/phase1_cli.py`
- `src/shopping/workflow.py`
- `src/shopping/playwright_executor.py`

### 第四步：如果进入真实联调
必须先看：

- `docs/phase1_real_test_checklist.md`
- `docs/phase1_review_and_risk_plan.md`
- `docs/REAL_PAGE_NOTES.md`
- `docs/SELECTOR_STRATEGY.md`
- `docs/SEARCH_PROBE_GUIDE.md`
- `docs/DETAIL_PROBE_GUIDE.md`

---

## 9. 当前最需要人类用户参与的节点

只有到下面这些节点，才需要用户配合：

1. 安装 Playwright 和 Chromium
2. 打开淘宝并人工扫码登录
3. 在本机执行真实 `search-once` / `detail-once` / `live-demo`
4. 提供真实 artifact / 报错 / 页面截图给 Agent 修复

在此之前，Agent 可继续独立开发。

---

## 10. 本轮开发记录（2026-05-29）

### 新增文件/修改
- `src/shopping/probe_analysis.py`：增强探针分析逻辑
- `src/shopping/extraction_utils.py`：增强提取工具回退逻辑
- `src/shopping/selector_profiles.py`：增加回退选择器配置
- `src/shopping/playwright_executor.py`：支持回退选择器
- `tests/test_probe_analysis.py`：新增 7 项测试
- `tests/test_extraction_utils.py`：新增 8 项测试
- `tests/test_factory.py`：修复路径问题
- `tests/test_handoff_snapshot.py`：修复路径问题
- `docs/AGENT_HANDOFF.md`：更新文档

### 测试状态
- 总计 69 项测试，全部通过
- 新增 17 项测试覆盖回退逻辑和探针分析

---

## 11. 本轮开发记录（2026-05-30 — 文档同步轮）

### 动机
用户要求：把 `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.docx` 与当前实际项目状态同步；以后每轮也同步；并补齐"意外中止后另一个 Agent 能接续"所需的维护文档。

### 新增文件
- `docs/CHANGELOG.md`：按轮次变更日志（最新在最上）。
- `docs/DECISIONS.md`：架构与选型决策日志（ADR 风格，7 条 ADR 初版）。
- `docs/ONBOARDING_CHECKLIST.md`：接手 Agent 30 分钟上手 6 步清单。
- `docs/OPEN_QUESTIONS.md`：5 个等待用户拍板的开放问题（OQ-001~OQ-005）。
- `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.md`：docx 的 Markdown 镜像（事实源）。
- `scripts/sync_v1_docx.py`：把 md 中"V1 实际实现现状"段同步进 docx 的脚本（幂等，可重复运行）。

### 修改文件
- `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.docx`：在 21 个章节锚点后追加"V1 实际实现现状（2026-05-30 同步）"段；原文一字未改。
- `docs/AGENT_HANDOFF.md`：第 4 节文档目录追加 6 份新文档；新增本第 11 节。
- `docs/CURRENT_STATE.md`：追加 2026-05-30 文档体系完整度状态。

### 测试状态
- 跑了一次 `PYTHONPATH=src python3 -m unittest discover -s tests -v`：**69 项全部通过**（无代码变更，与上轮一致）。
- docx 同步脚本验证：连跑两次幂等通过（第二次先清理旧块再插新块）。

### 给下一位 Agent 的强提示
1. 任何代码 / 选择器 / 选型变更，**收尾时必须**：
   - 在 `CHANGELOG.md` 顶部追加本轮条目；
   - 同步更新本文件最后一节、`CURRENT_STATE.md`、按需更新 `BACKLOG.md`。
2. V1 需求文档 md/docx 是**按需同步**（ADR-010），仅在以下 4 种情况触发：用户改需求 / 架构变化 / 模型路由变化 / V1 范围伸缩。触发时跑 `python3 scripts/sync_v1_docx.py`。
3. 想推翻已有决策？先去 `DECISIONS.md` 找对应 ADR，再新增 ADR-00X 并把旧 ADR 标 `superseded`。
4. 用户尚未答复的事项一律登记到 `OPEN_QUESTIONS.md`，**不要凭空假设**。
5. 沿用文件头部注释规范（"创建该文件的 LLM 大模型名称" + "创建时间（北京时间，精确到秒）"）。

---

## 12. 本轮开发记录（2026-05-30 第二次 — 用户决策落地轮）

### 动机
用户在本轮答复了 5 条开放问题（OQ-001 ~ OQ-005），并新增了"实机测试期 zip 补丁交付机制"要求。

### 落地动作
- **新增 6 条 ADR**：
  - ADR-008 真实淘宝联调启动判据（4 项自动通知判据）
  - ADR-009 V1 范围扩容补齐咨询主链路（supersedes ADR-002，新增 Phase 1B / 1C）
  - ADR-010 V1 需求文档按需同步（partially supersedes ADR-006）
  - ADR-011 商业 escalation 仅手动触发，前置依赖 model_guard 模块
  - ADR-012 V1.5 范围确定（知识库 / RAG / 视频管线 / B 专家 RAG 化）
  - ADR-013 实机测试期 zip 补丁交付机制
- **5 条 OQ 全部关闭**：移到 `OPEN_QUESTIONS.md` 的"已关闭"段，含每条用户原话与落地动作。
- **BACKLOG 重排**：按 Phase 1A 收尾 / 1B 待启动 / 1C 待启动 / V1.5 待启动 / V2+ 永久禁区。
- **V1 需求文档同步**（触发 ADR-010 第 (d) 种情况）：md 镜像把 §1.2 / §2.1 / §2.2 / §4.1 / §4.2 / §4.3 / §4.5 / §4.6 / §9 / §10 中"V1 暂不做咨询专家"的部分从 ⛔/🚫 升级为 ⏳，docx 同步完成。
- **新增 `scripts/make_patch.py`**：补丁打包脚本，支持 `--auto / --files / --since-commit`，幂等可重跑。
- **`sync_v1_docx.py` 升级**：清理逻辑改用"已知章节边界集合"，更稳健，幂等性已验证（连续 3 跑无误）。
- **ONBOARDING_CHECKLIST 第 6 步**：按 ADR-010 / ADR-013 重写，新增第 8 步（实机测试期专属）。

### 测试状态
- `PYTHONPATH=src python3 -m unittest discover -s tests -v` → **69 项全部通过**（无代码模块改动，仅文档 + 脚本）。
- `scripts/sync_v1_docx.py` 验证：连续 3 跑幂等。
- `scripts/make_patch.py --dry-run --auto` 验证：自动收集 12 个本轮改动文件，无排除目录污染。

### 给下一位 Agent 的下一步
1. **Phase 1A 收尾**优先级（按 BACKLOG.md）：API 真实接口 → 统一报告导出 → anti-bot 接入执行链 → risk_detection 接入中断 → playwright dry-run 测试 → 联调清单打磨。
2. 完成上述 5+ 项后，按 ADR-008 判断是否可以通知用户启动联调。
3. 实机测试一启动，每轮必须打 zip 补丁（ADR-013）。
4. 当前 OPEN_QUESTIONS.md 无未关闭项 — 等用户提出新需求时再登记。

---

## 13. 本轮开发记录（2026-05-30 第三次 — Phase 1A 收尾轮）

### 动机
用户指令"请继续推进开发"。目标是凑齐 ADR-008 4 项联调启动判据后通知用户启动联调。

### 落地动作
- **新增 dry-run 测试** `tests/test_playwright_executor_dry.py`：10 项测试，通过 monkey-patch `_open_context()` 注入 FakePage，覆盖 search / fetch_detail / probe_search_query / probe_detail_url / risk 中断 / 选择器回退 / enforce_delay / check_login_status。
- **新增 API 测试** `tests/test_api_app.py`：12 项 FastAPI TestClient 测试，包括 replay 端到端、history 接口族、404 映射、OpenAPI tags、异常装饰器（RuntimeError→503、ValueError→400）。
- **重构 `src/api/app.py`**：
  - 引入 `handle_shopping_errors` 装饰器，统一映射 `ShoppingRiskDetectedError`→409、`ShoppingExecutionError`→400、`RuntimeError`→503、`ValueError`→400、其他→500，error response 全部带 `error_type` 字段；
  - 给所有 endpoint 加 `tags=[...]` 与 `summary=...`；
  - 注册 8 个 `openapi_tags` 分组。
- **打磨 `docs/phase1_real_test_checklist.md`** 为"用户照做即可"10 节版本。
- **更新 `BACKLOG.md`** 把 Phase 1A 7 项全勾选；在底部标注"可以通知用户启动联调"。

### 测试状态
- **91 项全过**（69 → 91，本轮新增 22 项）。
- API 测试用临时项目根 + TestClient 跑通完整 replay 链路，再用 history 接口验证报告导出一致。

### ADR-008 判据全部满足
详见 `CHANGELOG.md` 本轮条目的表格。

### 给下一位 Agent / 用户的下一步
- 用户：按 `docs/phase1_real_test_checklist.md` 在 Mac 上启动联调，回传 artifact。
- Agent：根据真页 artifact 修选择器，每次修完打 zip 补丁（ADR-013）。
- 联调稳定后启动 Phase 1B（咨询主链路 A/B/E + F 协调员）。
- 如果用户暂不启动联调，Agent 可以提前做 review_fetcher dry-run 测试、Phase 1B `BaseExpert` 接口骨架等"非联调依赖"工作。
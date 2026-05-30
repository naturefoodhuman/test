<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-29 17:30:00 CST
-->

# 当前状态快照

> 这是给"下一位接手 Agent"看的最短摘要版文档。

## 当前阶段
- Phase 1：淘宝购物主链路开发

## 当前最重要结论
- 全局主模型：`qwen3.6:35b-a3b-q8_0`
- 购物推理 / 总结主模型：`qwen3-coder-next:q4_K_M`
- 轻量字段补归纳：`qwen3:14b`
- 开发流程：Arena.ai Agent Mode 主导，**不使用 Claude Code**（见 DECISIONS.md ADR-001）
- 文档事实源：md 优先，docx 每轮由 `scripts/sync_v1_docx.py` 同步（ADR-006）

## 当前最接近的里程碑
- 第一次真实淘宝联调

## 2026-05-30 用户决策落地（最新）

用户拍板了 5 条原 OQ，全部已落地：
- **OQ-001**：联调启动由 Agent 主动判断（ADR-008 4 项判据），不再被动等用户。
- **OQ-002**：V1 范围**扩容**——必须补齐 A/B/E 专家 + F 协调员（ADR-009，新增 Phase 1B / 1C）。
- **OQ-003**：V1 需求文档**按需同步**（ADR-010），而非每轮同步。
- **OQ-004**：商业 escalation 仅手动，前置依赖 `model_guard` 模块（ADR-011）。
- **OQ-005**：知识库 / RAG / 视频管线进入 V1.5（ADR-012）。
- **新增 ADR-013**：实机测试期 zip 补丁交付机制，`scripts/make_patch.py` 已实装。

## 当前 Phase 状态
- **Phase 1A（淘宝购物主链路 MVP）**：✅ **代码稳定化已完成**，等待用户在 Mac 上启动联调（OQ-001 P0.5）。
- **Phase 1B（咨询主链路）**：待启动，前置依赖 1A 联调通过。
- **Phase 1C（整合闭环）**：待启动，前置 1B 完成。
- **V1.5（知识库）**：待启动，前置 V1 全部交付。

## 当前测试状态
- **91 项测试全部通过**（69 → 79 → 91）。
- 新增覆盖：`tests/test_playwright_executor_dry.py`（10 项，mock playwright）+ `tests/test_api_app.py`（12 项，FastAPI 端到端）。

## ADR-008 联调启动判据全部满足
1. ✅ P1 列表基本完成（API / 报告统一 / anti-bot 接入 / risk 接入）。
2. ✅ 测试覆盖率不再下降（91/91，比上轮 +22）。
3. ✅ `playwright_executor` 在 mock 数据上端到端通过。
4. ✅ `phase1_real_test_checklist.md` 已 10 节"用户照做即可"。

→ **可以通知用户启动 OQ-001 真实联调流程**。

## 当前开放问题
- 无（5 条 OQ 全部关闭）。

## 文档体系完整度
- ✅ `CHANGELOG.md` / `DECISIONS.md` (13 条 ADR) / `ONBOARDING_CHECKLIST.md` (8 步) / `OPEN_QUESTIONS.md`
- ✅ V1 需求文档 md 镜像 + docx + `scripts/sync_v1_docx.py`（按 ADR-010 按需触发，本轮不触发）
- ✅ `scripts/make_patch.py`：补丁打包工具（按 ADR-013 实机测试期触发）
- ✅ `AGENT_HANDOFF.md` §11 / §12 / §13：3 轮记录与下一轮提示
- ✅ `phase1_real_test_checklist.md`：10 节用户照做即可的联调清单

## 本轮新增能力（2026-05-29）

1. **探针分析增强**
   - 搜索页：增加质量分析（广告比例、价格区间、标题长度分布）
   - 详情页：增加字段优先级分析、quality_score（0-1）
   - 增加 priority_fixes 优先级修复建议

2. **选择器回退逻辑**
   - 列表页：主选择器失败自动回退到备选选择器
   - 详情页：标题/店铺名/价格/正文都有回退策略
   - 探针结果标记 used_fallback 和 fallback_used

3. **提取工具函数增强**
   - 店铺名：增加 body 文本正则回退
   - 价格：增加多种格式支持和 body 回退
   - 正文：增加最小长度要求和回退选择器

## 当前最需要继续开发的模块
1. `src/shopping/playwright_executor.py`（真实淘宝联调）
2. `src/phase1_cli.py`
3. `src/api/app.py`
4. `src/web/routes.py`
5. `src/shopping/review_fetcher.py`

## 当前最需要修的潜在风险点
1. 列表页提取脚本可能无法适配真实淘宝页面（已增加回退）
2. 详情页正文提取可能不够稳定（已增加回退和多层策略）
3. 真实价格/店铺选择器可能需要回退方案（已实现）
4. 评论抓取虽然已有探针和抓取骨架，但真实评论区结构尚未验证
5. anti-bot 策略已进入工作流、事件统计、页面风险识别与 URL 防护，但还未真正接入 Playwright 节流与验证码中断逻辑的实机分支
6. 每轮都必须继续更新 handoff / community / current_state 文档

## 当前可以直接执行的关键命令
```bash
pip3 install httpx pydantic pyyaml rich typer playwright
PYTHONPATH=src python3 -m unittest discover -s tests -v
uv run python src/phase1_cli.py preflight
uv run python src/phase1_cli.py replay-demo
uv run python src/phase1_cli.py diagnostics
uv run python src/phase1_cli.py selector-status
uv run python src/phase1_cli.py handoff-snapshot
uv run python src/phase1_cli.py probe-search-query --query "隔音窗 夹胶中空 系统窗 性价比"
uv run python src/phase1_cli.py probe-detail-url --detail-url "https://item.taobao.com/item.htm?id=xxx"
uv run python src/phase1_cli.py probe-reviews --title "商品标题" --detail-url "https://item.taobao.com/item.htm?id=xxx"
uv run python src/phase1_cli.py probe-full --query "隔音窗 夹胶中空 系统窗 性价比" --title "商品标题" --detail-url "https://item.taobao.com/item.htm?id=xxx"
uv run python src/phase1_cli.py export-latest-bundle
uv run python src/phase1_cli.py export-latest-archive
```

## 当前测试状态
- 已通过 69 项测试（本轮新增 17 项）

## 当前用户尚未执行但后续必须做的动作
1. 安装 Playwright + Chromium（`pip3 install playwright && python -m playwright install chromium`）
2. 打开淘宝并人工扫码登录
3. 在本机执行真实 `search-once` / `detail-once` / `live-demo` / `probe-reviews` / `probe-full`
4. 把真实 artifact 数据回传给我来修正选择器
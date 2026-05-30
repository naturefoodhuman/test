<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-30 11:50:00 CST
-->

# 接手 Agent 30 分钟上手清单

> 目的：上一位 Agent 会话意外中止，你（新 Agent）从零开始接手，按这张清单顺着做，就能在 30 分钟内进入"可继续推进"的状态。
> 每一项做完打勾（在脑内 / 在回复里），不要跳步。

---

## 第 0 步：身份与原则（1 分钟）

- [ ] 我是 Arena.ai Agent Mode；用户是产品负责人；本项目的开发流程不依赖 Claude Code（见 `DECISIONS.md` ADR-001）。
- [ ] 本地优先；购物链路稳定优先于炫技；评论是"第二阶段增强"；反爬保守。

---

## 第 1 步：读 4 份"事实源"文档（10 分钟）

按顺序读，**不要跳**：

1. [ ] `docs/AGENT_HANDOFF.md` — 全局概览（最权威）
2. [ ] `docs/CURRENT_STATE.md` — 最短摘要
3. [ ] `docs/CHANGELOG.md` — 最近一轮发生了什么
4. [ ] `docs/BACKLOG.md` — 下一步要干什么（P0/P1/P2/P3）
5. [ ] `docs/OPEN_QUESTIONS.md` — 哪些事项还在等用户拍板

副读（按需）：
- `docs/DECISIONS.md` — 想推翻某个设计前必读
- `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.md` — 长期愿景 + V1 实际现状
- `docs/ARCHITECTURE_MAP.md` — 模块职责映射
- `docs/RUNBOOK.md` — 常用命令

---

## 第 2 步：确认代码还能跑（5 分钟）

```bash
cd soundproof-agent
pip3 install httpx pydantic pyyaml rich typer            # 最小依赖
# 可选：pip3 install playwright fastapi uvicorn jinja2  # phase1 / web 时再装
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

预期：
- [ ] **69 项测试全部通过**（截至 2026-05-30）。
- [ ] 若数字变了，去 `CHANGELOG.md` 最近一条确认是否本应如此；不一致就先修测试。

---

## 第 3 步：扫一遍当前最脆弱模块（5 分钟）

按脆弱度排序，**只看不改**：

1. [ ] `src/shopping/playwright_executor.py`（660 行；真实淘宝执行器，未实机验证）
2. [ ] `src/shopping/review_fetcher.py`（评论真实抓取骨架）
3. [ ] `src/shopping/filtering.py`（候选过滤规则，真页结果出来后大概率要调）
4. [ ] `src/shopping/selector_profiles.py`（主 / 回退选择器）

---

## 第 4 步：明确本轮要做什么（5 分钟）

按以下顺序判断：

1. [ ] 用户在本轮消息里有没有明确指令？有就照做。
2. [ ] 没有的话，看 `BACKLOG.md` 的 P0 列表，挑第一个还没做的。
3. [ ] 如果 P0 全部依赖"用户在本机做真实联调"才能推进，就转向 P1 中纯代码项（API 接口稳定化 / 报告导出统一）。
4. [ ] 不要自作主张做 P2 / P3。

---

## 第 5 步：动手前的最后两件事（4 分钟）

- [ ] 想推翻已有决策？先在 `DECISIONS.md` 找对应 ADR；若仍要推翻，新增 ADR-XXX 并标 superseded。
- [ ] 要问用户的事？写进 `OPEN_QUESTIONS.md`，不要凭空猜。

---

## 第 6 步：每一轮收尾必须做（每轮终末）

不论本轮做了什么，结束前都必须：

1. [ ] `docs/CHANGELOG.md`：在最上方追加本轮条目。
2. [ ] `docs/AGENT_HANDOFF.md` 最后一节之后：追加本轮记录小节。
3. [ ] `docs/CURRENT_STATE.md`：刷新"本轮新增能力""测试状态""下一步"。
4. [ ] **按需** 更新 V1 需求文档（ADR-010）——仅在以下 4 种情况触发：
   - (a) 用户提出新需求 / 删除需求 / 修改既有需求；
   - (b) 架构层面变化（新增 / 删除 / 边界改写）；
   - (c) 模型路由 / 选型决策变化；
   - (d) V1 范围伸缩（Phase 切片调整）。
   触发时同步两个文件：
   - `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.md`（事实源）
   - `docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.docx`：跑 `python3 scripts/sync_v1_docx.py` 自动同步。
   不触发时不用动这两个文件。
5. [ ] 用户答复了开放问题？把对应 OQ-XXX 从 `OPEN_QUESTIONS.md` 的"open"挪到"closed"，并在 `DECISIONS.md` 新增 ADR-XXX。用户提了新待澄清点？在 OQ 列表新增条目。
6. [ ] 跑一遍测试 (`PYTHONPATH=src python3 -m unittest discover -s tests -v`)，把"通过 N 项"写进文档。
7. [ ] 新文件/改文件头部加 `<!-- 创建该文件的LLM大模型名称 / 创建时间（北京时间，精确到秒） -->` 注释（沿用项目规范）。
8. [ ] **实机测试期专属**（ADR-013）：用户首次在 Mac 上执行 `open-login-window` 之后，每轮若改了项目文件，必须运行：
   ```bash
   python3 scripts/make_patch.py --auto --desc "本轮简短描述"
   ```
   生成 `patches/patch_*.zip`，并在回复中明确告诉用户：zip 路径 + 覆盖到 `/Users/naturist/MusicProject/Shopping-Agent/soundproof-agent/`。

---

## 常用入口速查

- 测试：`PYTHONPATH=src python3 -m unittest discover -s tests -v`
- CLI：`uv run python src/phase1_cli.py --help`
- 预检查：`uv run python src/phase1_cli.py preflight`
- 回放演示：`uv run python src/phase1_cli.py replay-demo`
- 探针：`probe-search-query` / `probe-detail-url` / `probe-reviews` / `probe-full`
- 真实抓取（需用户在本机登录后）：`search-once` / `detail-once` / `live-demo`
- 导出：`export-latest-report` / `export-latest-bundle` / `export-latest-archive`
- handoff 快照：`handoff-snapshot`

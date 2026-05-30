<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-28 21:13:05 CST
-->

# 隔音窗专家咨询与购物辅助系统

当前仓库处于 **Phase 1：淘宝购物主链路开发** 阶段。

## 当前阶段目标

先把下面这条链路打通：

1. 从咨询结果生成购物搜索意图
2. 生成淘宝搜索词
3. 抽取列表页商品
4. 抽取详情页商品信息
5. 生成商品对比总结

## 已完成阶段

### Phase 0：模型评测与路由确定

已完成两轮评测：

- Round 1：`qwen3.6:35b-a3b-q8_0` vs `qwen3:14b`
- Round 2：`qwen3-coder-next:q4_K_M`

### 当前模型路由结论

- 协调员 / 噪音分析 / 方案顾问：`qwen3.6:35b-a3b-q8_0`
- 购物推理 / 购物总结：`qwen3-coder-next:q4_K_M`
- 字段补归纳 / 轻量 fallback：`qwen3:14b`

## 重要说明

本项目开发流程已明确：

- **不使用 Claude Code**
- **由 Arena.ai Agent Mode 负责规划、开发、测试、文档**

## 当前已落地的 Phase 1 基础内容

- `src/main.py`
- `src/core/model_router.py`
- `src/security/anti_bot_policy.py`
- `src/shopping/factory.py`
- `src/shopping/app_service.py`
- `src/shopping/artifact_inspector.py`
- `src/shopping/filtering.py`
- `src/shopping/review_models.py`
- `src/shopping/review_pipeline.py`
- `src/shopping/schemas.py`
- `src/shopping/intent_builder.py`
- `src/shopping/keyword_builder.py`
- `src/shopping/price_utils.py`
- `src/shopping/ranking.py`
- `src/shopping/report_builder.py`
- `src/shopping/cache_models.py`
- `src/shopping/parser_rules.py`
- `src/shopping/executor_interface.py`
- `src/shopping/profile_manager.py`
- `src/shopping/preflight.py`
- `src/shopping/sqlite_cache.py`
- `src/shopping/replay_executor.py`
- `src/shopping/llm_services.py`
- `src/shopping/workflow.py`
- `src/shopping/playwright_executor.py`
- `src/api/app.py`
- `src/api/schemas.py`
- `src/phase1_cli.py`

## 当前测试状态

已通过基础单元测试：

- `test_anti_bot_policy.py`
- `test_app_service.py`
- `test_artifact_inspector.py`
- `test_cache_models.py`
- `test_filtering.py`
- `test_intent_builder.py`
- `test_keyword_builder.py`
- `test_model_router.py`
- `test_parser_rules.py`
- `test_phase1_preflight.py`
- `test_ranking.py`
- `test_replay_executor.py`
- `test_report_builder.py`
- `test_report_from_history.py`
- `test_review_pipeline.py`
- `test_sqlite_cache.py`
- `test_workflow.py`

## 推荐运行方式

### 安装基础依赖

```bash
cd soundproof-agent
uv sync
```

### 初始化 Phase 1 运行目录

```bash
uv run python src/phase1_cli.py init-runtime
```

### 执行 Phase 1 预检查

```bash
uv run python src/phase1_cli.py preflight
```

### 预览购物意图

```bash
uv run python src/phase1_cli.py preview-intent
```

### 跑离线回放演示

```bash
uv run python src/phase1_cli.py replay-demo
```

### 如需真实淘宝抓取（联调阶段）

先安装可选依赖：

```bash
uv sync --extra phase1
python -m playwright install chromium
```

然后可用：

```bash
uv run python src/phase1_cli.py check-login
uv run python src/phase1_cli.py open-login-window --keep-open-seconds 240
uv run python src/phase1_cli.py search-once --query "隔音窗 夹胶中空 系统窗 性价比"
uv run python src/phase1_cli.py live-demo
```

### 导出 Markdown 报告

```bash
uv run python src/phase1_cli.py export-latest-report
uv run python src/phase1_cli.py export-history-report --run-id run_xxx
```

### 如需启动 API 骨架（回放接口）

先安装：

```bash
uv sync --extra web
```

后续可通过 uvicorn 启动 `src/main.py` 暴露的 `app`。

## 联调说明

真实淘宝联调前，请查看：

- `docs/phase1_real_test_checklist.md`
- `docs/api_plan.md`
- `docs/phase1_review_and_risk_plan.md`

## 当前策略亮点

- 搜索前：先从咨询上下文生成购物意图
- 搜索后：先过滤明显不属于窗产品的噪声候选
- 详情后：先用确定性规则提取商品字段
- 总结前：先做一次确定性排序，把明显更适合的商品排前面
- 结果后：可导出 Markdown 报告用于分享和复盘
- 评论策略采用“两阶段”：先参数筛选，再对 Top 候选补抓评论并做有效评论识别
- 风控策略采用“慢、少、可中断、可人工接管”的保守模式
- 通过 app service、factory、api skeleton 把 CLI / API / 后续 Web 复用边界固定下来

## 下一步

- 第一次真实淘宝联调
- 根据真页结果修正列表页与详情页选择器
- 强化 detail 文本提取与价格/店铺识别
- 把评论抓取接入真实详情候选后的第二阶段链路
- 联调稳定后开始接 Web/API 层的真实抓取接口

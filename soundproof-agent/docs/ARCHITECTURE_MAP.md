<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-28 23:56:44 CST
-->

# 架构与模块映射

## 1. 总体数据流

当前 Phase 1 的购物主链数据流如下：

1. **咨询上下文**
2. **购物意图构建**
3. **搜索词构建**
4. **列表页抓取**
5. **候选过滤**
6. **详情页抓取**
7. **确定性字段提取**
8. **LLM 字段补归纳**
9. **第一次排序**
10. **评论增强**
11. **第二次排序**
12. **LLM 对比总结**
13. **SQLite 缓存**
14. **Markdown 报告导出**
15. **artifact / history / diagnostics / handoff**

---

## 2. 模块职责映射

### `src/shopping/intent_builder.py`
把咨询阶段的结构化上下文翻译成购物意图。

### `src/shopping/keyword_builder.py`
把购物意图翻译成搜索词。

### `src/shopping/filtering.py`
在进入详情页前过滤明显不是窗产品的候选。

### `src/shopping/parser_rules.py`
对详情页文本做第一轮确定性字段解析。

### `src/shopping/llm_services.py`
- `ShoppingFieldNormalizerService`：字段补归纳
- `ShoppingSummaryService`：商品对比总结

### `src/shopping/ranking.py`
在 LLM 总结前做一轮规则排序。

### `src/shopping/review_pipeline.py`
对评论做有效性判定与疑似刷评识别。

### `src/shopping/review_enricher.py`
把评论增强结果回写到 `ProductDetail`。

### `src/shopping/workflow.py`
把完整购物流程串起来，并记录 step traces。

### `src/shopping/sqlite_cache.py`
负责缓存运行结果、历史记录和执行事件。

### `src/shopping/report_builder.py`
生成 Markdown 报告。

### `src/shopping/playwright_executor.py`
真实淘宝页面抓取执行器 MVP。

### `src/shopping/replay_executor.py`
离线回放执行器，用于开发期联调与测试。

### `src/shopping/app_service.py`
给 CLI / API / Web 提供统一应用服务入口。

### `src/shopping/factory.py`
构建运行时依赖集合。

### `src/core/handoff_snapshot.py`
构建当前运行时的 handoff 快照。

### `src/api/app.py`
FastAPI 骨架。

### `src/phase1_cli.py`
当前最重要的命令入口。

---

## 3. 当前最脆弱的模块

### 第一名：`playwright_executor.py`
原因：
- 强依赖淘宝真实页面结构
- 还未实机联调
- 真实选择器稳定性未知

### 第二名：`review_fetcher.py`
原因：
- 真实评论区域结构尚未验证
- 真实抓取路径还未实机验证

### 第三名：`filtering.py`
原因：
- 当前规则主要靠经验先写
- 真页结果出来后很可能需要快速调整关键词表

---

## 4. 当前最稳的模块

### 稳定层
- `model_router.py`
- `intent_builder.py`
- `keyword_builder.py`
- `price_utils.py`
- `sqlite_cache.py`
- `report_builder.py`
- `handoff_snapshot.py`

这些模块后续大概率只做增量增强，不会大改。

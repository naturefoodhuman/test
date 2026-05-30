<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-27 16:13:50 CST
-->

# Phase 1 执行计划：淘宝购物主链路 MVP

## 1. Phase 1 目标

在不做加购、收藏、付款的前提下，先把下面这条链路打通：

> 搜索词生成 → 淘宝搜索 → 列表页抽取 → 详情页抽取 → 商品结构化 → 商品对比总结

## 2. 交付边界

### 必做

1. Playwright 浏览器执行器
2. 本地登录态 profile 复用
3. 列表页候选商品抽取
4. 详情页结构化字段抽取
5. 商品标准 schema
6. 商品对比摘要
7. 商品缓存落盘

### 暂不做

1. 加购
2. 收藏
3. 支付
4. 拼多多并行
5. Spectroid 图片识别

## 3. 开发顺序

### Step 1：商品 schema 固化
- 定义列表页商品 schema
- 定义详情页商品 schema
- 定义对比结果 schema

### Step 2：关键词构建器
- 从咨询结果生成搜索词
- 支持“性价比 / 高配 / 加内窗 / 整窗更换”几个模式

### Step 3：浏览器执行器 MVP
- 打开淘宝
- 输入搜索词
- 抽取前 N 个候选项
- 打开详情页

### Step 4：详情页解析
- 价格
- 店铺
- 规格
- 玻璃/型材/密封/五金关键词
- 包安装/测量/拆旧信息

### Step 5：总结层
- 把结构化字段喂给 LLM
- 输出推荐项 / 风险点 / 后续 refinement

## 4. 当前默认模型使用建议

- 协调与购物总结：qwen3.6:35b-a3b-q8_0
- 字段补归纳：qwen3:14b
- 待验证购物推理增强：qwen3-coder-next:q4_K_M

## 5. 下一批将落地的代码

1. `src/shopping/schemas.py`
2. `src/shopping/keyword_builder.py`
3. `src/shopping/cache_models.py`
4. `src/shopping/parser_rules.py`
5. `src/shopping/executor_interface.py`

<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-28 23:18:07 CST
-->

# API 规划（Phase 1 过渡版）

## 当前状态

项目已具备 API 骨架：

- `src/api/app.py`
- `src/api/schemas.py`
- `src/main.py`

当前 API 目标不是直接上线，而是为后续 Web 层接入提前稳定服务边界。

## 当前可提供的接口

### 健康检查
- `GET /health`

### 运行时 handoff 快照
- `GET /api/handoff`

### 运行时诊断
- `GET /api/diagnostics`

### 模型路由查看
- `GET /api/router`

### Phase 1 预检查
- `GET /api/preflight`

### 事件统计
- `GET /api/shopping/event-stats`

### 购物意图预览
- `GET /api/shopping/intent/preview`

### 离线购物回放
- `POST /api/shopping/replay-run`

### 真实搜索一次（实验接口）
- `POST /api/shopping/search-once`

### 真实抓取一个详情页（实验接口）
- `POST /api/shopping/detail-once`

### 真实完整购物流程（实验接口）
- `POST /api/shopping/live-run`

### 历史运行列表
- `GET /api/shopping/runs`

### 最近一次历史运行
- `GET /api/shopping/runs/latest`

### 历史运行详情
- `GET /api/shopping/runs/{run_id}`

### 最近一次 Markdown 报告
- `GET /api/shopping/runs/latest/report`

### 指定运行 Markdown 报告
- `GET /api/shopping/runs/{run_id}/report`

### 调试产物列表
- `GET /api/artifacts`

### 调试产物文本读取
- `GET /api/artifacts/{name}`

## 当前状态说明

### 已稳定接口

- 健康检查
- 路由查看
- 预检查
- replay-run
- runs / latest / report
- diagnostics / handoff / artifact 查询

### 实验接口

以下接口已接入，但仍待真实淘宝联调验证：

- `POST /api/shopping/search-once`
- `POST /api/shopping/detail-once`
- `POST /api/shopping/live-run`

这些接口已经具备服务边界，但需要真实淘宝页面联调后才能确认稳定性。

## 为什么现在先做这些接口

因为真实淘宝抓取还要经过：

1. Playwright 依赖安装
2. 本机 Chromium 安装
3. 淘宝登录态建立
4. 真页选择器验证

所以现阶段：

- 回放接口与历史接口用于先稳定 API 结构
- 真实接口先以“实验接口”身份接入，方便联调后直接修而不是从零扩展

## 后续扩展方向

### 下一步

- 基于真实联调修复 `search-once` / `detail-once` / `live-run`
- 将这些接口从“实验”推进为稳定接口

### 再下一步

- Web 页面
- 会话管理
- 看板更新
- WebSocket / SSE 推送

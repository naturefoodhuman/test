<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-29 14:40:06 CST
-->

# Web 界面计划（开发态）

## 当前状态

已具备开发态 Web 页面：

- 首页开发看板：`/`
- 运行详情页：`/runs/{run_id}`
- 运行分析页：`/runs/{run_id}/analysis`
- 最近运行分析页：`/runs/latest/analysis`
- Artifact 文本预览页：`/artifacts/{name}`
- Artifact Manifest 页：`/runs/{run_id}/artifacts`
- 最近运行快速跳转：`/runs/latest`
- 联调工具页：`/tools`
- 运行比较页：`/compare`、`/compare/latest`

## 当前作用

这不是正式产品页，而是为了：

1. 开发时可视化看最近运行
2. 快速触发 replay
3. 查看 Markdown 报告
4. 查看某次运行的详情与 artifact 列表
5. 查看 step traces 和 workflow notes
6. 在浏览器里快速打开某个 artifact 文本
7. 直接在页面里提交搜索页/详情页探针
8. 直接在页面里编辑和保存 selector override
9. 比较最近两次运行的差异
10. 查看某次运行的分析建议
11. 导出 ZIP 档案

## 已落地文件

- `src/web/routes.py`
- `src/web/templates/base.html`
- `src/web/templates/dashboard.html`
- `src/web/templates/run_detail.html`
- `src/web/templates/run_analysis.html`
- `src/web/templates/artifact_detail.html`
- `src/web/templates/artifact_manifest.html`
- `src/web/templates/tools.html`
- `src/web/templates/compare_runs.html`

## 下一步

### P1
- 在首页显示更多 step trace 摘要
- 在详情页显示 bundle 导出结果提示
- 在工具页增加导出 selector 模板按钮

### P2
- 增加真实联调辅助页
- 增加 diagnostics 可视化区块
- 增加事件日志详情页

### P3
- 与正式对话页、看板页合并

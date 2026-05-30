<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-28 21:29:23 CST
-->

# 运行手册（Runbook）

## 1. 安装基础依赖

```bash
cd soundproof-agent
uv sync
```

## 2. 运行测试

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## 3. 初始化运行目录

```bash
uv run python src/phase1_cli.py init-runtime
```

## 4. 执行预检查

```bash
uv run python src/phase1_cli.py preflight
```

## 5. 预览购物意图

```bash
uv run python src/phase1_cli.py preview-intent
```

## 6. 跑离线回放

```bash
uv run python src/phase1_cli.py replay-demo
```

## 7. 查看历史运行

```bash
uv run python src/phase1_cli.py list-history
uv run python src/phase1_cli.py show-latest-history
```

## 8. 导出 Markdown 报告

```bash
uv run python src/phase1_cli.py export-latest-report
uv run python src/phase1_cli.py export-history-report --run-id run_xxx
```

## 9. 真实淘宝联调前安装依赖

```bash
uv sync --extra phase1
python -m playwright install chromium
```

## 10. 真实淘宝联调命令

### 检查登录状态

```bash
uv run python src/phase1_cli.py check-login
```

### 打开登录窗口

```bash
uv run python src/phase1_cli.py open-login-window --keep-open-seconds 240
```

### 搜索一次

```bash
uv run python src/phase1_cli.py search-once --query "隔音窗 夹胶中空 系统窗 性价比"
```

### 抓一个详情页

```bash
uv run python src/phase1_cli.py detail-once --title "商品标题" --detail-url "详情页URL"
```

### 跑完整 live demo

```bash
uv run python src/phase1_cli.py live-demo
```

## 11. 查看 artifact

```bash
uv run python src/phase1_cli.py list-artifacts
uv run python src/phase1_cli.py show-artifact --name taobao_search_xxx.json
```

## 12. 启动 API 骨架

```bash
uv sync --extra web
uv run uvicorn src.main:app --reload --app-dir .
```

## 13. 文档同步（每轮收尾必做）

```bash
# 把 md 镜像里的"V1 实际实现现状"段同步到 docx（幂等，可重复跑）
pip3 install python-docx
python3 scripts/sync_v1_docx.py
```

写代码时若改了 md 里某节的"V1 实际实现现状"段，跑一次该脚本即可同步到 docx。
如果新增章节锚点，需先在 `scripts/sync_v1_docx.py` 的 `ANCHOR_BLOCKS` 里加一条 `(锚点段原文, [现状段文本列表])`。

<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-29 01:18:32 CST
-->

# 选择器覆盖指南

> 作用：真实淘宝联调时，如果页面结构变了，允许先通过 YAML 覆盖选择器，而不是马上改 Python 代码。

## 配置文件位置

默认路径：

```text
runtime/selector_overrides.yaml
```

也可以通过环境变量覆盖：

```bash
export SHOPPING_SELECTOR_OVERRIDE_PATH=runtime/selector_overrides.yaml
```

## 典型使用流程

### 1. 导出默认模板（后续可再补 CLI 命令）
当前代码已支持：
- `export_default_selector_profile(...)`

### 2. 修改某个区块
例如只改标题选择器：

```yaml
detail:
  title_selectors:
    - "h1.custom"
    - "[class*=newTitle]"
```

### 3. 重新运行探针

- `probe-search-query`
- `probe-detail-url`

看命中情况是否改善。

## 当前建议

- 联调时优先先改 YAML 覆盖
- 只有在覆盖模式已经验证有效后，再决定是否回写默认代码

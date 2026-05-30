<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-27 23:00:19 CST
最后更新（北京时间，精确到秒）：2026-05-30 14:20:00 CST
-->

# Phase 1 真实淘宝联调清单（用户照做即可产 artifact）

> 适用对象：用户（你）按本清单从头到尾跑一遍，把每一步产出的 artifact 回传给 Agent，Agent 据此修正选择器与逻辑。
> 设计原则：**先探针后真抓**——探针不依赖完整链路，能最快暴露选择器问题；真抓只在探针通过后才做。

---

## 0. 实机测试启动前的 Agent 端确认

Agent 在通知用户启动联调之前，必须满足 ADR-008 4 项判据。当前状态：

- ✅ Phase 1A 代码已通过 dry-run 测试（69 + 10 = **79 项**测试全过）
- ✅ `playwright_executor` 在 mock 数据上端到端通过（含 risk 中断、选择器回退、节流）
- ✅ Markdown 报告 CLI/API/Web 三处走统一函数
- 🟡 本清单已打磨为"用户照做即可"版本（本文件）

满足后 Agent 在 CHANGELOG / 用户回复中标注"建议启动真实淘宝联调"。

---

## 1. 环境准备（约 10 分钟）

> 全部命令在 macOS 上执行；当前默认项目路径 `/Users/naturist/MusicProject/Shopping-Agent/soundproof-agent`。

### 1.1 安装依赖

```bash
cd /Users/naturist/MusicProject/Shopping-Agent/soundproof-agent
uv sync --extra phase1
uv run python -m playwright install chromium
```

> 国内网络如果 Chromium 下载慢，可设置镜像：
> `export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright`

### 1.2 初始化运行目录

```bash
uv run python src/phase1_cli.py init-runtime
```

预期：在项目根下生成 `runtime/artifacts/`、`runtime/browser_profiles/taobao/`、`runtime/cache/` 等空目录。

### 1.3 执行预检查

```bash
uv run python src/phase1_cli.py preflight
```

预期输出：所有项目目录、配置、模型路由均显示 ✓。如果有 ✗，**回传给 Agent**，先不要继续。

### 1.4 跑测试确认代码可运行

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests
```

预期：`Ran 79 tests in xxx OK`。

---

## 2. 登录态准备（约 5 分钟）

> 2026-05-30 重要重写：旧版判定逻辑会把"未登录但首页有'我的淘宝'菜单"误判为已登录的反向 bug；同时旧版 `open-login-window` 只 goto 首页等待，不会跳到登录页 → 导致扫码后首页 DOM 不刷新 → 登录态拿不到。已全部修复。

### 2.1 检查当前登录状态（首次预期未登录）

```bash
uv run python src/phase1_cli.py check-login
```

预期输出（首次未登录）：
```
❌ 未登录（confidence=high）
  - 命中信号：body_login_hint
  - sso Cookie：_nk_=False unb=False
  - 当前 URL：https://www.taobao.com/
```

> 看 `confidence`：`high` = 判定可信；`low` = 页面没加载完，重试一次。
> 看 `sso Cookie`：`_nk_` 和 `unb` 是淘宝登录后必然下发的，**它们是否存在比 body 文本更可靠**。

### 2.2 打开淘宝登录页（手动扫码）

```bash
uv run python src/phase1_cli.py open-login-window --keep-open-seconds 240
```

新的流程（**与旧版不同，请仔细看**）：
1. 浏览器自动打开 `https://www.taobao.com` 拿到 before 快照；
2. 如果已登录则直接刷新 + 写 after 快照，直接结束；
3. 否则跳转到 `https://login.taobao.com` —— **页面应该出现淘宝的扫码二维码**；
4. **你用手机淘宝扫码**；
5. 淘宝会自动跳转回 `https://www.taobao.com/`（脚本每 3 秒轮询 URL 检测跳转）；
6. 检测到跳转后脚本会自动 `goto https://i.taobao.com/my_taobao.htm` 强制写入 sso Cookie；
7. 最后回到首页拿 after 快照，整个命令结束。

> ⚠️ **不要在脚本运行期间手动关闭浏览器**——会导致 Cookie 写入中断。让脚本自然结束（你扫码完会自动到第 5 步开始计时跳转，到第 7 步才会结束）。
>
> ⚠️ 如果命令结束后输出 `登录流程：timeout_without_login`，说明 240 秒里你没扫码或扫码没成功，重试一次。
>
> ⚠️ 如果输出 `登录流程：already_logged_in`，说明 profile 里 Cookie 已经有效（你之前扫过），直接跳到 2.3。

### 2.3 验证登录态

```bash
uv run python src/phase1_cli.py check-login
```

预期输出（已登录，2026-05-30 第五次更新格式）：
```
✅ 已登录（confidence=high）
  - 命中信号：cookie_nick, cookie_token
  - 昵称类 SSO Cookie：tracknick, lgc, dnk
  - Token 类 SSO Cookie：_tb_token_, aui
  - 当前 URL：https://www.taobao.com/
```

> **解读**：
> - `命中信号` 是 cookie_nick + cookie_token 两项强信号 → 已登录；
> - 实际命中的 SSO cookie 名字会列出来（淘宝当前主用 `tracknick / lgc / dnk / _tb_token_`，旧版的 `_nk_ / unb` 已经不下发）；
> - 即便 body 里有"亲，请登录"文本（淘宝首页 DOM 永远有这个隐藏链接），只要强信号命中，**不**会出现在 `命中信号` 列表里。

> ⚠️ **2026-05-30 第五次改进**：`check-login` 现在会**自动 reload 一次**重读登录态，解决"首次扫码后必须手动刷新一下才更新"的 race condition。
> 完整 JSON 里会有 `attempts` 字段显示两次尝试的判定结果，便于排查。

如果还是 `❌ 未登录`：

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `昵称类 SSO Cookie：无` 和 `Token 类 SSO Cookie：无`，`confidence=high` | 浏览器 profile 里没存到任何 SSO cookie | 重做 2.2，**不要中途关浏览器**；删除 `runtime/browser_profiles/taobao/` 重试 |
| `cookie_keys` 只有 `cna / t / xlly_s / _m_h5_tk` 这类 | 只下发了埋点 cookie | 扫码确认时如果有"是否允许 PC 登录"弹窗，需要在手机上确认；重做 2.2 |
| `confidence=low` 且 `body_preview` 很短 | 页面没加载完 | 增加网络等待；或确认网络代理设置 |
| `attempts` 里第一次未登录、第二次（reload 后）已登录 | 正常的 race condition，已被 reload 兜底 | 无须处理，最终判定为已登录即可 |
| 全部正常但仍未登录 | 淘宝可能下发了新的 cookie 字段 | 把 `runtime/artifacts/taobao_homepage_login_check.{json,html}` 回传 Agent |

---

## 3. 探针阶段（最重要：先探针后真抓）

> 探针不写入数据库、不触发 anti-bot 限速，专门用来快速发现选择器是否过期。

### 3.1 搜索页探针

```bash
uv run python src/phase1_cli.py probe-search-query --query "隔音窗 夹胶中空 系统窗 性价比"
```

产物：
- `runtime/artifacts/search_probe_*.html`（原始 HTML）
- `runtime/artifacts/search_probe_*.json`（包含 `selector_counts` / `records_preview` / `analysis.quality_score` / `analysis.priority_fixes`）

判断标准（看 JSON 里的 `analysis`）：
- ✅ `analysis.readiness == "ready"`：可继续 3.2。
- 🟡 `analysis.readiness == "partial"`：选择器部分命中，可继续但要观察。
- ⛔ `analysis.readiness == "needs_fix"`：把整个 JSON 回传 Agent，等修选择器。

### 3.2 详情页探针（从 3.1 结果里挑一个 detail_url）

```bash
uv run python src/phase1_cli.py probe-detail-url \
  --detail-url "https://item.taobao.com/item.htm?id=XXXXXXXXX"
```

产物：`runtime/artifacts/detail_probe_*.json`，看 `analysis.quality_score`。

### 3.3 评论区探针（可选，但建议跑）

```bash
uv run python src/phase1_cli.py probe-reviews \
  --title "上面挑的商品标题" \
  --detail-url "上面那个 detail_url"
```

### 3.4 全链路探针（一次性诊断）

```bash
uv run python src/phase1_cli.py probe-full \
  --query "隔音窗 夹胶中空 系统窗 性价比" \
  --title "上面挑的商品标题" \
  --detail-url "上面那个 detail_url"
```

产物里的 `full_analysis` 给出综合 readiness 与下一步建议。

> **如果任何探针 readiness != ready，停步**，把所有 `runtime/artifacts/*probe*.json` 回传 Agent。Agent 修选择器后给你 zip 补丁（ADR-013）。

---

## 4. 真实搜索调试（约 2 分钟）

> 探针通过后才做这一步。

```bash
uv run python src/phase1_cli.py search-once --query "隔音窗 夹胶中空 系统窗 性价比" --limit 5
```

产物：
- `runtime/artifacts/<run_id>_taobao_search_*.html`
- `runtime/artifacts/<run_id>_taobao_search_*.json`
- `runtime/artifacts/<run_id>_taobao_search_*.png`（截图）

检查：
- 控制台输出 5 个候选商品，标题 + URL 都非空。
- 候选不是广告位（标题含"广告"或店铺主页通常应被过滤掉）。

---

## 5. 真实详情页调试（约 2 分钟）

```bash
uv run python src/phase1_cli.py detail-once \
  --title "你的商品标题" \
  --detail-url "你的详情页 URL" \
  --price-text "718元/㎡" \
  --shop-name "XX门窗旗舰店"
```

预期：返回 `ProductDetail` JSON，包含 `glass_spec` / `frame_spec` / `seal_spec` 等字段。

如要跳过 LLM 字段补归纳（节省时间）：

```bash
uv run python src/phase1_cli.py detail-once \
  --title "..." --detail-url "..." --normalize-with-llm false
```

---

## 6. 真实完整链路调试（约 3~5 分钟）

```bash
uv run python src/phase1_cli.py live-demo \
  --scene "高架低频卧室" \
  --budget 8000 \
  --noise-source traffic \
  --frequency-profile low \
  --preferred-solution replace_window \
  --limit 3
```

这条命令会：
1. 生成购物意图
2. 搜淘宝 → 抓 3 个详情 → LLM 字段补归纳 → 排序
3. 对 Top N 做评论增强 → 二次排序
4. 调用本地模型生成对比总结
5. 把结果缓存到 SQLite（`runtime/cache/shopping_cache.sqlite3`）

完成后查看：
```bash
uv run python src/phase1_cli.py history          # 列出历史 run
uv run python src/phase1_cli.py export-latest-report   # 导出 Markdown 报告
uv run python src/phase1_cli.py export-latest-archive  # 导出 zip
```

---

## 7. 出现风控时的处理

如果任一命令抛出 `ShoppingRiskDetectedError`：

1. **立即停步**，不要重试。
2. `runtime/artifacts/` 里会有 `*_risk.json`，回传给 Agent。
3. 等几小时再重试（不要短时间内反复触发，可能加重风控）。
4. Agent 会根据 risk_type 调整策略：
   - `captcha`：建议手动登录后重试。
   - `access_limited`：建议把 `config.yaml: phase1.shopping.anti_bot.enforce_delay` 改成 `true` 并提高 `base_delay_seconds`。
   - `login_required`：重做第 2 步。

---

## 8. 联调后必须回传给 Agent 的东西

| 项目 | 路径 | 用途 |
|---|---|---|
| 探针 JSON | `runtime/artifacts/*probe*.json` | 修选择器 |
| 真实搜索 artifact | `runtime/artifacts/<run_id>_taobao_search_*.{html,json,png}` | 修列表抽取 |
| 真实详情 artifact | `runtime/artifacts/<run_id>_taobao_detail_*.{html,txt,png}` | 修详情抽取 |
| run bundle | `uv run python src/phase1_cli.py export-latest-archive` 输出的 zip | 完整 run 上下文 |
| 控制台报错 | 复制粘贴 | 定位异常 |
| 风控 artifact | `runtime/artifacts/*_risk.json` | 风控策略调整 |

**最简回传**：把整个 `runtime/artifacts/` 目录 zip 一下发给 Agent。

```bash
cd /Users/naturist/MusicProject/Shopping-Agent/soundproof-agent
zip -r /tmp/runtime_artifacts_$(date +%Y%m%d_%H%M%S).zip runtime/artifacts/
```

---

## 9. Agent 给你补丁后怎么应用（ADR-013）

Agent 修完后会在 workspace 出一个 `patches/patch_<时间戳>_<描述>.zip`，含 `PATCH_NOTES.md` 与 `soundproof-agent/...` 文件。

```bash
# 下载 zip 到 Mac 后：
cd /Users/naturist/MusicProject/Shopping-Agent
unzip -o /path/to/patch_xxx.zip
# 或者：cd 到上一级，让 zip 内的 soundproof-agent/ 直接覆盖
```

应用后：
1. 看 `PATCH_NOTES.md` 的"应用前置条件"。
2. 如改了 `pyproject.toml` → `uv sync`。
3. 如改了 `tests/` → `PYTHONPATH=src uv run python -m unittest discover -s tests`。
4. 重做出问题的那一步联调命令验证。

回滚：`git diff` 看改动，`git restore <file>` 回退。

---

## 10. 联调成功的判据

满足下面全部，Phase 1A 联调可视为通过：

- [ ] `probe-full` 在至少 2 个不同搜索词上 `readiness == ready`。
- [ ] `search-once` 在至少 3 个搜索词上稳定拿到 ≥3 个有效候选。
- [ ] `detail-once` 在至少 3 个商品上拿到 `glass_spec` / `frame_spec` 任意一项。
- [ ] `live-demo` 完整跑通一次，导出的 Markdown 报告内容合理。
- [ ] 联调期间未触发不可恢复的风控（偶发可接受）。

满足后 Agent 会通知你启动 **Phase 1B（咨询主链路 A/B/E + 协调员）**。

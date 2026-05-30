<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-30 11:50:00 CST
最后更新（北京时间，精确到秒）：2026-05-30 13:30:00 CST
镜像源：docs/隔音窗专家咨询与购物辅助Agent系统-项目需求文档-V1.docx
事实源约定：本 md 为事实源，docx 按需同步导出（见 DECISIONS.md ADR-006 + ADR-010）。
范围调整：2026-05-30 由 ADR-009 把咨询主链路重新纳入 V1；ADR-012 把知识库/RAG/视频管线进入 V1.5。
-->

# 专家咨询与购物辅助系统 — 项目需求文档 V1

> 阅读约定：
> - 每章先复述原始 V1 需求（来自原 docx），再用 **【V1 实际实现现状】** 子段标注现状。
> - 状态标签：
>   - ✅ 已实现
>   - 🟡 部分实现
>   - ⏳ Phase 1B / V1.5 计划中（待启动，前置依赖见 BACKLOG）
>   - ⛔ 未实现且尚未排期
>   - 🚫 V1+V1.5 永久不做
>   - 🔁 已被新决策替代

---

## #角色定位

你现在是我的技术合伙人。你的工作是帮我做出一个真正能用、能分享、能发布的产品。所有技术活儿你来搞定，但得让我随时知道进展，保持我的主导权。

### 【V1 实际实现现状（2026-05-30 同步）】
- ✅ 由 **Arena.ai Agent Mode** 充当技术合伙人；用户保留产品主导权。
- 🔁 与原文 §3.1 "Claude Code 作为开发助手"冲突 → 由 ADR-001 替代：**不使用 Claude Code**。

---

## #我的初步想法

### 1. 产品概述

#### 1.1 产品愿景
构建一个多 AI 协同的隔音窗领域专家咨询与购物辅助系统。用户通过自然语言描述噪音困扰，系统动态调度多位专家 Agent，提供从噪音诊断、材料选型、预算比价到施工验收的全流程服务。系统设计遵循通用"专家+购物助手"框架原则，为后续扩展至其他垂直领域（如汽车、家电）奠定基础。

#### 1.2 核心价值
- 专业诊断：基于声学原理精准分析噪音特征与隔音需求
- 个性化推荐：结合房屋状况、预算、气候等给出配置方案
- 真实比价：无痕采集淘宝/拼多多公开商品信息，预算透明
- 避坑指南：施工验收清单与社区经验沉淀，降低翻车风险
- 隐私安全：本地化部署，账号 Cookie 加密隔离，操作可审计

#### 【V1 实际实现现状（2026-05-30 同步）】
- 🟡 "真实比价"：✅ 淘宝公开页面抓取链路已实现（Playwright + 选择器 + 回退 + 探针 + 反爬骨架），🚫 拼多多 V1+V1.5 不做（ADR-002 / ADR-009 沿用禁区）。
- ⏳ "专业诊断 / 个性化推荐 / 避坑指南"：Phase 1B 由 ADR-009 承接（A 噪音 / B 材料 / E 施工 + F 协调员），落地后即满足。
- ✅ "隐私安全"：本地优先；URL 白名单（`src/security/url_guard.py`）；危险路径拦截；详情页 URL 规范化；登录态保存在本地浏览器 profile，不入库。

---

### 2. 用户场景与功能

#### 2.1 欢迎菜单（Slash Command `/soundproof`）
触发后显示简洁选项，支持对话中随时唤出：
- A. 快速评估：仅描述噪音与预算，快速输出摘要方案
- B. 完整方案：全流程诊断→选型→比价→施工
- C. 只比价 / 看商品：已知需求，直接搜索商品并对比
- D. 验收指导：已安装用户获取验收清单与常见问题
- E. 历史方案管理：浏览、对比、恢复历史咨询记录

#### 【V1 实际实现现状（2026-05-30 同步）】
- 🚫 Slash Command 入口：V1 不做（无聊天前端，V2+ 才考虑）。
- ✅ 模式 C「只比价/看商品」：CLI + API + 最小 Web 页面均可触发购物子链路。
- ⏳ 模式 A「快速评估」/ B「完整方案」/ D「验收指导」：Phase 1B 由 ADR-009 承接（A 噪音 / B 材料 / E 施工专家 + F 协调员），实装后即可对外暴露。
- 🟡 模式 E「历史方案管理」：购物 run 的历史/对比/分析已实现（`run_compare` / `run_analysis` / `phase1_cli history`），会话级历史 Phase 1B 落地后补齐。

#### 2.2 核心工作流（完整方案模式）
- 噪音困扰采集：F 协调员追问噪音类型、时段、房间类型、楼层、预算等
- 并行调度：参数齐备后，同时调用 A（噪音分析）、B（材料推荐）
- 购物参谋：基于 B 的方案，D 搜索平台商品并总结对比
- 施工指导：E 输出安装清单与验收要点
- 看板实时更新：每阶段结果通过 WebSocket 推送至独立 Web 页面
- 追问与回溯：点击看板任意卡片可查看详情浮层，或发起追问

#### 【V1 实际实现现状（2026-05-30 同步）】
- ⏳ F 协调员状态机：Phase 1B 由 ADR-009 承接；当前仅 schema 层定义了咨询上下文。
- ✅ D 购物参谋：完整购物子链路已实现（intent_builder → keyword_builder → 搜索 → 过滤 → 详情 → 提取 → 排序 → 评论增强 → 二次排序 → LLM 对比总结 → 缓存 → 报告导出）。
- 🚫 WebSocket 实时推送 / 看板卡片浮层：V2+ 才考虑。
- 🟡 最小开发态 Web 页面：已实装 dashboard / run detail / run analysis / artifact 预览 / 联调工具页（Jinja2，未用 HTMX/Alpine.js 完整方案）。

#### 2.3 其他特性
- 对话界面支持 Markdown 渲染、代码块、图片展示
- 看板支持暗黑模式
- 专家健康状态实时监控
- 购物缓存手动刷新

#### 【V1 实际实现现状（2026-05-30 同步）】
- 🚫 Markdown 对话渲染 / 暗黑模式：V1 不做（无对话前端）。
- ⛔ 专家健康监控：V1 不做。
- 🟡 购物缓存：✅ SQLite 缓存已实现，🟡 刷新方式当前是"每次运行写新 run"，未做"手动刷新某关键词缓存"按钮。

---

### 3. 系统架构

#### 3.1 架构原则
- 独立后端服务：所有业务逻辑、AI 调度、状态管理封装为 FastAPI Web 服务
- Claude Code 定位：作为开发阶段代码生成助手，并作为可选高级交互入口
- 本地优先：默认使用本地 Ollama 模型，仅用户明确要求时才调用商业模型
- 轻量隔离：不使用 Docker（避免 macOS GPU 性能损失），改用 Python 虚拟环境 + 网络代理沙箱 + 文件权限控制

#### 【V1 实际实现现状（2026-05-30 同步）】
- ✅ FastAPI 后端骨架（`src/api/app.py`，380 行）。
- 🔁 Claude Code → **被 ADR-001 替代**：开发流程改由 Arena.ai Agent Mode 主导，不使用 Claude Code。
- ✅ 本地优先：商业模型 `deepseek-chat` 配置存在但 `enabled: false`（参见 `config.yaml: phase0.candidates`）。
- ✅ 不用 Docker；用 `uv` 管理虚拟环境。
- 🟡 网络代理沙箱：✅ URL 白名单 + 危险路径拦截已实现（`src/security/url_guard.py`），⛔ 完整的本地代理拦截层未实装（当前用直连 + Playwright 上下文隔离 + 选择器约束）。

#### 3.2 架构全景图（节选）
```
用户浏览器 (对话区 HTMX + 看板 Alpine.js)
   │ WebSocket
FastAPI 后端
   ├─ F 协调员（状态机 + 调度器）
   ├─ A 噪音分析
   ├─ B 材料 + RAG
   ├─ D 购物 + 沙箱
   └─ E 施工指导
   ├─ SQLite DB
   └─ 知识库（向量）
        │ 本地调用
本地 Ollama 服务
   · qwen3.6:35b-a3b-q8_0 (F + 代码生成)
   · qwen3:14b (A/B/D/E)
   · qwen3-embedding:8b (知识库)
   · bge-m3:latest (备用)
```

#### 【V1 实际实现现状（2026-05-30 同步）】
- 🟡 后端：✅ FastAPI 应用 + 最小 Web 页面（Jinja2）；⛔ HTMX/Alpine.js 完整页面未做。
- 🟡 模型分配：**已被 ADR-003 升级**为三档路由（见 §7 段落"【V1 实际实现现状】"）。
- ⛔ 知识库（ChromaDB / 向量）：V1 未做。
- ✅ Ollama 本地调用骨架（`src/utils/ollama_client.py`）。

#### 3.3 外部服务
- 商业模型 API（仅兜底与代码生成增强）：DeepSeek API 或 GLM 5.1
- 购物平台：淘宝、拼多多公开网页

#### 【V1 实际实现现状（2026-05-30 同步）】
- 🟡 DeepSeek/GLM：配置存在但默认禁用。
- ✅ 淘宝。
- 🚫 拼多多：V1 不做。

---

### 4. 功能模块详述

#### 4.1 F 协调员
状态机：`IDLE → 意图分析 → (追问参数 | 调度专家 | 快捷模式) → 等待专家 → 整合更新`
槽位：噪音类型、时段、房间类型、楼层、预算、窗户尺寸、特殊需求
调度策略：参数齐全后并行；存在依赖串行（B 需 A 结果）
异常处理：格式错误自动重试一次；超时通知用户；失败可降级为纯 prompt（用户可选商业模型重试）

##### 【V1 实际实现现状（2026-05-30 同步）】
- ⏳ 状态机：Phase 1B 由 ADR-009 承接，落地于 `src/coordinator/state_machine.py`。
- ✅ 槽位映射：在 `src/shopping/intent_builder.py` 中以"咨询上下文 → 购物意图"的方式承接；Phase 1B 会增加 `src/coordinator/slots.py` 做交互式追问。
- 🚫 健康监控：V2+ 才考虑。

#### 4.2 A 噪音分析专家
- 实现方式：纯 Prompt（qwen3:14b）
- 输出 JSON：噪音类型 / 频率特征 / 预估声压级 / 建议隔声量

##### 【V1 实际实现现状（2026-05-30 同步）】
- ⏳ A 专家：Phase 1B 由 ADR-009 承接，落地于 `src/experts/noise_analyst.py`；评测路径 `eval_cases/noise_analysis_cases.json` 复用。
- 🔁 路由升级：实际选用 `qwen3.6:35b-a3b-q8_0` 而非 qwen3:14b（ADR-003）。

#### 4.3 B 材料与方案顾问
- 实现方式：RAG（本地知识库 + qwen3:14b）
- 输出：玻璃结构 / 型材 / 密封方案 / 预期降噪 / 知识源引用

##### 【V1 实际实现现状（2026-05-30 同步）】
- ⏳ B 专家纯 prompt 版：Phase 1B 由 ADR-009 承接，落地于 `src/experts/material_advisor.py`。
- ⏳ B 专家 RAG 化：V1.5 由 ADR-012 承接（ChromaDB + 嵌入 + 知识源引用）。
- 🔁 路由升级：实际由 `qwen3.6:35b-a3b-q8_0` 承担（ADR-003）。

#### 4.4 D 预算与购物参谋
- 实现方式：工具调用 + 安全沙箱（qwen3:14b）
- 沙箱：网络白名单 `*.taobao.com / *.pinduoduo.com`；过滤含 `order|delete|cart|password|payment` 的 URL；仅允许 GET
- Cookie：会话开始时一次性授权，加载到内存（加密，不落盘）
- 数据：抓取标题/价格/销量/店铺名/原始链接（剥离 Cookie 参数）；LLM 总结 3~5 款；存 SQLite
- 缓存策略：手动刷新

##### 【V1 实际实现现状（2026-05-30 同步）】
- ✅ **核心已实现**：搜索 → 列表 → 候选过滤（`filtering.py`）→ 详情 → 字段提取（`parser_rules.py` + `extraction_utils.py`，含回退）→ LLM 字段补归纳（`llm_services.py`）→ 排序（`ranking.py`）→ LLM 对比总结 → SQLite 缓存 → Markdown 报告。
- ✅ URL 白名单 / 危险路径拦截 / GET 限制：`src/security/url_guard.py`。
- ✅ 评论增强（第二阶段）：`review_pipeline.py` + `review_enricher.py` + `review_fetcher.py`（回放已通，真实抓取骨架已建）。
- ✅ 反爬：`src/security/anti_bot_policy.py` + `src/shopping/risk_detection.py`（验证码 / 访问受限页面探测）。
- 🟡 登录态：✅ 本地 Playwright user data 目录复用；⛔ 内存加密 Cookie 未做（当前依赖浏览器 profile 持久化）。
- 🚫 **加购 / 收藏 / 下单 / 付款：V1 暂不做**（ADR-002，用户原话）。
- 🚫 拼多多：V1 不做。
- 🟡 缓存刷新：每次运行写新 run，未做"针对关键词的手动刷新"按钮。
- 🔁 路由升级：实际购物推理 / 总结用 `qwen3-coder-next:q4_K_M`，字段补归纳用 `qwen3:14b`（ADR-003）。

#### 4.5 E 施工与验收指导
- 实现方式：纯 Prompt（qwen3:14b）
- 输出：安装前准备 / 步骤注意 / 验收标准 / 常见坑点

##### 【V1 实际实现现状（2026-05-30 同步）】
- ⏳ E 专家：Phase 1B 由 ADR-009 承接，落地于 `src/experts/installation_guide.py`，纯 prompt。

#### 4.6 知识库模块
- 向量存储：ChromaDB / FAISS
- 嵌入：qwen3-embedding:8b
- 文档模型：KnowledgeDocument（来源、质量分、多维度评分、标签）
- 质量评分：A 来源权威 / B 专业度 / C 时效 / D 社区可信 / E 信息密度 / F 重复度
- 视频管线：字幕下载（you-get/yt-dlp）→ 无字幕则 Whisper → LLM 摘要 + 评分 → 人工审核 → 切片入库
- 更新：watchdog 监控目录热加载

##### 【V1 实际实现现状（2026-05-30 同步）】
- ⏳ 整节移至 V1.5（ADR-012）。
- V1.5 范围：ChromaDB（默认）/ FAISS（fallback）；`qwen3-embedding:8b` 嵌入；手动入库 10~20 篇；六维度评分插件化；watchdog 热加载；B 专家 RAG 化；视频管线最低优先。
- 仅在 `model_router.yaml` 保留嵌入模型路由占位。

#### 4.7 看板与交互
- 前端：Alpine.js + Tailwind CSS
- 卡片：噪音诊断 / 方案配置 / 预算对比 / 施工清单 / 进度条 / 历史对比
- 交互：点击卡片浮层；专家在线/离线状态；暗黑模式
- 对话区：Markdown / 代码高亮 / 图片

##### 【V1 实际实现现状（2026-05-30 同步）】
- 🟡 **最小开发态 Web 页面已实装**（Jinja2 templates，9 个页面）：
  - `dashboard.html`：最近运行 / 事件统计 / selector override 状态
  - `run_detail.html`：运行详情 + step traces + artifact 链接 + ZIP 导出
  - `run_analysis.html`：运行分析 + 修复建议
  - `compare_runs.html`：运行间对比
  - `tools.html`：联调工具（4 种探针 + selector override 编辑）
  - `artifact_manifest.html` / `artifact_detail.html`：产物预览
  - `event_log.html`：事件日志
- 🚫 Alpine.js / 暗黑模式 / 卡片浮层 / 专家健康状态：V1 不做。
- 🚫 对话区 / Markdown 渲染：V1 不做（V1 没有聊天前端）。

---

### 5. 数据模型

#### 5.1 数据库选型
SQLite + SQLAlchemy ORM，可切换。

#### 5.2 核心表
- `sessions` / `messages` / `expert_outputs` / `solution_versions` / `product_cache` / `knowledge_references` / `user_preferences`（详见原 docx 表格）

#### 【V1 实际实现现状（2026-05-30 同步）】
- ✅ SQLite：`src/shopping/sqlite_cache.py`（232 行）。
- 🟡 当前未引入 SQLAlchemy ORM，直接用 sqlite3 + dataclass schema（`cache_models.py`），轻量但牺牲一些可移植性。
- 🟡 实际表：以"run 为中心"组织（runs / step_traces / events / artifacts / reports），与原 7 表结构不同。
- ⛔ `sessions / messages / solution_versions / knowledge_references / user_preferences`：V1 未建表（无会话主链与知识库）。

---

### 6. 安全方案

#### 6.1 安全层级
- 网络代理层：拦截非白名单域名 / 危险方法 / 敏感词 URL
- 工具约束层：D 专家仅能调用预置搜索函数
- 模型隔离层：商业 API 调用前过滤（去除 Cookie/Token/PII）
- 数据存储层：Cookie 仅内存加密；商品链接剥离 token；日志 30 天滚动
- 文件系统隔离：虚拟环境内执行，无敏感目录访问

#### 【V1 实际实现现状（2026-05-30 同步）】
- ✅ URL 白名单 + 危险路径拦截：`src/security/url_guard.py`（87 行）。
- ✅ 详情页 URL 规范化：`src/shopping/url_utils.py`。
- ✅ 反爬节流策略：`src/security/anti_bot_policy.py` + `politeness.py`。
- 🟡 商业模型 guard：未单独抽出模块，当前因 `enabled: false` 暂不触发。
- 🟡 Cookie 加密：V1 未实装（依赖浏览器 profile）。
- 🟡 日志滚动：未实装（依赖运行 artifact 的 run_id 隔离）。

#### 6.2 商业模型使用红线
- 绝对禁止传 Cookie / Session / PII / 完整商品链接 / 搜索截图
- 调用前 `model_guard` 模块白名单校验

#### 【V1 实际实现现状】
- ⛔ `model_guard` 模块未实装（因商业模型默认禁用）。

#### 6.3 安全测试用例（10 条 S-01 ~ S-10）
（见原 docx 表 7）

#### 【V1 实际实现现状】
- 🟡 仅 S-03/S-08/S-09（URL 拦截）有覆盖（`test_url_guard.py`）。
- ⛔ S-01/S-02/S-05/S-06/S-07/S-10 未覆盖。

---

### 7. 模型分配与降级策略

**原文规则**：默认本地；用户不满意时 F 调用商业模型重试；商业调用专用日志。
**原文表 8**：A/B/D/E 全部使用 `qwen3:14b`；F 用 `qwen3.6:35b-a3b-q8_0`。

#### 【V1 实际实现现状（2026-05-30 同步）— 已被 ADR-003 升级】
两轮 Phase 0 评测后，路由升级为：

| 角色 | 实际主模型 | fallback | escalation |
|---|---|---|---|
| 协调员 / 噪音分析 / 方案顾问 | `qwen3.6:35b-a3b-q8_0` | `qwen3:14b` | `deepseek-chat` |
| 购物推理 / 购物总结 | `qwen3-coder-next:q4_K_M` | `qwen3.6:35b-a3b-q8_0` | `deepseek-chat` |
| 购物字段补归纳 | `qwen3:14b` | `qwen3-coder-next:q4_K_M` | — |
| 浏览器执行器 | `deterministic_playwright` | `headed_playwright_with_manual_takeover` | — |
| 嵌入 | `qwen3-embedding:8b` | `bge-m3:latest` | — |
| 项目开发流程 | `arena-ai-agent-mode` | — | — |

- escalation 触发：**完全手动，仅用户主动提出时触发**（ADR-011）。CLI / API 将预留 `--use-cloud-escalation` 开关，实装前必须先做 `src/security/model_guard.py` 强制剥离敏感信息。

---

### 8. 开发与工程规范

#### 8.1 目标环境
macOS Sequoia 15.6.1；Apple M1 Max / 64GB；Python 3.11；Ollama V0.23.1（已拉取 bge-m3 / qwen3-embedding:8b / qwen3:14b / qwen3.6:35b-a3b-q8_0）；VS Code；Claude Code for VS Code；uv。

##### 【V1 实际实现现状】
- 🔁 Claude Code 已被 ADR-001 移除。其余目标环境保持。
- ✅ uv 已使用（见 `pyproject.toml`）。

#### 8.2 项目结构（src-layout）
（详见原文目录树）

##### 【V1 实际实现现状】
实际目录与原文基本一致，少数差异：
- `src/experts/`、`src/knowledge/`、`src/models/`、`src/web/static/` 等目录 V1 暂未生成（对应功能未做）。
- `src/shopping/`：✅ 36 个模块文件（购物子链路重头），原文档未单独列出此目录。
- `src/phase0_cli.py` / `src/phase1_cli.py`：✅ 两个阶段化的 CLI 入口（原文档未提）。
- `docs/`：✅ 大量阶段性维护文档（HANDOFF / CURRENT_STATE / BACKLOG / DECISIONS / CHANGELOG / ONBOARDING_CHECKLIST / OPEN_QUESTIONS / 探针 / 选择器 / 联调 / API plan / Web plan 等）。

#### 8.3 技术选型约束
FastAPI + Jinja2 + HTMX + Alpine.js + Tailwind CSS；SQLite + SQLAlchemy；uv；MLX→MPS→CPU 自动回退；中文亲和。

##### 【V1 实际实现现状】
- ✅ FastAPI + Jinja2。
- ⛔ HTMX / Alpine.js / Tailwind：V1 仅最小内联样式。
- 🟡 SQLite：✅；SQLAlchemy ORM：⛔ 未引入。
- ✅ uv。
- ⛔ MLX/MPS 自动回退：未实装（Ollama 自管）。
- ✅ 中文亲和（注释 / docstring / 文档全中文；错误日志保留英文 + 中文注释）。

#### 8.4 代码质量标准
- 文件头部注释注明"创建该文件的 LLM 大模型名称"和"创建时间（北京时间，精确到秒）"
- PEP 8 / 类型注解 / 中文 Google 风 docstring / 行内中文注释 / 关键决策注释理由
- 抽象基类定义专家接口
- 统一日志（logging，控制台 + 文件，异常堆栈）

##### 【V1 实际实现现状】
- ✅ 文件头部注释规范在所有新文件中遵守（见 `docs/AGENT_HANDOFF.md` §7.6）。
- ✅ 类型注解 / 中文 docstring / 抽象接口（`ShoppingExecutorInterface`）。
- 🟡 统一日志：基础 logging 已用，未做完整双输出 + 滚动配置。

#### 8.5 中国网络环境适配
（见原文表 9 各组件镜像）

##### 【V1 实际实现现状】
- 🟡 Python 包源 / Ollama / Hugging Face：用户本机已配置；项目本身未做镜像切换脚本。

#### 8.6 配置管理
- 所有可变参数放 `config.yaml` 或环境变量；`.env.example` 说明每个变量；config.yaml 可覆盖默认。

##### 【V1 实际实现现状】
- ✅ `config.yaml` + `.env.example` + `model_router.yaml` 三件套。
- ✅ `src/config.py` 统一加载。
- ✅ `runtime/selector_overrides.yaml` 联调期热覆盖选择器。

---

### 9. 实施路线图

原文 5 个 Phase：
1. **Phase 1 骨架打通**：FastAPI / F 协调员 / A/B 专家 prompt / SQLite / 对话+看板骨架 / Ollama 封装
2. **Phase 2 知识注入**：ChromaDB / 10-20 篇入库 / B-RAG / 看板浮层 / 健康检查
3. **Phase 3 购物安全**：网络代理 / 淘宝拼多多搜索 / Cookie / 商品缓存 / 商业 guard
4. **Phase 4 施工历史**：E 专家 / SQLAlchemy / 方案版本 / 历史对比
5. **Phase 5 优化增强**：视频管线 / 自动评分 / DeepSeek/GLM 兜底 / 偏好学习

#### 【V1 实际实现现状（2026-05-30 同步） — 实际路线已重排】

| 实际阶段 | 状态 | 对应原文 Phase | 备注 |
|---|---|---|---|
| **Phase 0：模型评测与路由定稿** | ✅ 已完成 | — | 两轮评测，结论见 `model_router.yaml` |
| **Phase 1A：淘宝购物主链路 MVP**（当前阶段） | 🟡 收尾中 | 主要对应原 Phase 3 + 部分 Phase 1 | 联调启动判据见 ADR-008 |
| **Phase 1B：咨询主链路补齐**（V1 范围内） | ⏳ 待启动 | 对应原 Phase 1 + 4 | ADR-009；前置依赖 Phase 1A 联调通过 |
| **Phase 1C：咨询↔购物 整合闭环** | ⏳ 待启动 | — | Phase 1B 完成后 |
| **V1.5：知识库 / RAG / 视频管线** | ⏳ 待启动 | 对应原 Phase 2 + 5 | ADR-012；前置依赖 V1 全部交付 |
| **V2+**：商业 escalation 自动化 / 偏好学习 / 拼多多 / 看板暗黑 / WebSocket / 健康监控 | 🚫 V1+V1.5 不做 | — | ADR-002 禁区清单延续 |

**当前 Phase 1 已落地能力（截至 2026-05-30，69 项测试全通过）**：
1. 咨询上下文 → 购物意图（`intent_builder.py`）
2. 购物意图 → 搜索词（`keyword_builder.py`）
3. 列表页候选过滤（`filtering.py`）
4. 详情页确定性字段提取 + 回退（`parser_rules.py` + `extraction_utils.py`）
5. LLM 字段补归纳 + LLM 对比总结（`llm_services.py`）
6. 确定性排序（`ranking.py`）
7. SQLite 缓存（`sqlite_cache.py`）
8. 历史记录 / 运行对比 / 运行分析
9. Markdown 报告导出（`report_builder.py`）
10. 评论规则审查骨架 + 评论增强（回放已通）
11. 反爬风险策略骨架 + 页面风险识别（验证码 / 访问受限）
12. URL 白名单 + 危险路径拦截 + 详情页 URL 规范化
13. 选择器配置中心化 + YAML override + 回退策略
14. 探针能力（搜索页 / 详情页 / 评论 / 全链路）+ 探针质量分析
15. 运行级 artifact 与 step traces；run bundle / ZIP 导出
16. handoff 快照
17. CLI（`phase1_cli.py`）+ FastAPI（`api/app.py`，380 行）+ 最小 Web 页面（9 个模板）
18. 淘宝 Playwright 执行器 MVP（660 行，**未实机验证**）
19. 维护文档体系：CHANGELOG / DECISIONS / HANDOFF / CURRENT_STATE / BACKLOG / ONBOARDING_CHECKLIST / OPEN_QUESTIONS

**当前 P0 未完成（详见 `BACKLOG.md`）**：
- 第一次真实淘宝联调
- 列表页 / 详情页选择器在真页上的修正
- 登录态复用稳定性验证
- 验证码 / 风控页识别真正接到执行器中断分支

---

### 10. 扩展性设计

- 所有专家继承自 `BaseExpert`
- 知识库评分插件化
- 协调员状态机槽位可配置
- 购物平台抽象为 `ShoppingPlatform` 接口

#### 【V1 实际实现现状】
- ⏳ `BaseExpert`：Phase 1B 由 ADR-009 承接，落地于 `src/experts/base.py`。
- ✅ 购物执行器抽象：`src/shopping/executor_interface.py`（`ShoppingExecutorInterface`），已有 `playwright_executor` / `replay_executor` 两实现。
- ⏳ 知识库评分插件化：V1.5 由 ADR-012 承接。
- ⏳ 槽位配置化：Phase 1B 由 ADR-009 承接，落地于 `src/coordinator/slots.py`。

---

### 11. 另外一个技术栈组合的想法

| 层次 | 推荐项目 | 作用 |
|---|---|---|
| 编排层 | CrewAI 或 LangGraph | Agent 协作 |
| 咨询层 | TradingAgents 思路 + RAG | 多角色辩论 |
| 搜索层 | Stagehand | 商品结构化提取 |
| 执行层 | Browser-Use | 加购下单 |
| 测试层 | WebArena | Agent 完成率评测 |
| 角色库 | agency-agents-zh | Prompt 模板 |

#### 【V1 实际实现现状】
- ⛔ V1 未采用上述任何一项。
- ✅ 当前用"确定性 Playwright + 选择器配置"代替 Stagehand / Browser-Use（ADR-004 理由）。
- 🟡 是否引入 LangGraph 做协调员状态机，待 OQ-002 决策。

---

## #我有多认真

> 我想分享给别人

## #项目框架（阶段流程）

1. 阶段一：需求发现
2. 阶段二：规划
3. 阶段三：开发
4. 阶段四：打磨
5. 阶段五：交接

### 【V1 实际实现现状】
- ✅ 阶段一 / 阶段二：已交付（Phase 0 评测 + Phase 1 计划文档）。
- 🟡 阶段三：进行中（Phase 1 MVP 完成代码 + 测试，待真实联调）。
- ⛔ 阶段四 / 五：未开始。

## #配合方式 / #原则

（保留原文）

---

## 文档版本

- **V1 原稿**：用户初拟，时间未注明。
- **V1 实施同步版**：2026-05-30 由 Arena.ai Agent Mode 在每章追加"V1 实际实现现状"段。
- **2026-05-30 范围扩容**：依据 ADR-009 把咨询主链路重新纳入 V1（Phase 1B）；依据 ADR-012 把知识库/RAG/视频管线移到 V1.5。
- **同步频率**：按需触发（ADR-010），见 ONBOARDING_CHECKLIST.md 第 6 步、DECISIONS.md ADR-010。

## 相关 ADR 索引

- ADR-001：开发流程用 Arena.ai Agent Mode（不用 Claude Code）
- ADR-002：V1 范围切片（已被 ADR-009 superseded）
- ADR-003：模型路由三档分配
- ADR-004：确定性 Playwright，不用 AI 代理
- ADR-005：反爬"慢、少、可中断、可人工接管"
- ADR-006：文档体系 md 优先（同步频率部分被 ADR-010 覆盖）
- ADR-007：选择器中心化 + override + 回退
- **ADR-008**：真实淘宝联调启动判据
- **ADR-009**：V1 补齐咨询主链路（Phase 1B/1C）
- **ADR-010**：V1 需求文档按需同步
- **ADR-011**：商业 escalation 仅手动
- **ADR-012**：V1.5 范围（知识库 / RAG / 视频管线）
- **ADR-013**：实机测试期 zip 补丁交付机制

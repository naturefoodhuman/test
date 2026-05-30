<!--
创建该文件的LLM大模型名称：Arena.ai Agent Mode
创建时间（北京时间，精确到秒）：2026-05-29 17:30:00 CST
-->

# Phase 1 进度记录

## 当前目标

打通淘宝购物主链路 MVP：

- 搜索词生成
- 列表页抓取
- 详情页抓取
- 商品结构化
- 商品对比总结

## 当前进度

- [x] Phase 0 完成
- [x] 最终模型路由定稿
- [x] 购物 schema 初版
- [x] 关键词构建器初版
- [x] 咨询上下文 → 购物意图构建器
- [x] 商品候选过滤器
- [x] 商品价格解析工具
- [x] 商品确定性排序器
- [x] 购物 Markdown 报告生成器
- [x] 商品评论规则审查骨架
- [x] 评论增强器与回放抓取器
- [x] 评论探针能力（CLI/API/Web）
- [x] 评论探针 selector 统计与匿名率信息
- [x] 全链路探针能力（CLI/API/Web）
- [x] 反爬与封号风险策略骨架
- [x] 页面风险识别（验证码/访问受限）
- [x] URL 白名单与危险路径拦截
- [x] 详情页 URL 规范化
- [x] 选择器配置中心化
- [x] 选择器 YAML 覆盖加载能力
- [x] 选择器 override 校验能力
- [x] 选择器 override 备份能力
- [x] 选择器 override 恢复能力
- [x] 详情页字段提取工具函数抽离（title/shop/price/body）
- [x] 详情页字段提取回退逻辑（body 正则、page.title 等）
- [x] 运行级 run_id 与 artifact 追踪
- [x] 工作流步骤 trace（耗时/状态/备注）
- [x] 搜索页探针命令与接口
- [x] 搜索页探针质量分析（广告比例、价格区间、标题长度）
- [x] 详情页探针命令与接口
- [x] 详情页探针字段优先级分析
- [x] 详情页探针 quality_score 评分
- [x] 事件日志查看能力
- [x] 运行 bundle 导出器
- [x] 运行 ZIP 档案导出器
- [x] 最小开发态 Web 页面骨架
- [x] 首页运行诊断 / 事件统计 / 最近运行展示
- [x] 首页 selector override 校验与内容展示
- [x] 首页 selector override 差异摘要与备份列表展示
- [x] 首页最近运行比较摘要
- [x] 首页最近运行分析摘要与入口
- [x] 运行详情页 step traces / artifact 链接展示
- [x] 运行详情页 Artifact Manifest 区块与 ZIP 导出入口
- [x] 运行分析页（run analysis）
- [x] artifact 文本预览页
- [x] 联调工具页（搜索页探针 / 详情页探针 / 评论探针 / 全链路探针）
- [x] 联调工具页支持保存 selector override
- [x] 联调工具页支持恢复 selector backup
- [x] 联调工具页支持重置默认模板
- [x] 联调工具页支持备份预览
- [x] Phase 1 执行计划文档
- [x] 商品缓存数据结构初版
- [x] 确定性解析规则初版
- [x] 浏览器执行器抽象接口初版
- [x] 浏览器 profile 管理器初版
- [x] SQLite 缓存存储初版
- [x] 执行事件统计
- [x] 模型路由加载器
- [x] 运行时依赖工厂（factory）
- [x] 应用服务层（app service）
- [x] 运行时 diagnostics
- [x] handoff snapshot 构建器
- [x] LLM 字段补归纳服务初版
- [x] LLM 商品对比总结服务初版
- [x] 本地回放执行器
- [x] 购物工作流编排器初版
- [x] 运行比较能力（run compare）
- [x] 运行分析能力（run analysis）
- [x] 淘宝 Playwright 执行器 MVP（未实机验证）
- [x] 淘宝 Playwright 执行器回退选择器支持
- [x] 可配置评论增强与可配置 anti-bot 参数
- [x] 可配置节流延时计算
- [x] Phase 1 CLI 初版
- [x] 登录态检查 / 登录窗口命令
- [x] 风控页面探测命令
- [x] 真实淘宝搜索 / 详情 / live demo 命令入口
- [x] 历史记录查看命令
- [x] 调试产物查看命令
- [x] Markdown 报告导出命令
- [x] API 骨架（回放、历史、健康检查、报告、artifact、diagnostics、handoff）
- [x] 真实抓取 API 实验接口（search-once / detail-once / live-run / probe-search / probe-detail / probe-reviews / probe-full）
- [x] `src/main.py` 应用入口
- [x] 真实淘宝联调清单文档
- [x] 搜索页 / 详情页 / 评论探针说明文档
- [x] 选择器覆盖指南
- [x] 评论与反爬策略文档
- [x] 社区参考策略文档
- [x] 基础单元测试通过（69项）

## 当前工作流特征

当前真实购物主链已经形成固定顺序：

1. 咨询上下文 → 购物意图
2. 购物意图 → 搜索词
3. 列表页抓取（主选择器 + 回退选择器）
4. 候选过滤
5. 详情页抓取
6. URL 安全校验与规范化
7. 确定性字段提取（带回退逻辑）
8. LLM 字段补归纳（可选）
9. 确定性排序
10. 前 N 个候选做评论增强
11. 再次排序
12. LLM 对比总结
13. SQLite 缓存
14. Markdown 报告导出
15. run bundle / archive 导出
16. run compare
17. run analysis

## 当前策略亮点

- 搜索前：先从咨询上下文生成购物意图
- 搜索后：先过滤明显不属于窗产品的噪声候选
- 详情前：先做 URL 白名单与危险路径拦截
- 详情后：先用确定性规则提取商品字段（优先主选择器，失败时回退）
- 标题/店铺/价格/正文的候选选择逻辑已从执行器中抽离成纯函数，后续调试更快
- 选择器支持 YAML 覆盖，联调时可先改配置再决定是否回写代码
- 现在还能对 override 文件直接做校验、备份、恢复，并在 Web 页面里直接操作
- 探针分析给出具体优先级修复建议（priority_fixes）
- 探针分析包含 quality_score 和 quality_analysis，帮助判断是否可用
- 总结前：先做一次确定性排序，把明显更适合的商品排前面
- 评论增强采用第二阶段策略，只对 Top 候选处理
- 评论探针可在真实联调前先单点检查评论区域是否能抓到有效文本
- 全链路探针可一次性给出搜索页 / 详情页 / 评论区的综合 readiness 建议
- 反爬策略已进入工作流，具备事件统计、页面风险识别、URL 防护与可配置延时
- 运行时支持 diagnostics 和 handoff snapshot 导出
- 搜索页 / 详情页探针命令可在真实联调前快速诊断选择器命中情况
- 搜索页探针已能直接给出 readiness 与建议
- 运行级 artifact 带 run_id 前缀，历史与产物的关联更清晰
- 运行 bundle 与 ZIP 档案可直接导出，便于分享、复盘、handoff
- 运行比较能力可用于对比 selector 改动前后的效果差异
- 运行分析能力可直接给出下一步修复建议
- 运行级 step traces 可帮助定位问题发生在搜索 / 详情 / 评论 / 总结哪个阶段
- 开发态 Web 页面已接入，可视化看最近运行、事件日志、报告、artifact、联调工具、selector override 状态、运行对比、运行分析
- 结果后：可导出 Markdown 报告用于分享和复盘
- 通过 app service、factory、api skeleton 把 CLI / API / 后续 Web 复用边界固定下来

## 下一步

1. 第一次真实淘宝联调
2. 根据真页结果修正列表页与详情页选择器
3. 强化 detail 文本提取与价格/店铺识别
4. 将 anti-bot 真正接入 Playwright 节流与验证码中断逻辑
5. 把真实评论抓取接入第二阶段候选增强链路
# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 20:18:32 CST

from __future__ import annotations

from shopping.schemas import ProductDetail, ShoppingSessionSnapshot


class ShoppingReportBuilder:
    """购物结果报告生成器。

    作用：
    - 把结构化快照导出成适合用户阅读和分享的 Markdown；
    - 为未来 Web 页面、历史报告导出、接口返回 Markdown 做准备；
    - 报告中尽量保留“为什么推荐”和“有哪些风险”两类关键信息。
    """

    def build_markdown(self, snapshot: ShoppingSessionSnapshot) -> str:
        """生成 Markdown 报告。"""

        lines: list[str] = [
            "# 购物决策报告",
            "",
            f"- 运行 ID：{snapshot.run_id or '未记录'}",
            f"- 场景：{snapshot.search_intent.scene}",
            f"- 搜索词：{snapshot.search_query}",
            f"- 预算等级：{snapshot.search_intent.budget_level}",
            f"- 方案类型：{snapshot.search_intent.solution_type}",
            "",
            "## 候选商品",
            "",
        ]

        for index, product in enumerate(snapshot.detailed_products, start=1):
            lines.extend(self._render_product(index, product))

        if snapshot.filtered_out_products:
            lines.extend(["## 被过滤候选", ""])
            for item in snapshot.filtered_out_products:
                lines.append(f"- {item.title or '未命名候选'}：{item.reason}")
            lines.append("")

        if snapshot.artifact_names:
            lines.extend(["", f"- 关联产物数：{len(snapshot.artifact_names)}", ""])

        if snapshot.workflow_notes:
            lines.extend(["## 工作流备注", ""])
            lines.extend([f"- {item}" for item in snapshot.workflow_notes])
            lines.append("")

        if snapshot.step_traces:
            lines.extend(["## 步骤轨迹", "", "| 步骤 | 状态 | 耗时(ms) | 备注 |", "|---|---|---:|---|"])
            for trace in snapshot.step_traces:
                notes = "；".join(trace.notes) if trace.notes else ""
                lines.append(f"| {trace.step} | {trace.status} | {trace.duration_ms} | {notes} |")
            lines.append("")

        if snapshot.comparison_summary is not None:
            lines.extend(
                [
                    "## 推荐结论",
                    "",
                    f"- 推荐项：{snapshot.comparison_summary.recommended_option}",
                    f"- 推荐理由：{snapshot.comparison_summary.reason_summary}",
                    "",
                    "### 风险点",
                ]
            )
            if snapshot.comparison_summary.risk_points:
                lines.extend([f"- {item}" for item in snapshot.comparison_summary.risk_points])
            else:
                lines.append("- 暂无")

            lines.extend(["", "### 后续搜索优化", ""])
            if snapshot.comparison_summary.search_refinement:
                lines.extend([f"- {item}" for item in snapshot.comparison_summary.search_refinement])
            else:
                lines.append("- 暂无")

        return "\n".join(lines).strip() + "\n"

    def _render_product(self, index: int, product: ProductDetail) -> list[str]:
        """渲染单个商品。"""

        lines = [
            f"### 候选 {index}：{product.title}",
            "",
            f"- 价格：{product.price_text or '未知'}",
            f"- 店铺：{product.shop_name or '未知'}",
            f"- 玻璃：{product.glass_spec or '未识别'}",
            f"- 型材/结构：{product.frame_spec or '未识别'}",
            f"- 密封：{product.seal_spec or '未识别'}",
            f"- 五金：{product.hardware_keyword or '未识别'}",
            f"- 排序分：{product.ranking_score if product.ranking_score is not None else '未计算'}",
            "",
        ]

        lines.append("- 安装服务：" + ("、".join(product.installation_services) if product.installation_services else "未识别"))
        lines.append("- 排序理由：" + ("；".join(product.ranking_reasons) if product.ranking_reasons else "暂无"))
        lines.append("- 风险标记：" + ("；".join(product.risk_flags) if product.risk_flags else "暂无"))
        lines.append(f"- 评论抽样：{product.review_effective_count}/{product.review_sample_count} 条有效")
        lines.append("- 评论亮点：" + ("；".join(product.review_highlights) if product.review_highlights else "暂无"))
        lines.append("- 评论风险：" + ("；".join(product.review_risk_flags) if product.review_risk_flags else "暂无"))
        lines.append("")
        return lines

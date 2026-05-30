# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 03:20:12 CST

from __future__ import annotations

from typing import Any

from shopping.cache_models import ShoppingRunCache


class RunAnalyzer:
    """单次运行分析器。

    目标：
    - 在真实联调阶段快速给出“这次运行最值得关注的问题”；
    - 让 CLI / API / Web 都能直接复用同一套分析逻辑；
    - 优先输出适合下一步动作的建议，而不是只做统计展示。
    """

    def analyze(self, run_cache: ShoppingRunCache) -> dict[str, Any]:
        """分析一次运行。"""

        snapshot = run_cache.to_snapshot()
        warnings: list[str] = []
        next_actions: list[str] = []

        if len(snapshot.listing_products) == 0:
            warnings.append("列表页没有保留候选商品。")
            next_actions.append("先运行搜索页探针，检查卡片选择器与链接提取逻辑。")

        if len(snapshot.filtered_out_products) >= len(snapshot.listing_products) and snapshot.filtered_out_products:
            warnings.append("过滤掉的候选较多，可能需要复核过滤关键词。")
            next_actions.append("检查 filtered_out_products 的原因，确认是否过滤过严。")

        if snapshot.detailed_products:
            missing_title = sum(1 for item in snapshot.detailed_products if not item.title)
            missing_price = sum(1 for item in snapshot.detailed_products if not item.price_text)
            missing_shop = sum(1 for item in snapshot.detailed_products if not item.shop_name)
            short_body = sum(1 for item in snapshot.detailed_products if len(item.raw_spec_text or "") < 200)

            if missing_price:
                warnings.append(f"有 {missing_price} 个候选未识别到价格。")
                next_actions.append("优先检查详情页价格选择器命中情况。")
            if missing_shop:
                warnings.append(f"有 {missing_shop} 个候选未识别到店铺名。")
                next_actions.append("优先检查详情页店铺名选择器或回退策略。")
            if short_body:
                warnings.append(f"有 {short_body} 个候选正文过短。")
                next_actions.append("优先运行详情页探针，确认正文候选区域是否足够长。")
            if missing_title:
                warnings.append(f"有 {missing_title} 个候选标题为空。")
                next_actions.append("检查详情页标题选择器与页面 title 回退逻辑。")

        review_sparse = [item.title for item in snapshot.detailed_products if item.review_sample_count and item.review_effective_count == 0]
        if review_sparse:
            warnings.append("评论样本存在但有效评论不足。")
            next_actions.append("检查评论抓取质量，或暂时降低评论在选购中的权重。")

        if snapshot.comparison_summary is None:
            warnings.append("本次运行未生成推荐总结。")
            next_actions.append("检查购物总结模型调用与输入候选质量。")

        step_summary = {
            item.step: {
                "status": item.status,
                "duration_ms": item.duration_ms,
                "notes": item.notes,
            }
            for item in snapshot.step_traces
        }

        return {
            "run_id": snapshot.run_id,
            "candidate_count": len(snapshot.detailed_products),
            "filtered_out_count": len(snapshot.filtered_out_products),
            "artifact_count": len(snapshot.artifact_names),
            "warning_count": len(warnings),
            "warnings": warnings,
            "next_actions": next_actions,
            "step_summary": step_summary,
        }

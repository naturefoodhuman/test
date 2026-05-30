# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 16:13:50 CST

from __future__ import annotations

from shopping.schemas import ShoppingSearchIntent


class KeywordBuilder:
    """购物搜索词构建器。

    先用确定性规则生成第一版搜索词，后续再叠加 LLM 改写。
    这么做的原因是：即使 LLM 阶段异常，购物模块仍然能退化运行。
    """

    def build_query(self, intent: ShoppingSearchIntent) -> str:
        """根据购物意图生成首选搜索词。"""

        tokens: list[str] = []
        tokens.extend(intent.primary_keywords)

        if intent.solution_type == "add_inner_window":
            tokens.append("内窗")
        elif intent.solution_type == "replace_window":
            tokens.append("系统窗")

        if intent.budget_level == "low":
            tokens.append("性价比")
        elif intent.budget_level == "high":
            tokens.append("高配")

        # 去重同时保持顺序，避免搜索词被无谓放大。
        deduplicated: list[str] = []
        for token in tokens:
            normalized = token.strip()
            if normalized and normalized not in deduplicated:
                deduplicated.append(normalized)

        return " ".join(deduplicated)

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 23:00:19 CST

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from shopping.schemas import ShoppingSearchIntent


class ConsultationContext(BaseModel):
    """咨询阶段输出给购物模块的最小上下文。

    说明：
    - 这不是完整用户档案，而是进入购物决策前必须保留的核心信息；
    - 先保持字段少而稳，避免 Phase 1 过早做成“大而全”的槽位模型。
    """

    scene: str = Field(description="用户场景摘要，例如：高架低频卧室、儿童房靠地铁")
    budget: int | None = Field(default=None, description="预算，单位元；若未知可为空")
    noise_source: Literal["traffic", "rail", "hvac", "mixed", "unknown"] = "unknown"
    frequency_profile: Literal["low", "mid_high", "full_band", "unknown"] = "unknown"
    preferred_solution: Literal["replace_window", "add_inner_window", "both_possible"] = "both_possible"
    room_type: str | None = None
    notes: list[str] = Field(default_factory=list)


class ShoppingIntentBuilder:
    """把咨询结论翻译成购物搜索意图。

    设计原则：
    1. 先用规则把最关键的搜索方向确定下来；
    2. 后续可以在此基础上叠加 LLM 改写，但不依赖 LLM 才能运行；
    3. 购物搜索词必须围绕“结构、密封、方案类型”展开，而不是只围绕噪音描述本身。
    """

    def build(self, context: ConsultationContext) -> ShoppingSearchIntent:
        """根据咨询上下文生成购物搜索意图。"""

        budget_level = self._map_budget_to_level(context.budget)
        primary_keywords = self._build_primary_keywords(context=context, budget_level=budget_level)
        negative_keywords = self._build_negative_keywords(context)
        notes = list(context.notes)

        if context.frequency_profile == "low":
            notes.append("优先关注夹胶、密封、低频场景实测")
        if context.preferred_solution == "add_inner_window":
            notes.append("优先考虑内窗、加装方案、施工干扰小")

        return ShoppingSearchIntent(
            scene=context.scene,
            budget_level=budget_level,
            solution_type=context.preferred_solution,
            primary_keywords=primary_keywords,
            negative_keywords=negative_keywords,
            notes=notes,
        )

    @staticmethod
    def _map_budget_to_level(budget: int | None) -> Literal["low", "medium", "high"]:
        """把预算映射为购物预算等级。"""

        if budget is None:
            return "medium"
        if budget <= 4000:
            return "low"
        if budget <= 10000:
            return "medium"
        return "high"

    def _build_primary_keywords(
        self,
        *,
        context: ConsultationContext,
        budget_level: Literal["low", "medium", "high"],
    ) -> list[str]:
        """构建主关键词。"""

        tokens: list[str] = ["隔音窗"]

        if context.preferred_solution == "add_inner_window":
            tokens.append("内窗")
        elif context.preferred_solution == "replace_window":
            tokens.append("系统窗")
        else:
            tokens.extend(["系统窗", "内窗"])

        if context.frequency_profile == "low":
            tokens.extend(["夹胶", "三道密封"])
        elif context.frequency_profile == "mid_high":
            tokens.append("中空")
        elif context.frequency_profile == "full_band":
            tokens.extend(["夹胶中空", "密封"])

        if context.noise_source == "rail":
            tokens.append("地铁")
        elif context.noise_source == "traffic":
            tokens.append("临街")
        elif context.noise_source == "hvac":
            tokens.append("低频")

        if budget_level == "low":
            tokens.append("性价比")
        elif budget_level == "high":
            tokens.append("高配")

        deduplicated: list[str] = []
        for token in tokens:
            normalized = token.strip()
            if normalized and normalized not in deduplicated:
                deduplicated.append(normalized)
        return deduplicated

    @staticmethod
    def _build_negative_keywords(context: ConsultationContext) -> list[str]:
        """构建负向关键词。

        这部分不会直接喂给淘宝搜索，但会在后续过滤和对比阶段使用。
        """

        negative_keywords: list[str] = []
        if context.frequency_profile == "low":
            negative_keywords.extend(["单层普通玻璃", "推拉窗优先"])
        if context.preferred_solution == "add_inner_window":
            negative_keywords.append("整窗强制更换")
        return negative_keywords

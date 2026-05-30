# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 16:13:50 CST

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ShoppingSearchIntent(BaseModel):
    """购物搜索意图。

    这是咨询模块与购物模块之间的桥。咨询系统先输出结构化搜索意图，
    后续浏览器执行器只消费这个对象，不直接依赖自由文本。
    """

    scene: str = Field(description="用户场景摘要，例如：高架低频卧室、地铁儿童房")
    budget_level: Literal["low", "medium", "high"]
    solution_type: Literal["replace_window", "add_inner_window", "both_possible"]
    primary_keywords: list[str] = Field(default_factory=list)
    negative_keywords: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ListingProduct(BaseModel):
    """列表页商品最小结构。"""

    platform: Literal["taobao", "pinduoduo"] = "taobao"
    title: str
    price_text: str | None = None
    sales_text: str | None = None
    shop_name: str | None = None
    detail_url: str | None = None
    source_rank: int | None = None


class RejectedListingProduct(BaseModel):
    """被过滤掉的列表页候选。"""

    title: str
    detail_url: str | None = None
    reason: str
    source_rank: int | None = None


class ProductDetail(BaseModel):
    """详情页标准化结构。

    V1 先按‘对比决策够用’的粒度设计，不追求把淘宝所有字段都抓全。
    """

    platform: Literal["taobao", "pinduoduo"] = "taobao"
    title: str
    price_text: str | None = None
    coupon_price_text: str | None = None
    shop_name: str | None = None
    detail_url: str | None = None
    glass_spec: str | None = None
    frame_spec: str | None = None
    seal_spec: str | None = None
    hardware_keyword: str | None = None
    installation_services: list[str] = Field(default_factory=list)
    extracted_keywords: list[str] = Field(default_factory=list)
    raw_spec_text: str | None = None
    risk_flags: list[str] = Field(default_factory=list)
    ranking_score: float | None = None
    ranking_reasons: list[str] = Field(default_factory=list)
    review_sample_count: int = 0
    review_effective_count: int = 0
    review_highlights: list[str] = Field(default_factory=list)
    review_risk_flags: list[str] = Field(default_factory=list)


class ProductComparisonSummary(BaseModel):
    """商品对比总结结构。"""

    recommended_option: str
    reason_summary: str
    risk_points: list[str] = Field(default_factory=list)
    search_refinement: list[str] = Field(default_factory=list)


class WorkflowStepTrace(BaseModel):
    """一次购物工作流中的单步执行记录。"""

    step: str
    status: Literal["ok", "skipped", "error"] = "ok"
    duration_ms: int = 0
    notes: list[str] = Field(default_factory=list)


class ShoppingSessionSnapshot(BaseModel):
    """一次购物检索过程的快照。"""

    run_id: str | None = None
    search_intent: ShoppingSearchIntent
    search_query: str
    listing_products: list[ListingProduct] = Field(default_factory=list)
    filtered_out_products: list[RejectedListingProduct] = Field(default_factory=list)
    detailed_products: list[ProductDetail] = Field(default_factory=list)
    comparison_summary: ProductComparisonSummary | None = None
    workflow_notes: list[str] = Field(default_factory=list)
    artifact_names: list[str] = Field(default_factory=list)
    step_traces: list[WorkflowStepTrace] = Field(default_factory=list)

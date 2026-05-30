# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 20:23:45 CST

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from shopping.schemas import (
    ListingProduct,
    ProductComparisonSummary,
    ProductDetail,
    RejectedListingProduct,
    ShoppingSearchIntent,
    ShoppingSessionSnapshot,
    WorkflowStepTrace,
)


class RawCaptureArtifact(BaseModel):
    """原始抓取证据。"""

    artifact_type: Literal["html", "screenshot", "json", "text"]
    relative_path: str | None = None
    inline_text: str | None = None


class ProductCacheEntry(BaseModel):
    """单个商品缓存条目。"""

    cache_id: str
    platform: Literal["taobao", "pinduoduo"] = "taobao"
    search_query: str
    listing: ListingProduct | None = None
    detail: ProductDetail | None = None
    artifacts: list[RawCaptureArtifact] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class ShoppingRunCache(BaseModel):
    """一次购物搜索运行的缓存快照。"""

    run_id: str
    platform: Literal["taobao", "pinduoduo"] = "taobao"
    search_query: str
    search_intent: ShoppingSearchIntent
    entries: list[ProductCacheEntry] = Field(default_factory=list)
    filtered_out_products: list[RejectedListingProduct] = Field(default_factory=list)
    summary: ProductComparisonSummary | None = None
    artifact_names: list[str] = Field(default_factory=list)
    workflow_notes: list[str] = Field(default_factory=list)
    step_traces: list[WorkflowStepTrace] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)

    def to_snapshot(self) -> ShoppingSessionSnapshot:
        """把缓存快照转回工作流快照。"""

        return ShoppingSessionSnapshot(
            run_id=self.run_id,
            search_intent=self.search_intent,
            search_query=self.search_query,
            listing_products=[entry.listing for entry in self.entries if entry.listing is not None],
            filtered_out_products=self.filtered_out_products,
            detailed_products=[entry.detail for entry in self.entries if entry.detail is not None],
            comparison_summary=self.summary,
            workflow_notes=self.workflow_notes,
            artifact_names=self.artifact_names,
            step_traces=self.step_traces,
        )

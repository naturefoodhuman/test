# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 21:13:05 CST

from __future__ import annotations

from pydantic import BaseModel, Field


class RawReview(BaseModel):
    """原始评论结构。

    当前先定义为平台无关模型，后续接淘宝评论抓取时统一映射到这里。
    """

    review_id: str | None = None
    rating: int | None = None
    content: str
    created_at: str | None = None
    sku_text: str | None = None
    image_count: int = 0
    is_anonymous: bool = False


class ReviewJudgement(BaseModel):
    """单条评论的有效性判定结果。"""

    effective: bool
    suspected_brushed: bool
    confidence_score: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    extracted_signals: list[str] = Field(default_factory=list)


class ReviewAuditSummary(BaseModel):
    """评论审查汇总结果。"""

    total_reviews: int = 0
    effective_reviews: int = 0
    suspected_brushed_reviews: int = 0
    neutral_reviews: int = 0
    highlights: list[str] = Field(default_factory=list)
    lowlights: list[str] = Field(default_factory=list)
    risk_notes: list[str] = Field(default_factory=list)

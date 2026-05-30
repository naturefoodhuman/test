# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 12:48:24 CST

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Phase0Case(BaseModel):
    """单条评测样例。"""

    id: str
    task_type: str
    title: str
    prompt: str
    expect_json: bool = True
    json_schema: dict[str, Any] | None = None
    expected_keywords: list[str] = Field(default_factory=list)
    forbidden_keywords: list[str] = Field(default_factory=list)
    notes: str = ""


class ScoreBreakdown(BaseModel):
    """单条样例评分结果。"""

    parse_success: float = 0.0
    required_fields: float = 0.0
    keyword_coverage: float = 0.0
    forbidden_penalty: float = 0.0
    total_score: float = 0.0
    comments: list[str] = Field(default_factory=list)


class GenerationRecord(BaseModel):
    """单模型单样例的原始记录。"""

    model_name: str
    case_id: str
    task_type: str
    raw_output: str
    parsed_output: dict[str, Any] | list[Any] | None = None
    score: ScoreBreakdown


class ModelSummary(BaseModel):
    """单模型汇总。"""

    model_name: str
    case_count: int
    average_score: float
    parse_success_rate: float


class Phase0Result(BaseModel):
    """Phase 0 完整结果。"""

    generated_at: str
    summaries: list[ModelSummary]
    records: list[GenerationRecord]

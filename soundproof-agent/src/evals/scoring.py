# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 12:48:24 CST

from __future__ import annotations

import json
from typing import Any

from evals.models import Phase0Case, ScoreBreakdown


def _safe_parse_json(raw_output: str) -> dict[str, Any] | list[Any] | None:
    """尽量把模型输出解析为 JSON。"""

    text = raw_output.strip()
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 兼容模型把 JSON 包在 Markdown 代码块里的常见情况。
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None


def _required_fields_score(case: Phase0Case, parsed_output: dict[str, Any] | list[Any] | None) -> tuple[float, list[str]]:
    """根据 JSON Schema 的 required 字段做一个轻量打分。"""

    comments: list[str] = []
    if not case.json_schema or not isinstance(parsed_output, dict):
        return 1.0, comments

    required_fields = case.json_schema.get("required", [])
    if not required_fields:
        return 1.0, comments

    hit_count = 0
    for field_name in required_fields:
        if field_name in parsed_output and parsed_output[field_name] not in (None, "", [], {}):
            hit_count += 1
        else:
            comments.append(f"缺少必填字段：{field_name}")

    return hit_count / len(required_fields), comments


def _keyword_score(case: Phase0Case, raw_output: str) -> tuple[float, float, list[str]]:
    """根据预期关键词与禁用关键词进行启发式打分。"""

    comments: list[str] = []
    normalized = raw_output.lower()

    if case.expected_keywords:
        hit = sum(1 for keyword in case.expected_keywords if keyword.lower() in normalized)
        coverage = hit / len(case.expected_keywords)
    else:
        coverage = 1.0

    penalty_count = sum(1 for keyword in case.forbidden_keywords if keyword.lower() in normalized)
    penalty = min(0.5, penalty_count * 0.1)
    if penalty_count:
        comments.append(f"命中禁用关键词 {penalty_count} 次")

    return coverage, penalty, comments


def score_case(case: Phase0Case, raw_output: str) -> tuple[dict[str, Any] | list[Any] | None, ScoreBreakdown]:
    """对单条样例打分。

    这是一个“Phase 0 可用”的轻量评分器，不追求替代人工评审，目的是先帮我们快速筛模型。
    """

    parsed_output = _safe_parse_json(raw_output) if case.expect_json else None
    parse_success = 1.0 if (not case.expect_json or parsed_output is not None) else 0.0

    required_fields_score, field_comments = _required_fields_score(case, parsed_output)
    keyword_coverage, forbidden_penalty, keyword_comments = _keyword_score(case, raw_output)

    total_score = (
        parse_success * 0.35
        + required_fields_score * 0.35
        + keyword_coverage * 0.30
        - forbidden_penalty
    )
    total_score = max(0.0, round(total_score, 4))

    score = ScoreBreakdown(
        parse_success=parse_success,
        required_fields=round(required_fields_score, 4),
        keyword_coverage=round(keyword_coverage, 4),
        forbidden_penalty=round(forbidden_penalty, 4),
        total_score=total_score,
        comments=[*field_comments, *keyword_comments],
    )
    return parsed_output, score

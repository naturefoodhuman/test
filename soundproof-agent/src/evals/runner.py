# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 12:48:24 CST

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from config import RuntimeConfig
from evals.models import GenerationRecord, ModelSummary, Phase0Case, Phase0Result
from evals.scoring import score_case
from utils.ollama_client import OllamaClient


def load_cases(case_file: str | Path) -> list[Phase0Case]:
    """加载 JSON 评测样例。"""

    path = Path(case_file)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Phase0Case.model_validate(item) for item in raw]


def build_model_prompt(case: Phase0Case) -> str:
    """构造发给模型的最终提示词。

    这里把“必须输出 JSON”写得比较死，是为了尽量提高 Phase 0 的可比较性。
    """

    prompt_parts = [
        "你正在参加一个真实产品的 Phase 0 模型评测。",
        "请严格按要求回答，不要输出无关寒暄。",
        case.prompt.strip(),
    ]
    if case.expect_json and case.json_schema:
        prompt_parts.append(
            "请直接输出 JSON，不要包裹 Markdown 代码块。JSON Schema 如下：\n"
            f"{json.dumps(case.json_schema, ensure_ascii=False, indent=2)}"
        )
    return "\n\n".join(prompt_parts)


def generate_markdown_report(result: Phase0Result) -> str:
    """生成便于人工查看的 Markdown 结果摘要。"""

    lines = [
        "# Phase 0 评测结果",
        "",
        f"- 生成时间：{result.generated_at}",
        f"- 参评模型数：{len(result.summaries)}",
        f"- 样例总数：{len(result.records)}",
        "",
        "## 模型排名",
        "",
        "| 排名 | 模型 | 平均分 | JSON 解析成功率 | 样例数 |",
        "|---|---|---:|---:|---:|",
    ]

    for index, summary in enumerate(sorted(result.summaries, key=lambda item: item.average_score, reverse=True), start=1):
        lines.append(
            f"| {index} | {summary.model_name} | {summary.average_score:.4f} | {summary.parse_success_rate:.2%} | {summary.case_count} |"
        )

    lines.extend(["", "## 逐条记录", ""])
    for record in result.records:
        lines.extend(
            [
                f"### {record.model_name} / {record.case_id}",
                f"- 任务类型：{record.task_type}",
                f"- 总分：{record.score.total_score:.4f}",
                f"- 备注：{'；'.join(record.score.comments) if record.score.comments else '无'}",
                "",
                "```json",
                json.dumps(record.parsed_output, ensure_ascii=False, indent=2) if record.parsed_output is not None else record.raw_output,
                "```",
                "",
            ]
        )

    return "\n".join(lines)


def run_phase0_evaluation(project_root: str | Path, config: RuntimeConfig) -> Path:
    """执行 Phase 0 全量评测，并把结果写入磁盘。"""

    project_root_path = Path(project_root)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root_path / config.phase0.output_root / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    client = OllamaClient(
        base_url=config.phase0.ollama.base_url,
        timeout_seconds=config.phase0.timeout_seconds,
    )

    all_cases: list[Phase0Case] = []
    for _, relative_case_path in config.phase0.case_files.items():
        all_cases.extend(load_cases(project_root_path / relative_case_path))

    records: list[GenerationRecord] = []
    for candidate in config.phase0.candidates:
        if not candidate.enabled:
            continue

        for case in all_cases:
            prompt = build_model_prompt(case)
            raw_output = client.chat(
                model=candidate.name,
                prompt=prompt,
                temperature=candidate.temperature,
                format_schema=case.json_schema if case.expect_json else None,
            )
            parsed_output, score = score_case(case, raw_output)
            records.append(
                GenerationRecord(
                    model_name=candidate.name,
                    case_id=case.id,
                    task_type=case.task_type,
                    raw_output=raw_output,
                    parsed_output=parsed_output,
                    score=score,
                )
            )

    grouped_scores: dict[str, list[GenerationRecord]] = defaultdict(list)
    for record in records:
        grouped_scores[record.model_name].append(record)

    summaries: list[ModelSummary] = []
    for model_name, model_records in grouped_scores.items():
        average_score = sum(item.score.total_score for item in model_records) / len(model_records)
        parse_success_rate = sum(item.score.parse_success for item in model_records) / len(model_records)
        summaries.append(
            ModelSummary(
                model_name=model_name,
                case_count=len(model_records),
                average_score=round(average_score, 4),
                parse_success_rate=round(parse_success_rate, 4),
            )
        )

    result = Phase0Result(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        summaries=sorted(summaries, key=lambda item: item.average_score, reverse=True),
        records=records,
    )

    (output_dir / "results.json").write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8",
    )
    (output_dir / "report.md").write_text(
        generate_markdown_report(result),
        encoding="utf-8",
    )
    return output_dir

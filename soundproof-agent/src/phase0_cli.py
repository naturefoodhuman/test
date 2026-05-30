# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 13:50:28 CST

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print

from config import load_runtime_config
from utils.preflight import run_preflight_check

app = typer.Typer(help="Phase 0 模型评测命令行工具。")


@app.command("show-config")
def show_config(config_path: str = "config.yaml") -> None:
    """显示当前 Phase 0 配置。"""

    config = load_runtime_config(config_path)
    print(json.dumps(config.model_dump(), ensure_ascii=False, indent=2))


@app.command("preflight")
def preflight(config_path: str = "config.yaml") -> None:
    """执行 Phase 0 启动前检查。"""

    config = load_runtime_config(config_path)
    result = run_preflight_check(config.phase0.ollama.base_url)
    print(json.dumps(result, ensure_ascii=False, indent=2))


@app.command("evaluate")
def evaluate(project_root: str = ".", config_path: str = "config.yaml") -> None:
    """运行全量 Phase 0 评测。"""

    from evals.runner import run_phase0_evaluation

    root = Path(project_root).resolve()
    config = load_runtime_config(root / config_path)
    output_dir = run_phase0_evaluation(root, config)
    print(f"[green]Phase 0 评测完成，结果目录：{output_dir}[/green]")


if __name__ == "__main__":
    app()

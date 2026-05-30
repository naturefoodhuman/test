# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 14:02:18 CST

from __future__ import annotations

from pathlib import Path
from typing import Any


def list_artifacts(artifact_root: str | Path, prefix: str | None = None) -> list[str]:
    """列出调试产物文件。"""

    root = Path(artifact_root)
    if not root.exists():
        return []

    files = [item for item in root.iterdir() if item.is_file()]
    if prefix:
        files = [item for item in files if item.name.startswith(prefix)]
    files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return [item.name for item in files]


def list_artifacts_for_run(artifact_root: str | Path, run_id: str) -> list[str]:
    """列出某个 run_id 关联的产物。"""

    return list_artifacts(artifact_root, prefix=f"{run_id}_")


def read_artifact_text(artifact_root: str | Path, name: str) -> str | None:
    """读取某个调试产物文本内容。"""

    file_path = Path(artifact_root) / name
    if not file_path.exists() or not file_path.is_file():
        return None
    return file_path.read_text(encoding="utf-8")


def artifact_exists(artifact_root: str | Path, name: str) -> bool:
    """判断某个 artifact 是否存在。"""

    file_path = Path(artifact_root) / name
    return file_path.exists() and file_path.is_file()


def build_artifact_manifest(artifact_root: str | Path, artifact_names: list[str]) -> list[dict[str, Any]]:
    """为一组 artifact 生成清单。"""

    root = Path(artifact_root)
    manifest: list[dict[str, Any]] = []
    for name in artifact_names:
        file_path = root / name
        if not file_path.exists() or not file_path.is_file():
            continue
        stat = file_path.stat()
        manifest.append(
            {
                "name": name,
                "size_bytes": stat.st_size,
                "modified_time": stat.st_mtime,
            }
        )
    return manifest

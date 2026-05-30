# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 02:53:27 CST

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from shopping.selector_loader import export_default_selector_profile, load_taobao_selector_profile
from shopping.selector_profiles import TAOBAO_SELECTOR_PROFILE


def read_selector_override_text(path: str | Path) -> str | None:
    """读取 selector override 文本。"""

    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return None
    return file_path.read_text(encoding="utf-8")


def write_selector_override_text(path: str | Path, content: str) -> Path:
    """写入 selector override 文本。"""

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def reset_selector_override_to_default(path: str | Path) -> Path:
    """把 selector override 重置为默认模板。"""

    return export_default_selector_profile(path)


def backup_selector_override(path: str | Path) -> Path | None:
    """备份现有 selector override 文件。"""

    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return None

    backup_dir = file_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix or '.yaml'}"
    backup_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def validate_selector_override(path: str | Path) -> dict[str, Any]:
    """校验 selector override 文件是否有效。"""

    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return {
            "exists": False,
            "valid": False,
            "errors": ["selector override 文件不存在"],
        }

    raw_text = file_path.read_text(encoding="utf-8")
    try:
        parsed = yaml.safe_load(raw_text) or {}
    except yaml.YAMLError as exc:
        return {
            "exists": True,
            "valid": False,
            "errors": [f"YAML 解析失败：{exc}"],
        }

    try:
        profile = load_taobao_selector_profile(file_path)
    except ValidationError as exc:
        return {
            "exists": True,
            "valid": False,
            "errors": [f"选择器结构校验失败：{exc}"],
        }

    return {
        "exists": True,
        "valid": True,
        "errors": [],
        "keys": list(parsed.keys()) if isinstance(parsed, dict) else [],
        "selector_summary": {
            "search_card_candidates": len(profile.search.card_candidates),
            "detail_title_selectors": len(profile.detail.title_selectors),
            "detail_shop_selectors": len(profile.detail.shop_name_selectors),
            "detail_price_selectors": len(profile.detail.price_selectors),
            "review_tab_selectors": len(profile.review.review_tab_selectors),
        },
    }


def build_selector_override_diff(path: str | Path) -> dict[str, Any]:
    """构建当前 override 与默认配置的差异摘要。"""

    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return {"exists": False, "changed_fields": []}

    current = load_taobao_selector_profile(file_path).model_dump()
    default = TAOBAO_SELECTOR_PROFILE.model_dump()
    changed_fields: list[str] = []
    _collect_diffs(default, current, prefix="", output=changed_fields)
    return {
        "exists": True,
        "changed_fields": changed_fields,
        "changed_count": len(changed_fields),
    }


def _collect_diffs(base: Any, current: Any, *, prefix: str, output: list[str]) -> None:
    """递归收集差异路径。"""

    if isinstance(base, dict) and isinstance(current, dict):
        for key in base.keys() | current.keys():
            next_prefix = f"{prefix}.{key}" if prefix else key
            _collect_diffs(base.get(key), current.get(key), prefix=next_prefix, output=output)
        return
    if base != current:
        output.append(prefix)


def list_selector_override_backups(path: str | Path, limit: int = 20) -> list[str]:
    """列出 selector override 备份文件。"""

    file_path = Path(path)
    backup_dir = file_path.parent / "backups"
    if not backup_dir.exists() or not backup_dir.is_dir():
        return []

    files = [item for item in backup_dir.iterdir() if item.is_file()]
    files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return [item.name for item in files[:limit]]


def read_selector_override_backup(path: str | Path, backup_name: str) -> str | None:
    """读取某个备份文件内容。"""

    file_path = Path(path)
    backup_path = file_path.parent / "backups" / backup_name
    if not backup_path.exists() or not backup_path.is_file():
        return None
    return backup_path.read_text(encoding="utf-8")


def restore_selector_override_backup(path: str | Path, backup_name: str) -> Path | None:
    """从备份恢复 selector override 文件。"""

    file_path = Path(path)
    backup_path = file_path.parent / "backups" / backup_name
    if not backup_path.exists() or not backup_path.is_file():
        return None

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")
    return file_path

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 01:18:32 CST

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from shopping.selector_profiles import TAOBAO_SELECTOR_PROFILE, TaobaoSelectorProfile


def load_taobao_selector_profile(override_path: str | Path | None = None) -> TaobaoSelectorProfile:
    """加载淘宝选择器配置，支持用 YAML 覆盖默认值。"""

    if override_path is None:
        return TAOBAO_SELECTOR_PROFILE

    path = Path(override_path)
    if not path.exists() or not path.is_file():
        return TAOBAO_SELECTOR_PROFILE

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    base = TAOBAO_SELECTOR_PROFILE.model_dump()
    merged = _deep_merge(base, raw)
    return TaobaoSelectorProfile.model_validate(merged)


def export_default_selector_profile(output_path: str | Path) -> Path:
    """导出默认选择器配置模板。"""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = TAOBAO_SELECTOR_PROFILE.model_dump()
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return path


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """递归合并字典。"""

    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def dump_default_selector_profile_yaml() -> str:
    """以 YAML 字符串形式返回默认 selector profile。"""

    payload = TAOBAO_SELECTOR_PROFILE.model_dump()
    return yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 23:00:19 CST

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from config import ShoppingRuntimeConfig
from shopping.profile_manager import BrowserProfileManager


def run_phase1_preflight(project_root: str | Path, runtime_config: ShoppingRuntimeConfig) -> dict[str, Any]:
    """执行 Phase 1 运行前检查。"""

    manager = BrowserProfileManager(runtime_config, project_root)
    manager.ensure_directories()

    playwright_installed = importlib.util.find_spec("playwright") is not None

    return {
        "platform": runtime_config.platform,
        "headed": runtime_config.headed,
        "allow_login_reuse": runtime_config.allow_login_reuse,
        "profile_root": str(manager.profile_root),
        "artifact_root": str(manager.artifact_root),
        "cache_db_path": str(manager.cache_db_path),
        "playwright_installed": playwright_installed,
        "profile_ready": manager.is_platform_profile_ready(runtime_config.platform),
        "notes": [
            "真实淘宝抓取前请确认已安装 Playwright 与 Chromium。",
            "首次运行真实抓取前，请准备淘宝测试账号并人工扫码登录。",
        ],
    }

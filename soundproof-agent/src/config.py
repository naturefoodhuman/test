# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 01:18:32 CST

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class CandidateModelConfig(BaseModel):
    """Phase 0 候选模型配置。"""

    name: str
    enabled: bool = True
    temperature: float = 0.2
    role_hints: list[str] = Field(default_factory=list)


class OllamaConfig(BaseModel):
    """Ollama 或兼容服务配置。"""

    base_url: str = "http://localhost:11434"


class Phase0Config(BaseModel):
    """Phase 0 运行配置。"""

    output_root: str = "phase0_outputs"
    timeout_seconds: int = 180
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    candidates: list[CandidateModelConfig] = Field(default_factory=list)
    case_files: dict[Literal["coordinator", "noise_analysis", "shopping_extract", "shopping_summary"], str]


class ShoppingReviewConfig(BaseModel):
    """评论增强配置。"""

    enabled: bool = True
    top_n: int = 3
    fetch_limit_per_product: int = 8


class ShoppingAntiBotConfig(BaseModel):
    """购物反爬与节流配置。"""

    max_detail_pages_per_run: int = 5
    max_searches_per_hour: int = 20
    max_review_fetches_per_run: int = 3
    base_delay_seconds: float = 2.5
    enforce_delay: bool = False


class ShoppingRuntimeConfig(BaseModel):
    """Phase 1 购物模块运行配置。"""

    platform: Literal["taobao", "pinduoduo"] = "taobao"
    browser_profile_root: str = "runtime/browser_profiles"
    artifact_root: str = "runtime/artifacts"
    cache_db_path: str = "runtime/cache/shopping_cache.sqlite3"
    selector_override_path: str = "runtime/selector_overrides.yaml"
    default_search_limit: int = 5
    headed: bool = True
    allow_login_reuse: bool = True
    reviews: ShoppingReviewConfig = Field(default_factory=ShoppingReviewConfig)
    anti_bot: ShoppingAntiBotConfig = Field(default_factory=ShoppingAntiBotConfig)


class Phase1Config(BaseModel):
    """Phase 1 运行配置。"""

    shopping: ShoppingRuntimeConfig = Field(default_factory=ShoppingRuntimeConfig)


class RuntimeConfig(BaseModel):
    """项目运行时配置。"""

    phase0: Phase0Config
    phase1: Phase1Config = Field(default_factory=Phase1Config)


def load_runtime_config(config_path: str | Path = "config.yaml") -> RuntimeConfig:
    """加载 YAML 配置，并叠加环境变量覆盖。"""

    path = Path(config_path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    config = RuntimeConfig.model_validate(raw)

    env_base_url = os.getenv("OLLAMA_BASE_URL")
    env_output_root = os.getenv("PHASE0_OUTPUT_ROOT")
    env_timeout = os.getenv("PHASE0_TIMEOUT_SECONDS")
    env_profile_root = os.getenv("SHOPPING_BROWSER_PROFILE_ROOT")
    env_artifact_root = os.getenv("SHOPPING_ARTIFACT_ROOT")
    env_cache_db_path = os.getenv("SHOPPING_CACHE_DB_PATH")
    env_selector_override_path = os.getenv("SHOPPING_SELECTOR_OVERRIDE_PATH")

    if env_base_url:
        config.phase0.ollama.base_url = env_base_url
    if env_output_root:
        config.phase0.output_root = env_output_root
    if env_timeout and env_timeout.isdigit():
        config.phase0.timeout_seconds = int(env_timeout)
    if env_profile_root:
        config.phase1.shopping.browser_profile_root = env_profile_root
    if env_artifact_root:
        config.phase1.shopping.artifact_root = env_artifact_root
    if env_cache_db_path:
        config.phase1.shopping.cache_db_path = env_cache_db_path
    if env_selector_override_path:
        config.phase1.shopping.selector_override_path = env_selector_override_path

    return config

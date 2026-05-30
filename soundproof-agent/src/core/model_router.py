# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 22:10:40 CST

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class RouteSpec(BaseModel):
    """单个角色的模型路由配置。"""

    primary: str
    fallback: str | None = None
    escalation: str | None = None
    note: str | None = None
    basis: str | None = None


class ModelRouter(BaseModel):
    """模型路由配置。"""

    status: str
    principles: list[str] = Field(default_factory=list)
    routes: dict[str, RouteSpec] = Field(default_factory=dict)

    def get_primary(self, route_name: str) -> str:
        """获取某角色的主模型。"""

        return self.routes[route_name].primary

    def get_fallback(self, route_name: str) -> str | None:
        """获取某角色的备用模型。"""

        return self.routes[route_name].fallback


def load_model_router(router_path: str | Path = "model_router.yaml") -> ModelRouter:
    """加载模型路由配置。"""

    path = Path(router_path)
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ModelRouter.model_validate(raw)

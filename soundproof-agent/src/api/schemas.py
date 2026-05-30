# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 02:46:11 CST

from __future__ import annotations

from pydantic import BaseModel, Field

from shopping.intent_builder import ConsultationContext


class BaseShoppingRunRequest(BaseModel):
    """购物运行请求基类。"""

    scene: str = Field(default="高架低频卧室")
    budget: int = Field(default=8000)
    noise_source: str = Field(default="traffic")
    frequency_profile: str = Field(default="low")
    preferred_solution: str = Field(default="replace_window")
    room_type: str = Field(default="卧室")
    limit: int = Field(default=5)

    def to_consultation_context(self) -> ConsultationContext:
        """转为咨询上下文。"""

        return ConsultationContext(
            scene=self.scene,
            budget=self.budget,
            noise_source=self.noise_source,
            frequency_profile=self.frequency_profile,
            preferred_solution=self.preferred_solution,
            room_type=self.room_type,
        )


class ReplayRunRequest(BaseShoppingRunRequest):
    """离线回放请求。"""


class LiveRunRequest(BaseShoppingRunRequest):
    """真实购物运行请求。"""


class SearchOnceRequest(BaseModel):
    """真实搜索一次请求。"""

    query: str
    limit: int = Field(default=5)


class DetailOnceRequest(BaseModel):
    """真实详情抓取请求。"""

    title: str
    detail_url: str
    price_text: str | None = None
    shop_name: str | None = None
    normalize_with_llm: bool = True


class ProbeDetailRequest(BaseModel):
    """详情页探针请求。"""

    detail_url: str
    wait_after_load_ms: int = Field(default=3000)


class SearchProbeRequest(BaseModel):
    """搜索页探针请求。"""

    query: str
    wait_after_load_ms: int = Field(default=3000)


class SelectorOverrideSaveRequest(BaseModel):
    """selector override 保存请求。"""

    content: str
    backup: bool = True


class SelectorBackupActionRequest(BaseModel):
    """selector 备份操作请求。"""

    backup_name: str


class ReviewProbeRequest(BaseModel):
    """评论探针请求。"""

    title: str
    detail_url: str
    limit: int = Field(default=10)


class FullProbeRequest(BaseModel):
    """全链路联调探针请求。"""

    query: str
    title: str
    detail_url: str
    wait_after_load_ms: int = Field(default=3000)
    review_limit: int = Field(default=10)

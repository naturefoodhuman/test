# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 23:56:44 CST

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from shopping.schemas import ListingProduct, ProductDetail


class ShoppingExecutor(ABC):
    """购物执行器抽象接口。

    Phase 1 先定义稳定接口，后续再分别实现：
    - 真实淘宝 Playwright 执行器
    - 调试用本地 HTML 回放执行器
    """

    def start_run_context(self, run_id: str, search_query: str) -> None:
        """开始一次运行上下文。

        默认实现为空，具体执行器可覆写，用于：
        - 为 artifact 增加 run 前缀
        - 记录本轮搜索词
        """

    def end_run_context(self) -> None:
        """结束一次运行上下文。"""

    def get_recent_artifact_names(self) -> list[str]:
        """返回当前运行收集到的 artifact 名称。"""

        return []

    @abstractmethod
    def ensure_session(self) -> bool:
        """确保浏览器会话可用。"""

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> list[ListingProduct]:
        """执行商品搜索并返回列表页候选。"""

    @abstractmethod
    def fetch_detail(self, product: ListingProduct) -> ProductDetail:
        """抓取单个商品详情。"""

    @abstractmethod
    def save_debug_artifact(self, name: str, content: str) -> Path:
        """保存调试证据，如 HTML 或文本快照。"""

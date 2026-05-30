# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 23:56:44 CST

from __future__ import annotations

import json
from pathlib import Path

from shopping.executor_interface import ShoppingExecutor
from shopping.schemas import ListingProduct, ProductDetail


class ReplayShoppingExecutor(ShoppingExecutor):
    """本地回放执行器。"""

    def __init__(self, fixture_root: str | Path) -> None:
        self.fixture_root = Path(fixture_root)
        self.fixture_root.mkdir(parents=True, exist_ok=True)
        self._current_run_id: str | None = None
        self._recent_artifacts: list[str] = []

    def start_run_context(self, run_id: str, search_query: str) -> None:
        """开始一次运行上下文。"""

        self._current_run_id = run_id
        self._recent_artifacts = []

    def end_run_context(self) -> None:
        """结束一次运行上下文。"""

        self._current_run_id = None

    def get_recent_artifact_names(self) -> list[str]:
        """返回当前运行收集到的 artifact 名称。"""

        return list(self._recent_artifacts)

    def ensure_session(self) -> bool:
        """回放模式下默认始终可用。"""

        return True

    def search(self, query: str, limit: int = 5) -> list[ListingProduct]:
        """读取固定列表页 fixtures。"""

        payload = json.loads((self.fixture_root / "listing_products.json").read_text(encoding="utf-8"))
        products = [ListingProduct.model_validate(item) for item in payload]
        return products[:limit]

    def fetch_detail(self, product: ListingProduct) -> ProductDetail:
        """按标题 slug 读取详情 fixture。"""

        safe_name = product.title.replace("/", "_").replace(" ", "_")
        detail_file = self.fixture_root / f"detail_{safe_name}.json"
        payload = json.loads(detail_file.read_text(encoding="utf-8"))
        return ProductDetail.model_validate(payload)

    def save_debug_artifact(self, name: str, content: str) -> Path:
        """保存回放调试文件。"""

        final_name = self._build_name(name)
        file_path = self.fixture_root / final_name
        file_path.write_text(content, encoding="utf-8")
        self._recent_artifacts.append(final_name)
        return file_path

    def _build_name(self, name: str) -> str:
        """构造带 run_id 的 artifact 名称。"""

        if not self._current_run_id:
            return name
        return f"{self._current_run_id}_{name}"

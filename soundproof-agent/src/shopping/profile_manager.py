# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 22:10:40 CST

from __future__ import annotations

from pathlib import Path

from config import ShoppingRuntimeConfig


class BrowserProfileManager:
    """浏览器 profile 管理器。

    V1 购物模块依赖“人工扫码一次 + 本地复用登录态”。
    这个类先把路径与目录约束统一起来，后续再接具体浏览器逻辑。
    """

    def __init__(self, runtime_config: ShoppingRuntimeConfig, project_root: str | Path) -> None:
        self.runtime_config = runtime_config
        self.project_root = Path(project_root)

    @property
    def profile_root(self) -> Path:
        """浏览器 profile 根目录。"""

        return self.project_root / self.runtime_config.browser_profile_root

    @property
    def artifact_root(self) -> Path:
        """调试产物目录。"""

        return self.project_root / self.runtime_config.artifact_root

    @property
    def cache_db_path(self) -> Path:
        """SQLite 缓存文件路径。"""

        return self.project_root / self.runtime_config.cache_db_path

    def ensure_directories(self) -> None:
        """确保运行目录存在。"""

        self.profile_root.mkdir(parents=True, exist_ok=True)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_platform_profile_dir(self, platform: str) -> Path:
        """获取平台 profile 目录。"""

        return self.profile_root / platform

    def is_platform_profile_ready(self, platform: str) -> bool:
        """判断某平台 profile 是否已建立。"""

        return self.get_platform_profile_dir(platform).exists()

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 01:18:32 CST

from __future__ import annotations

from pathlib import Path

from config import RuntimeConfig, load_runtime_config
from core.model_router import ModelRouter, load_model_router
from security.anti_bot_policy import ShoppingAntiBotPolicy
from shopping.llm_services import ShoppingFieldNormalizerService, ShoppingSummaryService
from shopping.playwright_executor import TaobaoPlaywrightExecutor
from shopping.profile_manager import BrowserProfileManager
from shopping.review_enricher import ProductReviewEnricher
from shopping.review_fetcher import TaobaoPlaywrightReviewFetcher
from shopping.selector_loader import load_taobao_selector_profile
from shopping.sqlite_cache import ShoppingCacheStore
from utils.ollama_client import OllamaClient


class ShoppingRuntimeBundle:
    """购物模块运行时依赖集合。"""

    def __init__(
        self,
        *,
        project_root: Path,
        config: RuntimeConfig,
        router: ModelRouter,
        profile_manager: BrowserProfileManager,
        cache_store: ShoppingCacheStore,
        summary_service: ShoppingSummaryService,
        field_normalizer_service: ShoppingFieldNormalizerService,
        anti_bot_policy: ShoppingAntiBotPolicy,
        review_enricher: ProductReviewEnricher | None,
        selector_profile,
    ) -> None:
        self.project_root = project_root
        self.config = config
        self.router = router
        self.profile_manager = profile_manager
        self.cache_store = cache_store
        self.summary_service = summary_service
        self.field_normalizer_service = field_normalizer_service
        self.anti_bot_policy = anti_bot_policy
        self.review_enricher = review_enricher
        self.selector_profile = selector_profile


def build_shopping_runtime_bundle(project_root: str | Path, config_path: str | Path = "config.yaml") -> ShoppingRuntimeBundle:
    """构建购物模块运行时依赖集合。"""

    root = Path(project_root).resolve()
    config = load_runtime_config(root / config_path)
    router = load_model_router(root / "model_router.yaml")
    profile_manager = BrowserProfileManager(config.phase1.shopping, root)
    profile_manager.ensure_directories()

    cache_store = ShoppingCacheStore(profile_manager.cache_db_path)
    cache_store.initialize()

    client = OllamaClient(
        base_url=config.phase0.ollama.base_url,
        timeout_seconds=config.phase0.timeout_seconds,
    )
    summary_service = ShoppingSummaryService(
        client=client,
        model_name=router.get_primary("shopping_summary"),
        temperature=0.1,
    )
    field_normalizer_service = ShoppingFieldNormalizerService(
        client=client,
        model_name=router.get_primary("shopping_field_normalizer"),
        temperature=0.1,
    )
    selector_profile = load_taobao_selector_profile(root / config.phase1.shopping.selector_override_path)
    anti_bot_policy = ShoppingAntiBotPolicy(
        max_detail_pages_per_run=config.phase1.shopping.anti_bot.max_detail_pages_per_run,
        max_searches_per_hour=config.phase1.shopping.anti_bot.max_searches_per_hour,
        max_review_fetches_per_run=config.phase1.shopping.anti_bot.max_review_fetches_per_run,
        base_delay_seconds=config.phase1.shopping.anti_bot.base_delay_seconds,
    )

    review_enricher = None
    if config.phase1.shopping.reviews.enabled:
        review_executor = TaobaoPlaywrightExecutor(config.phase1.shopping, root)
        review_enricher = ProductReviewEnricher(
            TaobaoPlaywrightReviewFetcher(review_executor),
        )

    return ShoppingRuntimeBundle(
        project_root=root,
        config=config,
        router=router,
        profile_manager=profile_manager,
        cache_store=cache_store,
        summary_service=summary_service,
        field_normalizer_service=field_normalizer_service,
        anti_bot_policy=anti_bot_policy,
        review_enricher=review_enricher,
        selector_profile=selector_profile,
    )

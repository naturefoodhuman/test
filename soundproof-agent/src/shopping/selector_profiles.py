# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 17:30:00 CST

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchSelectorProfile(BaseModel):
    """列表页选择器配置。"""

    # 主选择器（优先级高）
    card_candidates: list[str] = Field(default_factory=list)
    # 备选选择器（回退用）
    card_fallbacks: list[str] = Field(default_factory=list)
    detail_link_patterns: list[str] = Field(default_factory=list)
    shop_name_text_signals: list[str] = Field(default_factory=list)


class DetailSelectorProfile(BaseModel):
    """详情页选择器配置。"""

    # 标题选择器
    title_selectors: list[str] = Field(default_factory=list)
    title_fallback: str = ""  # 回退到 page.title()
    # 备选标题选择器
    title_fallbacks: list[str] = Field(default_factory=list)
    # 店铺名选择器
    shop_name_selectors: list[str] = Field(default_factory=list)
    shop_name_fallback_pattern: str = ""  # 从 body 正则匹配店铺名
    # 备选店铺名选择器
    shop_name_fallbacks: list[str] = Field(default_factory=list)
    # 价格选择器
    price_selectors: list[str] = Field(default_factory=list)
    price_fallback_pattern: str = ""  # 从 body 正则匹配价格
    # 备选价格选择器
    price_fallbacks: list[str] = Field(default_factory=list)
    # 正文选择器
    body_selectors: list[str] = Field(default_factory=list)
    body_fallback_selectors: list[str] = Field(default_factory=list)


class ReviewSelectorProfile(BaseModel):
    """评论区域选择器配置。"""

    review_tab_selectors: list[str] = Field(default_factory=list)
    review_tab_fallbacks: list[str] = Field(default_factory=list)
    review_container_selectors: list[str] = Field(default_factory=list)
    review_container_fallbacks: list[str] = Field(default_factory=list)
    review_text_signals: list[str] = Field(default_factory=list)


class TaobaoSelectorProfile(BaseModel):
    """淘宝选择器总配置。"""

    search: SearchSelectorProfile
    detail: DetailSelectorProfile
    review: ReviewSelectorProfile


TAOBAO_SELECTOR_PROFILE = TaobaoSelectorProfile(
    search=SearchSelectorProfile(
        # 主选择器
        card_candidates=[
            'div[class*="Card"]',
            'div[class*="doubleCard"]',
            'div[data-index]',
            'div[class*="item"]',
        ],
        # 回退选择器（更通用）
        card_fallbacks=[
            'div[class*="pic"]',
            'div[class*="info"]',
            'li[class*="item"]',
            '.item',
            '[data-item-id]',
        ],
        detail_link_patterns=[
            'item.taobao.com',
            'detail.tmall.com',
            'item.htm',
        ],
        shop_name_text_signals=['店', '旗舰', '门窗', '官方'],
    ),
    detail=DetailSelectorProfile(
        # 标题选择器
        title_selectors=[
            'h1[class*="title"]',
            'h1[class*="Title"]',
            '[data-testid="itemTitle"]',
            '.tb-item-title h1',
            '#bd h1',
        ],
        title_fallback="page.title",
        title_fallbacks=[
            'h1',
            '[class*="title"]',
            '.tb-item-title',
        ],
        # 店铺名选择器
        shop_name_selectors=[
            '[class*="shop-name"]',
            '[class*="ShopName"]',
            '[class*="seller"]',
            'a[href*="shop"]:not([class*="logo"])',
            '.shop-name-text',
        ],
        shop_name_fallback_pattern=r"([\u4e00-\u9fa5]{2,20}(?:旗舰店|专营店|专卖店|官方店|店))",
        shop_name_fallbacks=[
            '[class*="shop"]',
            'a[href*="shop"]',
        ],
        # 价格选择器
        price_selectors=[
            '[class*="price"]',
            '[class*="Price"]',
            '[data-testid="price"]',
            '.tb-price',
            '#price',
        ],
        price_fallback_pattern=r"(\d+(?:\.\d+)?)\s*(?:元/㎡|/平米)",
        price_fallbacks=[
            '[class*="Price"]',
            '.price',
        ],
        # 正文选择器
        body_selectors=[
            '#J_DecorateDesc',
            '[class*="description"]',
            '[class*="detail"]',
            '#description',
        ],
        body_fallback_selectors=[
            '[class*="content"]',
            '[class*="main"]',
            'body',
        ],
    ),
    review=ReviewSelectorProfile(
        # 评论 Tab 选择器
        review_tab_selectors=[
            'text=评价',
            'text=全部评价',
            '#J_TabBar li:nth-child(2)',
        ],
        review_tab_fallbacks=[
            'a[href*="#description"]',
            'span:has-text("评价")',
            '[data-tab="reviews"]',
        ],
        # 评论容器选择器
        review_container_selectors=[
            '.tb-reviews-item',
            '[class*="review-item"]',
            '.rate-list .rate-item',
        ],
        review_container_fallbacks=[
            'div[class*="item"]',
            'li[class*="review"]',
            '.comment-list li',
        ],
        # 评论文本关键词（用于过滤有效评论）
        review_text_signals=['安装', '隔音', '玻璃', '密封', '噪音', '窗', '效果', '质量'],
    ),
)
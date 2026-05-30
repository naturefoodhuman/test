# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:28:41 CST

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def canonicalize_detail_url(url: str) -> str:
    """把商品详情页 URL 规范化，便于去重与缓存。

    当前策略：
    - 强制 https；
    - 去掉 fragment；
    - 只保留少数对详情页定位有意义的 query 参数；
    """

    parsed = urlparse(url)
    kept_keys = {"id", "skuId", "item_id"}
    kept_pairs = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key in kept_keys]
    normalized = parsed._replace(
        scheme="https",
        query=urlencode(kept_pairs),
        fragment="",
    )
    return urlunparse(normalized)

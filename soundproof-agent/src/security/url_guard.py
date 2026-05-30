# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:28:41 CST

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from shopping.errors import ShoppingExecutionError

_ALLOWED_HOST_SUFFIXES = (
    "taobao.com",
    "tmall.com",
)

_DANGEROUS_KEYWORDS = (
    "order",
    "cart",
    "pay",
    "payment",
    "favorite",
    "collect",
    "delete",
    "address",
)

_TRACKING_QUERY_KEYS = {
    "spm",
    "abbucket",
    "ns",
    "ut_sk",
    "trackid",
    "initiative_id",
    "clk1",
    "from",
    "sourceType",
    "scene",
    "broadcastType",
    "wh_pid",
    "wh_random_str",
}


def is_allowed_host(host: str | None) -> bool:
    """判断域名是否在允许范围内。"""

    if not host:
        return False
    normalized = host.lower()
    return any(normalized == suffix or normalized.endswith(f".{suffix}") for suffix in _ALLOWED_HOST_SUFFIXES)


def ensure_safe_readonly_url(url: str) -> str:
    """校验 URL 是否属于允许的只读页面。

    原则：
    - 仅允许 taobao / tmall 域名；
    - 拦截订单、支付、收藏等高风险路径或查询；
    - 返回标准化后的 URL，供执行器统一使用。
    """

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ShoppingExecutionError(f"不允许的 URL 协议：{parsed.scheme}")
    if not is_allowed_host(parsed.hostname):
        raise ShoppingExecutionError(f"不允许访问的域名：{parsed.hostname}")

    lowered = f"{parsed.path}?{parsed.query}".lower()
    if any(keyword in lowered for keyword in _DANGEROUS_KEYWORDS):
        raise ShoppingExecutionError("URL 命中高风险关键词，拒绝访问。")

    cleaned_query = _strip_tracking_query(parsed.query)
    normalized = parsed._replace(query=cleaned_query, fragment="")
    return urlunparse(normalized)


def _strip_tracking_query(query: str) -> str:
    """剥离明显的跟踪参数。"""

    if not query:
        return ""

    kept_pairs = []
    for key, value in parse_qsl(query, keep_blank_values=True):
        if key in _TRACKING_QUERY_KEYS:
            continue
        kept_pairs.append((key, value))
    return urlencode(kept_pairs)

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 17:30:00 CST

from __future__ import annotations

import re

_PRICE_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*元(?:/㎡|/平米|/平方|)")
_PRICE_ALT_PATTERN = re.compile(r"(?:价格|售价|价)[\s:：]*(\d+(?:\.\d+)?)\s*(?:元|¥)")
_SHOP_NAME_PATTERNS = [
    re.compile(r"([^\s]+(?:店|门窗|家居|建材)[^\s]*)"),
    re.compile(r"([\u4e00-\u9fa5]{2,20}(?:旗舰店|专营店|专卖店|官方店))"),
]
_TITLE_LENGTH_MIN = 8
_TITLE_LENGTH_MAX = 200


def choose_best_title(candidates: list[str], page_title: str | None = None) -> str | None:
    """从多个标题候选中挑选最可信的一项。"""

    normalized = _normalize_candidates(candidates)
    if normalized:
        # 标题通常是相对更长但不过分长的文本
        # 优先选择长度在合理范围内的候选
        valid_candidates = [c for c in normalized if _TITLE_LENGTH_MIN <= len(c) <= _TITLE_LENGTH_MAX]
        if valid_candidates:
            valid_candidates.sort(key=lambda item: len(item), reverse=True)
            return valid_candidates[0]
        # 如果没有有效长度的候选，选择最短的那个（可能是被截断的）
        normalized.sort(key=lambda item: len(item))
        return normalized[0]

    page_title_text = (page_title or "").strip()
    if page_title_text and _TITLE_LENGTH_MIN <= len(page_title_text) <= _TITLE_LENGTH_MAX:
        return page_title_text

    return page_title_text or None


def choose_best_shop_name(candidates: list[str], body_text: str = "") -> str | None:
    """从多个店铺候选中挑选最可信的一项。"""

    normalized = _normalize_candidates(candidates)
    # 优先选择包含店铺相关关键词的候选
    preferred = [item for item in normalized if any(keyword in item for keyword in ["店", "旗舰", "官方", "门窗", "家居"])]
    if preferred:
        # 选择最长的（更完整的店铺名）
        preferred.sort(key=len, reverse=True)
        return preferred[0]
    if normalized:
        normalized.sort(key=len, reverse=True)
        return normalized[0]

    # 回退：从 body 文本中正则匹配店铺名
    if body_text:
        return _extract_shop_name_from_body(body_text)

    return None


def _extract_shop_name_from_body(body_text: str) -> str | None:
    """从正文文本中提取店铺名。"""

    for pattern in _SHOP_NAME_PATTERNS:
        match = pattern.search(body_text)
        if match:
            shop_name = match.group(1).strip()
            if 2 <= len(shop_name) <= 30:
                return shop_name
    return None


def choose_best_price_text(candidates: list[str], body_text: str = "") -> str | None:
    """从候选文本与正文中挑选最可信的价格文本。"""

    normalized = _normalize_candidates(candidates)

    # 首先从候选中查找符合价格格式的文本
    for item in normalized:
        match = _PRICE_PATTERN.search(item)
        if match:
            return match.group(0)

    # 回退：尝试匹配其他价格格式
    for item in normalized:
        match = _PRICE_ALT_PATTERN.search(item)
        if match:
            return f"{match.group(1)}元/㎡"

    # 回退：从 body 文本中查找价格
    if body_text:
        body_match = _PRICE_PATTERN.search(body_text)
        if body_match:
            return body_match.group(0)

        alt_body_match = _PRICE_ALT_PATTERN.search(body_text)
        if alt_body_match:
            return f"{alt_body_match.group(1)}元/㎡"

    # 最后回退：返回第一个候选（可能是价格数字）
    return normalized[0] if normalized else None


def choose_best_body_text(candidates: list[str], min_length: int = 100) -> str:
    """从正文候选中选择最长且信息密度较高的一段。"""

    normalized = _normalize_candidates(candidates)
    if not normalized:
        return ""

    # 优先选择长度超过最小阈值的候选
    valid_candidates = [c for c in normalized if len(c) >= min_length]
    if valid_candidates:
        valid_candidates.sort(key=lambda item: len(item), reverse=True)
        return valid_candidates[0]

    # 如果没有达到最小长度的候选，选择最长的
    normalized.sort(key=lambda item: len(item), reverse=True)
    return normalized[0]


def _normalize_candidates(candidates: list[str]) -> list[str]:
    """清洗并去重候选文本。"""

    seen: set[str] = set()
    result: list[str] = []
    for item in candidates:
        text = " ".join((item or "").split()).strip()
        if not text:
            continue
        if text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
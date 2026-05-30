# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 23:55:38 CST

from __future__ import annotations

import re


def parse_price_value(price_text: str | None) -> float | None:
    """从价格文本中解析数值。

    目标不是做复杂币种支持，而是先把淘宝门窗场景常见的：
    - 718元/㎡
    - 980 元/平米
    - 6064

    统一抽出一个可比较的数值。
    """

    if not price_text:
        return None

    normalized = str(price_text).replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", normalized)
    if not match:
        return None
    return float(match.group(0))

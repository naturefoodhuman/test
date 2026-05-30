# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 22:10:40 CST

from __future__ import annotations

import re

from shopping.schemas import ProductDetail

GLASS_SPEC_PATTERNS = [
    re.compile(r"\d+(?:\+\d+(?:夹胶|PVB|SGP)?)*(?:\+\d+A)?(?:\+\d+)?(?:双层钢化中空玻璃|钢化中空玻璃|双层钢化中空|中空玻璃|中空)"),
    re.compile(r"\d+\+\d+(?:夹胶|PVB|SGP).{0,20}"),
]

FRAME_SPEC_PATTERNS = [
    re.compile(r"(?:\d{2,3})系统(?:平开窗|窗|门窗)"),
    re.compile(r"壁厚\s*1\.\d"),
]

SEAL_PATTERNS = [
    re.compile(r"[三四五六]道密封"),
    re.compile(r"三元乙丙密封条"),
    re.compile(r"EPDM密封条", re.IGNORECASE),
]

HARDWARE_PATTERNS = [
    re.compile(r"HOPO执手", re.IGNORECASE),
    re.compile(r"好博"),
    re.compile(r"瑞纳斯"),
]

SERVICE_KEYWORDS = ["测量", "安装", "拆旧", "防水", "运输", "上门"]


def normalize_text(text: str) -> str:
    """统一空白字符，减少规则匹配噪声。"""

    return re.sub(r"\s+", " ", text or "").strip()


def _first_match(text: str, patterns: list[re.Pattern[str]]) -> str | None:
    """返回第一条命中的规则。"""

    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return None


def extract_installation_services(text: str) -> list[str]:
    """从文本中提取服务项。"""

    normalized = normalize_text(text)
    found: list[str] = []
    for keyword in SERVICE_KEYWORDS:
        if keyword in normalized and keyword not in found:
            found.append(keyword)
    return found


def extract_candidate_keywords(text: str) -> list[str]:
    """从原始文本中抽取可用于后续摘要的关键词。"""

    normalized = normalize_text(text)
    candidates = [
        _first_match(normalized, GLASS_SPEC_PATTERNS),
        _first_match(normalized, FRAME_SPEC_PATTERNS),
        _first_match(normalized, SEAL_PATTERNS),
        _first_match(normalized, HARDWARE_PATTERNS),
    ]
    return [item for item in candidates if item]


def build_product_detail_from_text(
    *,
    title: str,
    raw_text: str,
    price_text: str | None = None,
    shop_name: str | None = None,
    detail_url: str | None = None,
) -> ProductDetail:
    """根据原始商品文本做一轮确定性标准化。

    这层规则的目标不是取代 LLM，而是先把“好提取、稳定提取”的字段尽量拿出来。
    """

    normalized = normalize_text(raw_text)
    glass_spec = _first_match(normalized, GLASS_SPEC_PATTERNS)
    frame_spec = _first_match(normalized, FRAME_SPEC_PATTERNS)
    seal_spec = _first_match(normalized, SEAL_PATTERNS)
    hardware_keyword = _first_match(normalized, HARDWARE_PATTERNS)
    installation_services = extract_installation_services(normalized)
    extracted_keywords = extract_candidate_keywords(normalized)

    risk_flags: list[str] = []
    if "推拉窗" in normalized:
        risk_flags.append("推拉窗结构隔音上限通常弱于平开窗")
    if glass_spec is None:
        risk_flags.append("未识别到明确玻璃配置")
    if seal_spec is None:
        risk_flags.append("未识别到明确密封配置")

    return ProductDetail(
        title=title,
        price_text=price_text,
        shop_name=shop_name,
        detail_url=detail_url,
        glass_spec=glass_spec,
        frame_spec=frame_spec,
        seal_spec=seal_spec,
        hardware_keyword=hardware_keyword,
        installation_services=installation_services,
        extracted_keywords=extracted_keywords,
        raw_spec_text=normalized,
        risk_flags=risk_flags,
    )

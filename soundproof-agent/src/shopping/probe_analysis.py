# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 17:30:00 CST

from __future__ import annotations

import re
from typing import Any

_PRICE_PATTERN = re.compile(r"\d+(?:\.\d+)?")
_PRICE_UNIT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:元|¥|$)")


def analyze_search_probe(payload: dict[str, Any]) -> dict[str, Any]:
    """分析搜索页探针结果并给出建议。"""

    suggestions: list[str] = []
    priority_fixes: list[str] = []
    selector_counts = payload.get("selector_counts", []) or []
    records = payload.get("records_preview", []) or []
    records_count = int(payload.get("records_count", 0) or 0)
    body_length = int(payload.get("body_length", 0) or 0)
    risk = payload.get("risk", {}) or {}

    if risk.get("detected"):
        suggestions.append("页面命中风控/验证码，先停止自动抓取并切人工接管。")
        return _build_search_probe_result(payload, suggestions, priority_fixes, "blocked", selector_counts, records_count, body_length)

    positive_selectors = [item for item in selector_counts if int(item.get("count", 0) or 0) > 0]
    if not positive_selectors:
        suggestions.append("列表页卡片选择器全部未命中，优先检查页面结构是否改版。")
        priority_fixes.append("检查页面是否正常加载（查看 artifact HTML）")
        priority_fixes.append("尝试使用更通用的选择器如 'a[href]' 作为兜底")
        priority_fixes.append("检查是否需要滚动加载更多内容")
    elif records_count == 0:
        suggestions.append("卡片选择器有命中但未抽出候选，优先检查链接提取逻辑。")
        priority_fixes.append("检查 detail_link_patterns 是否需要更新")
        priority_fixes.append("检查商品卡片的 DOM 结构是否有变化")

    if body_length < 200:
        suggestions.append("搜索页正文长度偏短，可能页面未完整加载、跳转异常或被风控。")
        priority_fixes.append("增加 wait_after_load_ms 参数到 5000ms")
        priority_fixes.append("检查 artifact 截图确认页面是否正常显示")

    # 分析候选质量
    quality_analysis = _analyze_search_records_quality(records)
    if quality_analysis["ad_ratio"] > 0.3:
        suggestions.append(f"候选中广告/推广商品占比偏高（{quality_analysis['ad_ratio']:.0%}），可能需要加强广告过滤。")
        priority_fixes.append("检查广告识别关键词是否需要更新")

    if quality_analysis["avg_title_length"] < 10:
        suggestions.append(f"商品标题平均长度偏短（{quality_analysis['avg_title_length']:.0f}），可能抽取逻辑有问题。")
        priority_fixes.append("检查标题提取脚本的 textNodes 过滤条件")

    if quality_analysis["price_coverage"] < 0.3:
        suggestions.append(f"候选中价格覆盖率偏低（{quality_analysis['price_coverage']:.0%}），可能价格提取逻辑需要改进。")

    # 价格区间分析
    price_range = _analyze_price_range(records)
    if price_range:
        suggestions.append(f"候选商品价格区间：{price_range['min']}-{price_range['max']} 元/㎡，均价约 {price_range['avg']:.0f} 元/㎡。")

    if records_count > 0 and not suggestions:
        suggestions.append("搜索页探针结果基本可用，可继续执行 search-once 或 live-demo。")

    readiness = "ready" if records_count > 0 and not risk.get("detected") and positive_selectors else "needs_fix"
    return _build_search_probe_result(payload, suggestions, priority_fixes, readiness, selector_counts, records_count, body_length, quality_analysis, price_range)


def analyze_detail_probe(payload: dict[str, Any]) -> dict[str, Any]:
    """分析详情页探针结果并给出建议。"""

    suggestions: list[str] = []
    priority_fixes: list[str] = []
    risk = payload.get("risk", {}) or {}
    title_candidates = payload.get("title_candidates", []) or []
    shop_candidates = payload.get("shop_candidates", []) or []
    price_candidates = payload.get("price_candidates", []) or []
    body_length = int(payload.get("body_length", 0) or 0)

    if risk.get("detected"):
        suggestions.append("详情页命中风控/验证码，先停止自动抓取并切人工接管。")
        return _build_detail_probe_result(payload, suggestions, priority_fixes, "blocked", title_candidates, shop_candidates, price_candidates, body_length)

    # 分析各字段的提取优先级
    field_priority = _analyze_field_priority(title_candidates, shop_candidates, price_candidates, body_length)

    if not title_candidates:
        suggestions.append("标题选择器未命中，优先检查标题区域结构。")
        priority_fixes.append("检查页面是否使用动态渲染（如 Vue/React）")
        priority_fixes.append("尝试回退到 page.title() 作为兜底")
        priority_fixes.append("检查 h1 元素是否存在或标题是否在其他标签中")
    elif len(title_candidates) > 1:
        suggestions.append(f"标题候选过多（{len(title_candidates)}），可能需要更精确的选择器。")

    if not shop_candidates:
        suggestions.append("店铺选择器未命中，优先补充店铺名回退策略。")
        priority_fixes.append("尝试从页面 body 文本中正则匹配 'XX门窗旗舰店' 等模式")
        priority_fixes.append("检查店铺链接是否包含 shopId 参数")
        priority_fixes.append("使用包含 '店' 或 '旗舰' 的文本节点作为兜底")

    if not price_candidates:
        suggestions.append("价格选择器未命中，优先检查价格展示区域。")
        priority_fixes.append("从 body 文本中正则提取价格（如 '718元/㎡'）")
        priority_fixes.append("检查价格是否在图片中而非文本中")
        priority_fixes.append("确认商品是否按面积计价")

    if body_length < 300:
        suggestions.append("详情页正文长度偏短，可能页面未完整加载或正文抽取过弱。")
        priority_fixes.append("增加 wait_after_load_ms 参数到 5000ms")
        priority_fixes.append("尝试滚动页面触发懒加载内容")
        priority_fixes.append("检查页面是否需要登录才能查看完整内容")

    # 字段质量评估
    quality_score = _evaluate_detail_field_quality(title_candidates, shop_candidates, price_candidates, body_length)
    if quality_score < 0.5:
        suggestions.append(f"详情页字段质量评分偏低（{quality_score:.0%}），建议先修复再执行完整链路。")

    if title_candidates and price_candidates and body_length >= 300 and not risk.get("detected"):
        suggestions.append("详情页探针结果基本可用，可继续执行 detail-once 或 live-demo。")

    readiness = "ready" if title_candidates and price_candidates and body_length >= 300 and not risk.get("detected") else "needs_fix"
    return _build_detail_probe_result(payload, suggestions, priority_fixes, readiness, title_candidates, shop_candidates, price_candidates, body_length, field_priority, quality_score)


def _analyze_search_records_quality(records: list[dict]) -> dict[str, Any]:
    """分析搜索候选记录的质量。"""

    if not records:
        return {
            "ad_ratio": 0.0,
            "avg_title_length": 0.0,
            "price_coverage": 0.0,
        }

    total = len(records)
    ad_count = sum(1 for r in records if _is_ad_product(r))
    has_price_count = sum(1 for r in records if r.get("price_text"))
    title_lengths = [len(r.get("title", "")) for r in records]

    return {
        "ad_ratio": ad_count / total if total > 0 else 0.0,
        "avg_title_length": sum(title_lengths) / len(title_lengths) if title_lengths else 0.0,
        "price_coverage": has_price_count / total if total > 0 else 0.0,
    }


def _is_ad_product(record: dict) -> bool:
    """判断是否为广告/推广商品。"""

    title = record.get("title", "") or ""
    price_text = record.get("price_text", "") or ""

    ad_signals = ["推广", "广告", "热卖", "爆款", "限时"]
    for signal in ad_signals:
        if signal in title:
            return True

    if price_text and "???" in price_text:
        return True

    return False


def _analyze_price_range(records: list[dict]) -> dict[str, Any] | None:
    """分析候选商品的价格区间。"""

    prices = []
    for record in records:
        price_text = record.get("price_text", "") or ""
        match = _PRICE_UNIT_PATTERN.search(price_text)
        if match:
            try:
                price = float(match.group(1))
                if 50 < price < 2000:
                    prices.append(price)
            except ValueError:
                continue

    if not prices:
        return None

    return {
        "min": min(prices),
        "max": max(prices),
        "avg": sum(prices) / len(prices),
        "count": len(prices),
    }


def _analyze_field_priority(
    title_candidates: list, shop_candidates: list, price_candidates: list, body_length: int
) -> list[dict[str, str]]:
    """分析各字段的提取优先级。"""

    priorities = []

    if not title_candidates:
        priorities.append({"field": "title", "status": "missing", "suggestion": "使用 page.title() 回退"})
    elif len(title_candidates) == 1:
        priorities.append({"field": "title", "status": "ready", "suggestion": f"提取到：{title_candidates[0].get('text', '')[:30]}..."})
    else:
        priorities.append({"field": "title", "status": "multiple", "suggestion": "需要从多个候选中选择最佳"})

    if not shop_candidates:
        priorities.append({"field": "shop_name", "status": "missing", "suggestion": "从 body 文本正则匹配店铺名"})
    else:
        priorities.append({"field": "shop_name", "status": "ready", "suggestion": f"提取到：{shop_candidates[0].get('text', '')[:20]}"})

    if not price_candidates:
        priorities.append({"field": "price", "status": "missing", "suggestion": "从 body 文本正则提取价格"})
    else:
        priorities.append({"field": "price", "status": "ready", "suggestion": f"提取到：{price_candidates[0].get('text', '')[:20]}"})

    priorities.append({"field": "body", "status": "ready" if body_length >= 500 else "weak", "suggestion": f"正文长度 {body_length} 字符"})

    return priorities


def _evaluate_detail_field_quality(title_candidates: list, shop_candidates: list, price_candidates: list, body_length: int) -> float:
    """评估详情页字段提取的整体质量分数（0-1）。"""

    score = 0.0

    if title_candidates:
        score += 0.3
    if shop_candidates:
        score += 0.2
    if price_candidates:
        score += 0.2

    if body_length >= 500:
        score += 0.2
    elif body_length >= 300:
        score += 0.1
    elif body_length >= 100:
        score += 0.05

    return min(score, 1.0)


def _build_search_probe_result(
    payload: dict,
    suggestions: list,
    priority_fixes: list,
    readiness: str,
    selector_counts: list,
    records_count: int,
    body_length: int,
    quality_analysis: dict | None = None,
    price_range: dict | None = None,
) -> dict[str, Any]:
    """构建搜索页探针分析结果。"""

    result = {
        "readiness": readiness,
        "suggestions": suggestions,
        "priority_fixes": priority_fixes,
        "positive_selector_count": len([s for s in selector_counts if int(s.get("count", 0) or 0) > 0]),
        "records_count": records_count,
        "body_length": body_length,
    }

    if quality_analysis:
        result["quality_analysis"] = {
            "ad_ratio": round(quality_analysis["ad_ratio"], 2),
            "avg_title_length": round(quality_analysis["avg_title_length"], 1),
            "price_coverage": round(quality_analysis["price_coverage"], 2),
        }

    if price_range:
        result["price_range"] = {
            "min": price_range["min"],
            "max": price_range["max"],
            "avg": round(price_range["avg"], 0),
            "count": price_range["count"],
        }

    return result


def _build_detail_probe_result(
    payload: dict,
    suggestions: list,
    priority_fixes: list,
    readiness: str,
    title_candidates: list,
    shop_candidates: list,
    price_candidates: list,
    body_length: int,
    field_priority: list | None = None,
    quality_score: float | None = None,
) -> dict[str, Any]:
    """构建详情页探针分析结果。"""

    result = {
        "readiness": readiness,
        "suggestions": suggestions,
        "priority_fixes": priority_fixes,
        "title_hit_count": len(title_candidates),
        "shop_hit_count": len(shop_candidates),
        "price_hit_count": len(price_candidates),
        "body_length": body_length,
    }

    if field_priority:
        result["field_priority"] = field_priority

    if quality_score is not None:
        result["quality_score"] = round(quality_score, 2)

    return result
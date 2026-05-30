# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 22:10:40 CST

from __future__ import annotations

import json
from typing import Any

from shopping.parser_rules import build_product_detail_from_text
from shopping.schemas import ProductComparisonSummary, ProductDetail, ShoppingSearchIntent
from utils.ollama_client import OllamaClient


class ShoppingFieldNormalizerService:
    """商品字段补归纳服务。"""

    def __init__(self, client: OllamaClient, model_name: str, temperature: float = 0.1) -> None:
        self.client = client
        self.model_name = model_name
        self.temperature = temperature

    def normalize(
        self,
        *,
        title: str,
        raw_text: str,
        price_text: str | None = None,
        shop_name: str | None = None,
        detail_url: str | None = None,
    ) -> ProductDetail:
        """对详情页文本做结构化归一。"""

        base_detail = build_product_detail_from_text(
            title=title,
            raw_text=raw_text,
            price_text=price_text,
            shop_name=shop_name,
            detail_url=detail_url,
        )

        prompt = self._build_prompt(base_detail=base_detail, raw_text=raw_text)
        schema = ProductDetail.model_json_schema()
        response_text = self.client.chat(
            model=self.model_name,
            prompt=prompt,
            temperature=self.temperature,
            format_schema=schema,
        )
        payload = self._safe_load_json(response_text)
        if payload is None:
            return base_detail

        try:
            llm_detail = ProductDetail.model_validate(payload)
        except Exception:
            return base_detail

        merged = base_detail.model_dump()
        for key, value in llm_detail.model_dump().items():
            if merged.get(key) in (None, "", [], {}):
                merged[key] = value
        return ProductDetail.model_validate(merged)

    def _build_prompt(self, *, base_detail: ProductDetail, raw_text: str) -> str:
        """构造字段补归纳提示词。"""

        return "\n\n".join(
            [
                "你是隔音窗电商商品结构化助手。",
                "请基于给定原始文本，补全商品详情 JSON。",
                "原则：已有字段尽量保持不变，不要臆造没有出现的品牌和参数。",
                f"当前已提取字段：\n{json.dumps(base_detail.model_dump(), ensure_ascii=False, indent=2)}",
                f"原始商品文本：\n{raw_text}",
                "请直接输出 JSON，不要输出 Markdown 代码块。",
            ]
        )

    @staticmethod
    def _safe_load_json(text: str) -> dict[str, Any] | None:
        """安全解析 JSON。"""

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return None


class ShoppingSummaryService:
    """商品对比总结服务。"""

    def __init__(self, client: OllamaClient, model_name: str, temperature: float = 0.1) -> None:
        self.client = client
        self.model_name = model_name
        self.temperature = temperature

    def summarize(
        self,
        *,
        intent: ShoppingSearchIntent,
        products: list[ProductDetail],
    ) -> ProductComparisonSummary:
        """对一组商品做比较总结。"""

        prompt = self._build_prompt(intent=intent, products=products)
        schema = ProductComparisonSummary.model_json_schema()
        response_text = self.client.chat(
            model=self.model_name,
            prompt=prompt,
            temperature=self.temperature,
            format_schema=schema,
        )
        payload = ShoppingFieldNormalizerService._safe_load_json(response_text)
        if payload is None:
            raise ValueError("购物总结模型未返回可解析 JSON。")
        return ProductComparisonSummary.model_validate(payload)

    def _build_prompt(self, *, intent: ShoppingSearchIntent, products: list[ProductDetail]) -> str:
        """构造对比总结提示词。"""

        return "\n\n".join(
            [
                "你是隔音窗购物参谋，请根据用户场景在候选商品中给出推荐。",
                "重点考虑：低频噪音适配、密封、玻璃结构、安装风险、是否适合当前预算。",
                f"用户购物意图：\n{json.dumps(intent.model_dump(), ensure_ascii=False, indent=2)}",
                f"候选商品：\n{json.dumps([item.model_dump() for item in products], ensure_ascii=False, indent=2)}",
                "请直接输出 JSON，不要输出 Markdown 代码块。",
            ]
        )

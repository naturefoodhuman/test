# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 12:48:24 CST

from __future__ import annotations

import json
from typing import Any


class OllamaClient:
    """面向 Phase 0 的极简 Ollama 客户端。

    当前只封装评测所需的 `/api/chat` 调用；后续阶段再抽成更通用的模型客户端。
    """

    def __init__(self, base_url: str, timeout_seconds: int = 180) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def chat(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        format_schema: dict[str, Any] | str | None = None,
    ) -> str:
        """调用 Ollama 生成回答。

        Args:
            model: 模型名称。
            prompt: 发送给模型的完整提示词。
            temperature: 采样温度。
            format_schema: 可选 JSON Schema；若传入，将要求模型输出结构化结果。

        Returns:
            str: 模型返回的文本内容。
        """

        try:
            import httpx
        except ModuleNotFoundError as exc:  # pragma: no cover - 依赖缺失时的友好报错
            raise RuntimeError(
                "缺少 httpx 依赖，请先在项目目录执行 `uv sync`。"
            ) from exc

        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if format_schema is not None:
            payload["format"] = format_schema

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

        message = data.get("message", {})
        content = message.get("content", "")
        if not isinstance(content, str):
            return json.dumps(content, ensure_ascii=False)
        return content

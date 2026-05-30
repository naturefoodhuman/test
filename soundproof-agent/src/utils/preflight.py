# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 13:50:28 CST

from __future__ import annotations

from typing import Any


def run_preflight_check(base_url: str) -> dict[str, Any]:
    """检查 Ollama 服务可达性与模型可用性。

    Args:
        base_url: Ollama 服务地址。

    Returns:
        dict[str, Any]: 预检查结果。
    """

    try:
        import httpx
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("缺少 httpx 依赖，请先执行 `uv sync`。") from exc

    normalized_base_url = base_url.rstrip("/")
    result: dict[str, Any] = {
        "base_url": normalized_base_url,
        "reachable": False,
        "version": None,
        "models": [],
        "error": None,
    }

    try:
        with httpx.Client(timeout=20) as client:
            version_response = client.get(f"{normalized_base_url}/api/version")
            version_response.raise_for_status()
            result["reachable"] = True
            result["version"] = version_response.json()

            tags_response = client.get(f"{normalized_base_url}/api/tags")
            tags_response.raise_for_status()
            tags_payload = tags_response.json()
            models = tags_payload.get("models", [])
            result["models"] = [item.get("name") for item in models if isinstance(item, dict) and item.get("name")]
    except Exception as exc:  # pragma: no cover - 环境依赖型逻辑
        result["error"] = str(exc)

    return result

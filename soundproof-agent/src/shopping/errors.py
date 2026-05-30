# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:05:58 CST

from __future__ import annotations


class ShoppingExecutionError(RuntimeError):
    """购物执行通用异常。"""


class ShoppingRiskDetectedError(ShoppingExecutionError):
    """当页面出现验证码、风控、访问受限等信号时抛出。"""

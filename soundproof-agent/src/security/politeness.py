# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-28 22:55:19 CST

from __future__ import annotations


def compute_polite_delay(base_delay_seconds: float, *, multiplier: float = 1.0, extra_seconds: float = 0.0) -> float:
    """计算一个保守的执行延时。

    设计目标：
    - 把“慢一点”从口头约定变成可复用函数；
    - 让工作流与执行器层都能统一调用；
    - 当前先做确定性延时，不引入随机性，便于测试与审计。
    """

    return max(0.0, round(base_delay_seconds * multiplier + extra_seconds, 4))

# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-27 23:58:35 CST

from __future__ import annotations

import os
from pathlib import Path

from api.app import create_app

PROJECT_ROOT = Path(os.getenv("SOUNDPROOF_AGENT_PROJECT_ROOT", ".")).resolve()
app = create_app(PROJECT_ROOT)

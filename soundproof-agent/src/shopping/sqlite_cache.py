# 创建该文件的LLM大模型名称：Arena.ai Agent Mode
# 创建时间（北京时间，精确到秒）：2026-05-29 16:41:07 CST

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from shopping.cache_models import ShoppingRunCache


class ShoppingCacheStore:
    """购物缓存 SQLite 存储。

    V1 先用 sqlite3 直接实现，优先把缓存能力落地。
    后续若接入完整 ORM，再平滑迁移。
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def initialize(self) -> None:
        """初始化缓存表与事件表。"""

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS shopping_runs (
                    run_id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    search_query TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS shopping_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def save_run(self, run_cache: ShoppingRunCache) -> None:
        """保存一次购物运行快照。"""

        payload_json = run_cache.model_dump_json()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO shopping_runs (run_id, platform, search_query, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    run_cache.run_id,
                    run_cache.platform,
                    run_cache.search_query,
                    payload_json,
                    run_cache.created_at.isoformat(timespec="seconds"),
                ),
            )
            connection.commit()

    def get_run(self, run_id: str) -> ShoppingRunCache | None:
        """读取一次购物运行快照。"""

        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(
                "SELECT payload_json FROM shopping_runs WHERE run_id = ?",
                (run_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None
        payload = json.loads(row[0])
        return ShoppingRunCache.model_validate(payload)

    def list_runs(self) -> list[tuple[str, str, str]]:
        """列出历史运行摘要。"""

        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(
                "SELECT run_id, platform, search_query FROM shopping_runs ORDER BY created_at DESC"
            )
            return [(row[0], row[1], row[2]) for row in cursor.fetchall()]

    def list_recent_run_caches(self, limit: int = 20) -> list[ShoppingRunCache]:
        """读取最近若干次完整运行快照。"""

        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(
                "SELECT payload_json FROM shopping_runs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
        return [ShoppingRunCache.model_validate(json.loads(row[0])) for row in rows]

    def list_run_summaries(self, limit: int = 20) -> list[dict]:
        """列出带时间的运行摘要。"""

        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(
                """
                SELECT run_id, platform, search_query, created_at
                FROM shopping_runs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
        return [
            {
                "run_id": row[0],
                "platform": row[1],
                "search_query": row[2],
                "created_at": row[3],
            }
            for row in rows
        ]

    def latest_run_id(self) -> str | None:
        """获取最近一次运行 ID。"""

        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(
                "SELECT run_id FROM shopping_runs ORDER BY created_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
        return row[0] if row else None

    def record_event(self, event_type: str, payload: dict | None = None) -> None:
        """记录一次运行事件。"""

        self.initialize()
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                INSERT INTO shopping_events (event_type, payload_json, created_at)
                VALUES (?, ?, ?)
                """,
                (
                    event_type,
                    json.dumps(payload or {}, ensure_ascii=False),
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            connection.commit()

    def count_recent_events(self, event_type: str, within_seconds: int) -> int:
        """统计最近一段时间内的事件数量。"""

        self.initialize()
        threshold = (datetime.now() - timedelta(seconds=within_seconds)).isoformat(timespec="seconds")
        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(
                """
                SELECT COUNT(*) FROM shopping_events
                WHERE event_type = ? AND created_at >= ?
                """,
                (event_type, threshold),
            )
            row = cursor.fetchone()
        return int(row[0]) if row else 0

    def summarize_recent_events(self, within_seconds: int = 3600) -> dict[str, int]:
        """汇总最近一段时间各类事件数。"""

        self.initialize()
        threshold = (datetime.now() - timedelta(seconds=within_seconds)).isoformat(timespec="seconds")
        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(
                """
                SELECT event_type, COUNT(*)
                FROM shopping_events
                WHERE created_at >= ?
                GROUP BY event_type
                ORDER BY event_type ASC
                """,
                (threshold,),
            )
            rows = cursor.fetchall()
        return {row[0]: int(row[1]) for row in rows}

    def list_recent_events(self, limit: int = 50, *, event_type: str | None = None, run_id: str | None = None) -> list[dict]:
        """列出最近的事件日志。

        Args:
            limit: 返回条数上限。
            event_type: 可选事件类型过滤。
            run_id: 可选运行 ID 过滤，会在 JSON payload 里匹配。
        """

        self.initialize()
        query = "SELECT id, event_type, payload_json, created_at FROM shopping_events"
        clauses: list[str] = []
        params: list[object] = []

        if event_type is not None:
            clauses.append("event_type = ?")
            params.append(event_type)
        if run_id is not None:
            clauses.append("payload_json LIKE ?")
            params.append(f'%"run_id": "{run_id}"%')

        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with closing(sqlite3.connect(self.db_path)) as connection:
            cursor = connection.execute(query, tuple(params))
            rows = cursor.fetchall()
        return [
            {
                "id": int(row[0]),
                "event_type": row[1],
                "payload": json.loads(row[2]),
                "created_at": row[3],
            }
            for row in rows
        ]

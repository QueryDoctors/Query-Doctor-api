"""ClickHouse repository for reading historical query latency data."""
import hashlib
import re
from dataclasses import dataclass
from datetime import datetime

import clickhouse_connect

from app.infrastructure.config import Settings


@dataclass
class LatencyPoint:
    captured_at: datetime
    mean_latency_ms: float


def _normalize_query(q: str) -> str:
    n = re.sub(r"'[^']*'", "?", q)
    n = re.sub(r"\b\d+\b", "?", n)
    return " ".join(n.lower().split())


def query_hash(q: str) -> str:
    return hashlib.sha256(_normalize_query(q).encode()).hexdigest()[:16]


class ChHistoryRepo:
    def __init__(self, settings: Settings) -> None:
        self._client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_db,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
        )
        self._db = settings.clickhouse_db

    def get_history(
        self, db_id: str, q_hash: str, hours: int = 2
    ) -> list[LatencyPoint]:
        result = self._client.query(
            f"SELECT captured_at, mean_latency_ms"
            f" FROM `{self._db}`.query_latency_snapshots"
            f" WHERE db_id = {{db_id:String}}"
            f"   AND query_hash = {{qh:String}}"
            f"   AND captured_at >= now() - INTERVAL {{h:UInt32}} HOUR"
            f" ORDER BY captured_at ASC",
            parameters={"db_id": db_id, "qh": q_hash, "h": hours},
        )
        return [
            LatencyPoint(captured_at=row[0], mean_latency_ms=row[1])
            for row in result.result_rows
        ]

import asyncio
from typing import Optional

from app.domain.entities.query_latency_snapshot import QueryLatencySnapshot
from app.domain.repositories.baseline_repository import IBaselineRepository
from app.infrastructure.persistence.ch_manager import ClickHouseManager
from app.infrastructure.config import get_settings


class ChBaselineRepository(IBaselineRepository):
    """
    ClickHouse implementation of IBaselineRepository.
    All DB calls wrapped in asyncio.to_thread — clickhouse-connect is synchronous.
    """

    def __init__(self, manager: ClickHouseManager) -> None:
        self._manager = manager

    @property
    def _db(self) -> str:
        return get_settings().clickhouse_db

    async def save_snapshot(self, snapshot: QueryLatencySnapshot) -> None:
        client = self._manager.client
        data = [[
            snapshot.db_id,
            snapshot.query_hash,
            snapshot.query_text,
            snapshot.mean_latency_ms,
            snapshot.calls,
            snapshot.calls_per_minute,
            snapshot.captured_at,
        ]]
        await asyncio.to_thread(
            client.insert,
            f"`{self._db}`.query_latency_snapshots",
            data,
            column_names=[
                "db_id", "query_hash", "query_text",
                "mean_latency_ms", "calls", "calls_per_minute", "captured_at",
            ],
        )

    async def get_p95(
        self, db_id: str, query_hash: str, within_minutes: int
    ) -> Optional[float]:
        client = self._manager.client

        def _query():
            result = client.query(f"""
                SELECT quantile(0.95)(mean_latency_ms)
                FROM `{self._db}`.query_latency_snapshots
                WHERE db_id = %(db_id)s
                  AND query_hash = %(query_hash)s
                  AND captured_at > now() - toIntervalMinute(%(minutes)s)
            """, parameters={"db_id": db_id, "query_hash": query_hash, "minutes": within_minutes})
            return result.result_rows

        rows = await asyncio.to_thread(_query)
        if not rows or rows[0][0] is None:
            return None
        val = float(rows[0][0])
        return val if val > 0 else None

    async def get_snapshot_count(
        self, db_id: str, query_hash: str, within_seconds: int
    ) -> int:
        client = self._manager.client

        def _query():
            result = client.query(f"""
                SELECT count()
                FROM `{self._db}`.query_latency_snapshots
                WHERE db_id = %(db_id)s
                  AND query_hash = %(query_hash)s
                  AND captured_at > now() - toIntervalSecond(%(seconds)s)
            """, parameters={"db_id": db_id, "query_hash": query_hash, "seconds": within_seconds})
            return result.result_rows

        rows = await asyncio.to_thread(_query)
        return int(rows[0][0]) if rows else 0

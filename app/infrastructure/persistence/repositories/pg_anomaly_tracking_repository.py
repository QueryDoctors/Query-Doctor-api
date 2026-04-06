from datetime import datetime
from typing import Optional, Tuple

from app.domain.repositories.anomaly_tracking_repository import IAnomalyTrackingRepository
from app.infrastructure.persistence.pg_manager import AppPgManager


class PgAnomalyTrackingRepository(IAnomalyTrackingRepository):

    def __init__(self, manager: AppPgManager) -> None:
        self._manager = manager

    async def upsert(
        self, db_id: str, query_hash: str, first_seen_at: datetime, last_seen_at: datetime
    ) -> None:
        async with self._manager.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO anomaly_tracking (query_hash, db_id, first_seen_at, last_seen_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (query_hash, db_id)
                DO UPDATE SET last_seen_at = EXCLUDED.last_seen_at
            """, query_hash, db_id, first_seen_at, last_seen_at)

    async def get(
        self, db_id: str, query_hash: str
    ) -> Optional[Tuple[datetime, datetime]]:
        async with self._manager.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT first_seen_at, last_seen_at FROM anomaly_tracking WHERE query_hash = $1 AND db_id = $2",
                query_hash, db_id,
            )
        if row is None:
            return None
        return (row["first_seen_at"], row["last_seen_at"])

    async def delete(self, db_id: str, query_hash: str) -> None:
        async with self._manager.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM anomaly_tracking WHERE query_hash = $1 AND db_id = $2",
                query_hash, db_id,
            )

    async def delete_stale(self, older_than_minutes: int) -> None:
        async with self._manager.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM anomaly_tracking
                WHERE last_seen_at < now() - ($1 * interval '1 minute')
            """, older_than_minutes)

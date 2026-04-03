import re
from typing import List

from app.domain.repositories.query_repository import IQueryRepository
from app.domain.entities.query_stat import QueryStat
from app.infrastructure.database.pool_manager import PoolManager


def _normalize(query: str) -> str:
    """Strip string literals and numeric constants from query text."""
    query = re.sub(r"'[^']*'", "'?'", query)
    query = re.sub(r"\b\d+\b", "?", query)
    return query.strip()


def _to_entity(row) -> QueryStat:
    return QueryStat(
        query=_normalize(row["query"]),
        mean_time_ms=round(float(row["mean_exec_time"]), 2),
        calls=int(row["calls"]),
        total_time_ms=round(float(row["total_exec_time"]), 2),
        rows=int(row["rows"]) if row["rows"] is not None else None,
    )


class PgQueryRepository(IQueryRepository):
    def __init__(self, pool_manager: PoolManager) -> None:
        self._pool_manager = pool_manager

    async def fetch_slow(self, db_id: str) -> List[QueryStat]:
        pool = self._pool_manager.get(db_id)
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT query, mean_exec_time, calls, total_exec_time, rows
                FROM pg_stat_statements
                ORDER BY mean_exec_time DESC
                LIMIT 10
            """)
        return [_to_entity(r) for r in rows]

    async def fetch_frequent(self, db_id: str) -> List[QueryStat]:
        pool = self._pool_manager.get(db_id)
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT query, calls, mean_exec_time, total_exec_time, rows
                FROM pg_stat_statements
                ORDER BY calls DESC
                LIMIT 10
            """)
        return [_to_entity(r) for r in rows]

    async def fetch_heaviest(self, db_id: str) -> List[QueryStat]:
        pool = self._pool_manager.get(db_id)
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT query, total_exec_time, calls, mean_exec_time, rows
                FROM pg_stat_statements
                ORDER BY total_exec_time DESC
                LIMIT 10
            """)
        return [_to_entity(r) for r in rows]

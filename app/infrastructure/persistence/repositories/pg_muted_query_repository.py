from app.domain.repositories.muted_query_repository import IMutedQueryRepository
from app.infrastructure.persistence.pg_manager import AppPgManager


class PgMutedQueryRepository(IMutedQueryRepository):

    def __init__(self, manager: AppPgManager) -> None:
        self._manager = manager

    async def mute(self, query_hash: str, db_id: str) -> None:
        async with self._manager.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO muted_queries (query_hash, db_id, is_whitelisted)
                VALUES ($1, $2, false)
                ON CONFLICT (query_hash, db_id) DO UPDATE SET is_whitelisted = false
            """, query_hash, db_id)

    async def unmute(self, query_hash: str, db_id: str) -> None:
        async with self._manager.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM muted_queries WHERE query_hash = $1 AND db_id = $2",
                query_hash, db_id,
            )

    async def whitelist(self, query_hash: str, db_id: str) -> None:
        async with self._manager.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO muted_queries (query_hash, db_id, is_whitelisted)
                VALUES ($1, $2, true)
                ON CONFLICT (query_hash, db_id) DO UPDATE SET is_whitelisted = true
            """, query_hash, db_id)

    async def is_muted(self, query_hash: str, db_id: str) -> bool:
        async with self._manager.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT is_whitelisted FROM muted_queries WHERE query_hash = $1 AND db_id = $2",
                query_hash, db_id,
            )
        if row is None:
            return False
        # Whitelisted = in table with is_whitelisted=true → NOT muted
        return not row["is_whitelisted"]

    async def is_whitelisted(self, query_hash: str, db_id: str) -> bool:
        async with self._manager.pool.acquire() as conn:
            val = await conn.fetchval(
                "SELECT is_whitelisted FROM muted_queries WHERE query_hash = $1 AND db_id = $2",
                query_hash, db_id,
            )
        return bool(val)

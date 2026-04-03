import uuid
import asyncpg

from app.domain.repositories.connection_repository import IConnectionRepository
from app.domain.value_objects.connection_config import ConnectionConfig
from app.infrastructure.database.pool_manager import PoolManager


class PgConnectionRepository(IConnectionRepository):
    def __init__(self, pool_manager: PoolManager) -> None:
        self._pool_manager = pool_manager

    async def create(self, config: ConnectionConfig) -> str:
        db_id = str(uuid.uuid4())
        await self._pool_manager.create(
            db_id=db_id,
            host=config.host,
            port=config.port,
            database=config.database,
            user=config.user,
            password=config.password,
        )
        await self._validate_pg_stat_statements(db_id)
        return db_id

    async def _validate_pg_stat_statements(self, db_id: str) -> None:
        pool = self._pool_manager.get(db_id)
        async with pool.acquire() as conn:
            try:
                await conn.fetchval("SELECT count(*) FROM pg_stat_statements LIMIT 1")
            except (asyncpg.UndefinedTableError, asyncpg.UndefinedFunctionError):
                await self._pool_manager.close(db_id)
                raise RuntimeError(
                    "pg_stat_statements extension is not enabled on this database. "
                    "To enable it: (1) add 'pg_stat_statements' to shared_preload_libraries "
                    "in postgresql.conf (or RDS parameter group), restart the server, "
                    "then (2) run: CREATE EXTENSION pg_stat_statements;"
                )

    def exists(self, db_id: str) -> bool:
        return self._pool_manager.exists(db_id)

    async def close(self, db_id: str) -> None:
        await self._pool_manager.close(db_id)

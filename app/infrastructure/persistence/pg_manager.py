import asyncpg
from app.infrastructure.config import Settings


class AppPgManager:
    """
    asyncpg connection pool for the advisor app's own PostgreSQL database.
    Separate from the monitored-DB pools in PoolManager.
    """

    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    async def connect(self, settings: Settings) -> None:
        self._pool = await asyncpg.create_pool(
            dsn=settings.app_database_url,
            ssl="disable",      # advisor_db is always local — no SSL needed
            min_size=1,
            max_size=settings.db_pool_size,
            command_timeout=10,
        )

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("AppPgManager not connected. Call connect() first.")
        return self._pool

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

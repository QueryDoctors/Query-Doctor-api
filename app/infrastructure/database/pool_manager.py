import asyncpg
from typing import Dict


class PoolManager:
    """In-memory registry of asyncpg connection pools keyed by db_id."""

    def __init__(self) -> None:
        self._pools: Dict[str, asyncpg.Pool] = {}

    async def create(
        self,
        db_id: str,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        ssl: str = "prefer",
    ) -> None:
        pool = await asyncpg.create_pool(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            ssl=ssl,          # "prefer" = SSL if available (RDS), falls back if not (local)
            min_size=1,
            max_size=10,
            command_timeout=30,
        )
        self._pools[db_id] = pool

    def get(self, db_id: str) -> asyncpg.Pool:
        pool = self._pools.get(db_id)
        if pool is None:
            raise KeyError(f"No connection found for db_id: {db_id}")
        return pool

    def exists(self, db_id: str) -> bool:
        return db_id in self._pools

    def all_ids(self) -> list:
        return list(self._pools.keys())

    async def close(self, db_id: str) -> None:
        pool = self._pools.pop(db_id, None)
        if pool:
            await pool.close()

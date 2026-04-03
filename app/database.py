import asyncpg
import uuid
from typing import Dict

# In-memory registry: db_id → asyncpg.Pool
_pools: Dict[str, asyncpg.Pool] = {}


async def create_connection(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
) -> str:
    pool = await asyncpg.create_pool(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        min_size=1,
        max_size=10,
        command_timeout=10,
    )
    db_id = str(uuid.uuid4())
    _pools[db_id] = pool
    return db_id


async def get_pool(db_id: str) -> asyncpg.Pool:
    pool = _pools.get(db_id)
    if pool is None:
        raise KeyError(f"No connection found for db_id: {db_id}")
    return pool


async def close_connection(db_id: str) -> None:
    pool = _pools.pop(db_id, None)
    if pool:
        await pool.close()

import uuid
from typing import List, Optional

from app.domain.repositories.connection_store_repository import IConnectionStoreRepository
from app.domain.entities.saved_connection import SavedConnection
from app.infrastructure.persistence.pg_manager import AppPgManager
from app.infrastructure.persistence.encryptor import Encryptor


class PgConnectionStoreRepository(IConnectionStoreRepository):
    def __init__(self, manager: AppPgManager, encryptor: Encryptor) -> None:
        self._manager = manager
        self._encryptor = encryptor

    async def save(self, connection: SavedConnection) -> SavedConnection:
        encrypted = self._encryptor.encrypt(connection.password)
        async with self._manager.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO connections (id, user_id, name, host, port, database, db_user, password, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (name, user_id) DO UPDATE
                    SET host = EXCLUDED.host,
                        port = EXCLUDED.port,
                        database = EXCLUDED.database,
                        db_user = EXCLUDED.db_user,
                        password = EXCLUDED.password,
                        last_used = now()
            """,
                connection.id, connection.user_id, connection.name, connection.host,
                connection.port, connection.database, connection.user,
                encrypted, connection.created_at,
            )
        return connection

    async def get_by_id(self, connection_id: str) -> Optional[SavedConnection]:
        async with self._manager.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM connections WHERE id = $1", connection_id
            )
        return self._to_entity(row) if row else None

    async def list_all(self, user_id: str) -> List[SavedConnection]:
        async with self._manager.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM connections WHERE user_id = $1 ORDER BY created_at DESC",
                user_id,
            )
        return [self._to_entity(r) for r in rows]

    async def delete(self, connection_id: str, user_id: str) -> None:
        async with self._manager.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM connections WHERE id = $1 AND user_id = $2",
                connection_id, user_id,
            )

    async def touch(self, connection_id: str) -> None:
        async with self._manager.pool.acquire() as conn:
            await conn.execute(
                "UPDATE connections SET last_used = now() WHERE id = $1",
                connection_id,
            )

    def _to_entity(self, row) -> SavedConnection:
        return SavedConnection(
            id=row["id"],
            user_id=row["user_id"] or "",
            name=row["name"],
            host=row["host"],
            port=row["port"],
            database=row["database"],
            user=row["db_user"],
            password=self._encryptor.decrypt(row["password"]),
            created_at=row["created_at"],
            last_used=row["last_used"],
        )

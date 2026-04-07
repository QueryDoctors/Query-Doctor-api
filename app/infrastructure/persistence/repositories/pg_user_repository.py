from typing import Optional

from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.persistence.pg_manager import AppPgManager


class PgUserRepository(IUserRepository):

    def __init__(self, manager: AppPgManager) -> None:
        self._manager = manager

    async def create(self, user: User) -> User:
        async with self._manager.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (id, email, password_hash, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                user.id,
                user.email,
                user.password_hash,
                user.is_active,
                user.created_at,
                user.updated_at,
            )
        return user

    async def get_by_id(self, user_id: str) -> Optional[User]:
        async with self._manager.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return self._to_entity(row) if row else None

    async def get_by_email(self, email: str) -> Optional[User]:
        async with self._manager.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        return self._to_entity(row) if row else None

    def _to_entity(self, row) -> User:
        return User(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

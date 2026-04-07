from typing import Optional

from app.domain.entities.refresh_token import RefreshToken
from app.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from app.infrastructure.persistence.pg_manager import AppPgManager


class PgRefreshTokenRepository(IRefreshTokenRepository):

    def __init__(self, manager: AppPgManager) -> None:
        self._manager = manager

    async def create(self, token: RefreshToken) -> RefreshToken:
        async with self._manager.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at, created_at, revoked)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                token.id,
                token.user_id,
                token.token_hash,
                token.expires_at,
                token.created_at,
                token.revoked,
            )
        return token

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        async with self._manager.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM refresh_tokens WHERE token_hash = $1", token_hash
            )
        return self._to_entity(row) if row else None

    async def revoke(self, token_id: str) -> None:
        async with self._manager.pool.acquire() as conn:
            await conn.execute(
                "UPDATE refresh_tokens SET revoked = true WHERE id = $1", token_id
            )

    async def revoke_all_for_user(self, user_id: str) -> None:
        async with self._manager.pool.acquire() as conn:
            await conn.execute(
                "UPDATE refresh_tokens SET revoked = true WHERE user_id = $1", user_id
            )

    async def delete_expired(self) -> int:
        async with self._manager.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM refresh_tokens WHERE expires_at < now() OR revoked = true"
            )
        # asyncpg returns "DELETE N" — parse count
        return int(result.split()[-1])

    def _to_entity(self, row) -> RefreshToken:
        return RefreshToken(
            id=row["id"],
            user_id=row["user_id"],
            token_hash=row["token_hash"],
            expires_at=row["expires_at"],
            created_at=row["created_at"],
            revoked=row["revoked"],
        )

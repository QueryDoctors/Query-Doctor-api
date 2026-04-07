import hashlib

from app.domain.repositories.refresh_token_repository import IRefreshTokenRepository


class LogoutUserUseCase:

    def __init__(self, refresh_token_repo: IRefreshTokenRepository) -> None:
        self._rt_repo = refresh_token_repo

    async def execute(self, raw_token: str) -> None:
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        stored = await self._rt_repo.get_by_hash(token_hash)
        if stored is not None and not stored.revoked:
            await self._rt_repo.revoke(stored.id)

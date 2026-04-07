import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.application.dtos.auth_dto import AccessTokenResult, RefreshTokenRequest
from app.domain.entities.refresh_token import RefreshToken
from app.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from app.domain.repositories.user_repository import IUserRepository
from app.domain.services.jwt_service import IJwtService


class RefreshAccessTokenUseCase:

    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
        jwt_service: IJwtService,
        refresh_token_expire_days: int = 7,
    ) -> None:
        self._user_repo = user_repo
        self._rt_repo = refresh_token_repo
        self._jwt = jwt_service
        self._rt_expire_days = refresh_token_expire_days

    async def execute(self, request: RefreshTokenRequest) -> tuple[AccessTokenResult, str]:
        """Rotates the refresh token. Returns (AccessTokenResult, new_raw_refresh_token)."""
        token_hash = hashlib.sha256(request.raw_token.encode()).hexdigest()
        stored = await self._rt_repo.get_by_hash(token_hash)

        if stored is None:
            raise ValueError("Token not found")

        if stored.revoked:
            # Reuse of a revoked token — possible theft; invalidate all sessions
            await self._rt_repo.revoke_all_for_user(stored.user_id)
            raise ValueError("Token reuse detected — all sessions invalidated")

        if stored.expires_at < datetime.now(timezone.utc):
            raise ValueError("Refresh token expired")

        user = await self._user_repo.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise ValueError("User not found or inactive")

        # Rotate: revoke old, issue new
        await self._rt_repo.revoke(stored.id)

        new_raw = secrets.token_urlsafe(32)
        new_hash = hashlib.sha256(new_raw.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        new_rt = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=new_hash,
            expires_at=now + timedelta(days=self._rt_expire_days),
            created_at=now,
            revoked=False,
        )
        await self._rt_repo.create(new_rt)

        access_token = self._jwt.create_access_token(user.id, user.email)
        return AccessTokenResult(access_token=access_token, token_type="bearer"), new_raw

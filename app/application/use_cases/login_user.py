import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from app.application.dtos.auth_dto import AuthTokenResult, LoginRequest
from app.domain.entities.refresh_token import RefreshToken
from app.domain.repositories.refresh_token_repository import IRefreshTokenRepository
from app.domain.repositories.user_repository import IUserRepository
from app.domain.services.jwt_service import IJwtService
from app.domain.services.password_hasher import IPasswordHasher


class LoginUserUseCase:

    def __init__(
        self,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
        password_hasher: IPasswordHasher,
        jwt_service: IJwtService,
        refresh_token_expire_days: int = 7,
    ) -> None:
        self._user_repo = user_repo
        self._rt_repo = refresh_token_repo
        self._hasher = password_hasher
        self._jwt = jwt_service
        self._rt_expire_days = refresh_token_expire_days

    async def execute(self, request: LoginRequest) -> tuple[AuthTokenResult, str]:
        """Returns (AuthTokenResult, raw_refresh_token). raw_refresh_token is for cookie only."""
        user = await self._user_repo.get_by_email(request.email.lower().strip())
        if user is None or not user.is_active:
            raise ValueError("Invalid credentials")

        if not self._hasher.verify(request.password, user.password_hash):
            raise ValueError("Invalid credentials")

        access_token = self._jwt.create_access_token(user.id, user.email)

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        rt = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=now + timedelta(days=self._rt_expire_days),
            created_at=now,
            revoked=False,
        )
        await self._rt_repo.create(rt)

        result = AuthTokenResult(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            email=user.email,
        )
        return result, raw_token

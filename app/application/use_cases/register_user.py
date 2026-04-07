import uuid
from datetime import datetime, timezone

from app.application.dtos.auth_dto import RegisterUserRequest, UserCreatedResult
from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.domain.services.password_hasher import IPasswordHasher


class RegisterUserUseCase:

    def __init__(self, user_repo: IUserRepository, password_hasher: IPasswordHasher) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher

    async def execute(self, request: RegisterUserRequest) -> UserCreatedResult:
        existing = await self._user_repo.get_by_email(request.email)
        if existing is not None:
            raise ValueError("Email already registered")

        now = datetime.now(timezone.utc)
        user = User(
            id=str(uuid.uuid4()),
            email=request.email.lower().strip(),
            password_hash=self._password_hasher.hash(request.password),
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        await self._user_repo.create(user)
        return UserCreatedResult(user_id=user.id, email=user.email)

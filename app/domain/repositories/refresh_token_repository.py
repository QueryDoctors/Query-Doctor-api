from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.refresh_token import RefreshToken


class IRefreshTokenRepository(ABC):

    @abstractmethod
    async def create(self, token: RefreshToken) -> RefreshToken: ...

    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]: ...

    @abstractmethod
    async def revoke(self, token_id: str) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: str) -> None: ...

    @abstractmethod
    async def delete_expired(self) -> int: ...

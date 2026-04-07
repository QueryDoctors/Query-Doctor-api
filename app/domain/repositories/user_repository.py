from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.user import User


class IUserRepository(ABC):

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]: ...

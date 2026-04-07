from abc import ABC, abstractmethod


class IJwtService(ABC):

    @abstractmethod
    def create_access_token(self, user_id: str, email: str) -> str: ...

    @abstractmethod
    def decode_access_token(self, token: str) -> dict:
        """Decode and validate the token. Raises JWTError on invalid/expired token."""
        ...

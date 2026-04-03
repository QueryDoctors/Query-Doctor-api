from abc import ABC, abstractmethod
from app.domain.value_objects.connection_config import ConnectionConfig


class IConnectionRepository(ABC):

    @abstractmethod
    async def create(self, config: ConnectionConfig) -> str:
        """Create a new connection pool and return a db_id."""

    @abstractmethod
    def exists(self, db_id: str) -> bool:
        """Return True if a connection pool exists for db_id."""

    @abstractmethod
    async def close(self, db_id: str) -> None:
        """Close and remove the connection pool for db_id."""

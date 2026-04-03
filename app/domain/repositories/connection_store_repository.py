from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.saved_connection import SavedConnection


class IConnectionStoreRepository(ABC):

    @abstractmethod
    async def save(self, connection: SavedConnection) -> SavedConnection:
        """Persist a new saved connection (password pre-encrypted by caller)."""

    @abstractmethod
    async def get_by_id(self, connection_id: str) -> Optional[SavedConnection]:
        """Return a saved connection by id, or None."""

    @abstractmethod
    async def list_all(self) -> List[SavedConnection]:
        """Return all saved connections ordered by created_at DESC."""

    @abstractmethod
    async def delete(self, connection_id: str) -> None:
        """Delete a saved connection and all its snapshots (cascade)."""

    @abstractmethod
    async def touch(self, connection_id: str) -> None:
        """Update last_used to now."""

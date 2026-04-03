from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.snapshot import Snapshot


class ISnapshotRepository(ABC):

    @abstractmethod
    async def save(self, snapshot: Snapshot) -> Snapshot:
        """Persist a full snapshot including queries and recommendations."""

    @abstractmethod
    async def get_by_id(self, snapshot_id: str) -> Optional[Snapshot]:
        """Return a snapshot by id including nested queries and recommendations."""

    @abstractmethod
    async def list_by_connection(self, connection_id: str) -> List[Snapshot]:
        """Return the 50 most recent snapshots for a connection."""

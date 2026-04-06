from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Tuple


class IAnomalyTrackingRepository(ABC):

    @abstractmethod
    async def upsert(
        self, db_id: str, query_hash: str, first_seen_at: datetime, last_seen_at: datetime
    ) -> None: ...

    @abstractmethod
    async def get(
        self, db_id: str, query_hash: str
    ) -> Optional[Tuple[datetime, datetime]]: ...

    @abstractmethod
    async def delete(self, db_id: str, query_hash: str) -> None: ...

    @abstractmethod
    async def delete_stale(self, older_than_minutes: int) -> None: ...

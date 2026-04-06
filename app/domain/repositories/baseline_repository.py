from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.query_latency_snapshot import QueryLatencySnapshot


class IBaselineRepository(ABC):

    @abstractmethod
    async def save_snapshot(self, snapshot: QueryLatencySnapshot) -> None: ...

    @abstractmethod
    async def get_p95(
        self, db_id: str, query_hash: str, within_minutes: int
    ) -> Optional[float]: ...

    @abstractmethod
    async def get_snapshot_count(
        self, db_id: str, query_hash: str, within_seconds: int
    ) -> int: ...

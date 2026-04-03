from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.query_stat import QueryStat


class IQueryRepository(ABC):

    @abstractmethod
    async def fetch_slow(self, db_id: str) -> List[QueryStat]:
        """Top 10 queries sorted by mean execution time DESC."""

    @abstractmethod
    async def fetch_frequent(self, db_id: str) -> List[QueryStat]:
        """Top 10 queries sorted by call count DESC."""

    @abstractmethod
    async def fetch_heaviest(self, db_id: str) -> List[QueryStat]:
        """Top 10 queries sorted by total execution time DESC."""

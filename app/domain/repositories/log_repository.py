from abc import ABC, abstractmethod
from app.domain.entities.log_entry import LogEntry


class ILogRepository(ABC):
    @abstractmethod
    async def fetch(self, db_id: str) -> list[LogEntry]:
        ...

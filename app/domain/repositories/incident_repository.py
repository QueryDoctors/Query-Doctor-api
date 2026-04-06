from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.domain.entities.incident import Incident
from app.domain.value_objects.incident_status import IncidentStatus
from app.domain.value_objects.severity import Severity


class IIncidentRepository(ABC):

    @abstractmethod
    async def create(self, incident: Incident) -> Incident: ...

    @abstractmethod
    async def get_by_id(self, incident_id: str) -> Optional[Incident]: ...

    @abstractmethod
    async def list_by_db(self, db_id: str, limit: int = 50, offset: int = 0) -> List[Incident]: ...

    @abstractmethod
    async def count_by_db(self, db_id: str) -> int: ...

    @abstractmethod
    async def update_status(
        self, incident_id: str, status: IncidentStatus, timestamp: datetime
    ) -> None: ...

    @abstractmethod
    async def update_severity(
        self, incident_id: str, severity: Severity, latency_ms: float, ratio: float, last_updated: datetime
    ) -> None: ...

    @abstractmethod
    async def find_active_for_query(self, db_id: str, query_hash: str) -> Optional[Incident]: ...

    @abstractmethod
    async def find_recent_for_query(
        self, db_id: str, query_hash: str, within_minutes: int
    ) -> Optional[Incident]: ...

    @abstractmethod
    async def get_open_incidents(self, db_id: str) -> List[Incident]: ...

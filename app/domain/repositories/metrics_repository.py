from abc import ABC, abstractmethod
from app.domain.value_objects.database_metrics import DatabaseMetrics


class IMetricsRepository(ABC):

    @abstractmethod
    async def fetch(self, db_id: str) -> DatabaseMetrics:
        """Fetch a metrics snapshot for the given db_id."""

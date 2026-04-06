from datetime import datetime, timezone

from app.application.dtos.incident_dto import IncidentDTO
from app.domain.repositories.incident_repository import IIncidentRepository
from app.domain.value_objects.incident_status import IncidentStatus


class ResolveIncidentUseCase:

    def __init__(self, repo: IIncidentRepository) -> None:
        self._repo = repo

    async def execute(self, incident_id: str) -> IncidentDTO:
        incident = await self._repo.get_by_id(incident_id)
        if incident is None:
            raise KeyError(f"Incident not found: {incident_id}")

        now = datetime.now(tz=timezone.utc)
        await self._repo.update_status(incident_id, IncidentStatus.RESOLVED, now)

        return IncidentDTO(
            id=incident.id,
            db_id=incident.db_id,
            query_hash=incident.query_hash,
            query_text=incident.query_text,
            severity=incident.severity.value,
            status=IncidentStatus.RESOLVED.value,
            start_time=incident.start_time,
            last_updated=now,
            current_latency_ms=incident.current_latency_ms,
            baseline_latency_ms=incident.baseline_latency_ms,
            latency_ratio=incident.latency_ratio,
            calls_per_minute=incident.calls_per_minute,
            resolved_at=now,
            acknowledged_at=incident.acknowledged_at,
        )

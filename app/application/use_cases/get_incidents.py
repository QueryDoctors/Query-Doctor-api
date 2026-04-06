from app.application.dtos.incident_dto import IncidentDTO, IncidentsResult
from app.domain.repositories.incident_repository import IIncidentRepository


class GetIncidentsUseCase:

    def __init__(self, repo: IIncidentRepository) -> None:
        self._repo = repo

    async def execute(self, db_id: str, limit: int = 50, offset: int = 0) -> IncidentsResult:
        incidents = await self._repo.list_by_db(db_id, limit, offset)
        total = await self._repo.count_by_db(db_id)
        return IncidentsResult(
            incidents=[
                IncidentDTO(
                    id=i.id,
                    db_id=i.db_id,
                    query_hash=i.query_hash,
                    query_text=i.query_text,
                    severity=i.severity.value,
                    status=i.status.value,
                    start_time=i.start_time,
                    last_updated=i.last_updated,
                    current_latency_ms=i.current_latency_ms,
                    baseline_latency_ms=i.baseline_latency_ms,
                    latency_ratio=i.latency_ratio,
                    calls_per_minute=i.calls_per_minute,
                    resolved_at=i.resolved_at,
                    acknowledged_at=i.acknowledged_at,
                )
                for i in incidents
            ],
            total=total,
        )

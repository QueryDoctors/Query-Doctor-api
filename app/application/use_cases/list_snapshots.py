from app.domain.repositories.snapshot_repository import ISnapshotRepository
from app.domain.entities.snapshot import Snapshot
from app.application.dtos.snapshot_dto import (
    SnapshotResult, SnapshotQueryDTO, SnapshotRecommendationDTO, ListSnapshotsResult,
)


class ListSnapshotsUseCase:
    def __init__(self, repo: ISnapshotRepository) -> None:
        self._repo = repo

    async def execute(self, connection_id: str) -> ListSnapshotsResult:
        snapshots = await self._repo.list_by_connection(connection_id)
        return ListSnapshotsResult(snapshots=[_to_result(s) for s in snapshots])


def _to_result(s: Snapshot) -> SnapshotResult:
    return SnapshotResult(
        id=s.id,
        connection_id=s.connection_id,
        captured_at=s.captured_at,
        active_connections=s.active_connections,
        qps=s.qps,
        avg_query_time_ms=s.avg_query_time_ms,
        total_queries=s.total_queries,
        queries=[
            SnapshotQueryDTO(
                id=q.id, category=q.category, query=q.query,
                mean_time_ms=q.mean_time_ms, calls=q.calls,
                total_time_ms=q.total_time_ms, rows=q.rows,
            )
            for q in s.queries
        ],
        recommendations=[
            SnapshotRecommendationDTO(
                id=r.id, problem=r.problem, impact=r.impact,
                suggestion=r.suggestion, severity=r.severity,
            )
            for r in s.recommendations
        ],
    )

import uuid
from datetime import datetime, timezone

from app.domain.repositories.metrics_repository import IMetricsRepository
from app.domain.repositories.query_repository import IQueryRepository
from app.domain.repositories.snapshot_repository import ISnapshotRepository
from app.domain.services.recommendation_engine import RecommendationEngine
from app.domain.entities.snapshot import Snapshot, SnapshotQuery, SnapshotRecommendation
from app.application.dtos.snapshot_dto import (
    SnapshotResult, SnapshotQueryDTO, SnapshotRecommendationDTO,
)


class SaveSnapshotUseCase:
    def __init__(
        self,
        metrics_repo: IMetricsRepository,
        query_repo: IQueryRepository,
        snapshot_repo: ISnapshotRepository,
        engine: RecommendationEngine,
    ) -> None:
        self._metrics_repo = metrics_repo
        self._query_repo = query_repo
        self._snapshot_repo = snapshot_repo
        self._engine = engine

    async def execute(self, db_id: str, connection_id: str) -> SnapshotResult:
        metrics = await self._metrics_repo.fetch(db_id)
        slow = await self._query_repo.fetch_slow(db_id)
        frequent = await self._query_repo.fetch_frequent(db_id)
        heaviest = await self._query_repo.fetch_heaviest(db_id)
        recommendations = self._engine.generate(metrics, slow, frequent, heaviest)

        snapshot = Snapshot(
            id=str(uuid.uuid4()),
            connection_id=connection_id,
            captured_at=datetime.now(timezone.utc),
            active_connections=metrics.active_connections,
            qps=metrics.qps,
            avg_query_time_ms=metrics.avg_query_time_ms,
            total_queries=metrics.total_queries,
            queries=[
                SnapshotQuery(
                    id=str(uuid.uuid4()),
                    category=category,
                    query=q.query,
                    mean_time_ms=q.mean_time_ms,
                    calls=q.calls,
                    total_time_ms=q.total_time_ms,
                    rows=q.rows,
                )
                for category, qs in [("slow", slow), ("frequent", frequent), ("heaviest", heaviest)]
                for q in qs
            ],
            recommendations=[
                SnapshotRecommendation(
                    id=str(uuid.uuid4()),
                    problem=r.problem,
                    impact=r.impact,
                    suggestion=r.suggestion,
                    severity=r.severity.value,
                )
                for r in recommendations
            ],
        )

        saved = await self._snapshot_repo.save(snapshot)
        return _to_result(saved)


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

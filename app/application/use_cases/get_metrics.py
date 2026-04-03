from app.domain.repositories.metrics_repository import IMetricsRepository
from app.application.dtos.metrics_dto import MetricsResult


class GetMetricsUseCase:
    def __init__(self, metrics_repo: IMetricsRepository) -> None:
        self._metrics_repo = metrics_repo

    async def execute(self, db_id: str) -> MetricsResult:
        metrics = await self._metrics_repo.fetch(db_id)
        return MetricsResult(
            active_connections=metrics.active_connections,
            qps=metrics.qps,
            avg_query_time_ms=metrics.avg_query_time_ms,
            total_queries=metrics.total_queries,
        )

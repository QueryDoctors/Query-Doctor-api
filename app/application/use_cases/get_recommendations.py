from app.domain.repositories.metrics_repository import IMetricsRepository
from app.domain.repositories.query_repository import IQueryRepository
from app.domain.services.recommendation_engine import RecommendationEngine
from app.application.dtos.recommendation_dto import RecommendationDTO, RecommendationsResult


class GetRecommendationsUseCase:
    def __init__(
        self,
        metrics_repo: IMetricsRepository,
        query_repo: IQueryRepository,
        engine: RecommendationEngine,
    ) -> None:
        self._metrics_repo = metrics_repo
        self._query_repo = query_repo
        self._engine = engine

    async def execute(self, db_id: str) -> RecommendationsResult:
        metrics = await self._metrics_repo.fetch(db_id)
        slow = await self._query_repo.fetch_slow(db_id)
        frequent = await self._query_repo.fetch_frequent(db_id)
        heaviest = await self._query_repo.fetch_heaviest(db_id)

        recommendations = self._engine.generate(metrics, slow, frequent, heaviest)

        return RecommendationsResult(
            recommendations=[
                RecommendationDTO(
                    problem=r.problem,
                    impact=r.impact,
                    suggestion=r.suggestion,
                    severity=r.severity.value,
                )
                for r in recommendations
            ]
        )

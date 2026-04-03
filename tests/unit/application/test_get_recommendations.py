from unittest.mock import AsyncMock, MagicMock
import pytest

from app.application.use_cases.get_recommendations import GetRecommendationsUseCase
from app.domain.services.recommendation_engine import RecommendationEngine
from app.domain.value_objects.database_metrics import DatabaseMetrics
from app.domain.entities.query_stat import QueryStat
from app.domain.entities.recommendation import Recommendation
from app.domain.value_objects.severity import Severity


@pytest.fixture
def metrics():
    return DatabaseMetrics(active_connections=10, qps=50.0, avg_query_time_ms=30.0, total_queries=1000)


@pytest.fixture
def use_case(metrics):
    metrics_repo = AsyncMock()
    metrics_repo.fetch.return_value = metrics

    query_repo = AsyncMock()
    query_repo.fetch_slow.return_value = []
    query_repo.fetch_frequent.return_value = []
    query_repo.fetch_heaviest.return_value = []

    engine = MagicMock(spec=RecommendationEngine)
    engine.generate.return_value = [
        Recommendation(
            problem="Slow query detected",
            impact="High latency",
            suggestion="Add index",
            severity=Severity.HIGH,
        )
    ]

    return GetRecommendationsUseCase(metrics_repo, query_repo, engine), metrics_repo, query_repo, engine


async def test_returns_mapped_recommendations(use_case):
    uc, *_ = use_case
    result = await uc.execute("some-db-id")
    assert len(result.recommendations) == 1
    assert result.recommendations[0].problem == "Slow query detected"
    assert result.recommendations[0].severity == "high"


async def test_engine_called_with_correct_data(use_case, metrics):
    uc, metrics_repo, query_repo, engine = use_case
    await uc.execute("some-db-id")
    engine.generate.assert_called_once_with(metrics, [], [], [])


async def test_metrics_repo_called_with_db_id(use_case):
    uc, metrics_repo, *_ = use_case
    await uc.execute("test-id")
    metrics_repo.fetch.assert_called_once_with("test-id")


async def test_empty_recommendations_when_engine_returns_none(use_case):
    uc, _, _, engine = use_case
    engine.generate.return_value = []
    result = await uc.execute("some-db-id")
    assert result.recommendations == []

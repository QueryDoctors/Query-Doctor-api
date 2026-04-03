from unittest.mock import AsyncMock
import pytest

from app.application.use_cases.get_metrics import GetMetricsUseCase
from app.domain.value_objects.database_metrics import DatabaseMetrics


@pytest.fixture
def metrics_repo():
    repo = AsyncMock()
    repo.fetch.return_value = DatabaseMetrics(
        active_connections=12,
        qps=45.3,
        avg_query_time_ms=18.5,
        total_queries=102938,
    )
    return repo


async def test_returns_mapped_metrics(metrics_repo):
    uc = GetMetricsUseCase(metrics_repo)
    result = await uc.execute("db-id")
    assert result.active_connections == 12
    assert result.qps == 45.3
    assert result.avg_query_time_ms == 18.5
    assert result.total_queries == 102938


async def test_repo_called_with_db_id(metrics_repo):
    uc = GetMetricsUseCase(metrics_repo)
    await uc.execute("my-db-id")
    metrics_repo.fetch.assert_called_once_with("my-db-id")


async def test_propagates_key_error_from_repo(metrics_repo):
    metrics_repo.fetch.side_effect = KeyError("not found")
    uc = GetMetricsUseCase(metrics_repo)
    with pytest.raises(KeyError):
        await uc.execute("bad-id")

import pytest
from app.domain.entities.query_stat import QueryStat
from app.domain.value_objects.database_metrics import DatabaseMetrics


@pytest.fixture
def sample_metrics() -> DatabaseMetrics:
    return DatabaseMetrics(
        active_connections=10,
        qps=50.0,
        avg_query_time_ms=50.0,
        total_queries=5000,
    )


@pytest.fixture
def slow_query() -> QueryStat:
    return QueryStat(
        query="SELECT * FROM orders WHERE status = '?'",
        mean_time_ms=350.0,
        calls=200,
        total_time_ms=70_000.0,
        rows=500_000,
    )


@pytest.fixture
def fast_query() -> QueryStat:
    return QueryStat(
        query="SELECT id FROM users WHERE id = ?",
        mean_time_ms=1.5,
        calls=10_000,
        total_time_ms=15_000.0,
        rows=10_000,
    )

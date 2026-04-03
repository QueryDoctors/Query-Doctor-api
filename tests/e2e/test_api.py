from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.presentation.dependencies import (
    get_connect_use_case,
    get_metrics_use_case,
    get_queries_use_case,
    get_recommendations_use_case,
)
from app.application.dtos.connection_dto import ConnectResult
from app.application.dtos.metrics_dto import MetricsResult
from app.application.dtos.query_dto import QueriesResult
from app.application.dtos.recommendation_dto import RecommendationsResult, RecommendationDTO


@pytest.fixture
def client_with_fakes():
    connect_uc = AsyncMock()
    connect_uc.execute.return_value = ConnectResult(db_id="fake-id", status="connected")

    metrics_uc = AsyncMock()
    metrics_uc.execute.return_value = MetricsResult(
        active_connections=5, qps=20.0, avg_query_time_ms=15.0, total_queries=1000
    )

    queries_uc = AsyncMock()
    queries_uc.execute.return_value = QueriesResult(
        slow_queries=[], frequent_queries=[], heaviest_queries=[]
    )

    recs_uc = AsyncMock()
    recs_uc.execute.return_value = RecommendationsResult(
        recommendations=[
            RecommendationDTO(
                problem="Slow query detected",
                impact="High latency",
                suggestion="Add index",
                severity="high",
            )
        ]
    )

    app.dependency_overrides[get_connect_use_case] = lambda: connect_uc
    app.dependency_overrides[get_metrics_use_case] = lambda: metrics_uc
    app.dependency_overrides[get_queries_use_case] = lambda: queries_uc
    app.dependency_overrides[get_recommendations_use_case] = lambda: recs_uc

    yield

    app.dependency_overrides.clear()


async def test_health(client_with_fakes):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_connect_db_success(client_with_fakes):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/connect-db", json={
            "host": "localhost", "port": 5432,
            "database": "mydb", "user": "user", "password": "pass",
        })
    assert response.status_code == 200
    assert response.json()["db_id"] == "fake-id"
    assert response.json()["status"] == "connected"


async def test_get_metrics_success(client_with_fakes):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/metrics/fake-id")
    assert response.status_code == 200
    data = response.json()
    assert data["active_connections"] == 5
    assert data["qps"] == 20.0


async def test_get_metrics_not_found(client_with_fakes):
    from app.presentation.dependencies import get_metrics_use_case
    bad_uc = AsyncMock()
    bad_uc.execute.side_effect = KeyError("not found")
    app.dependency_overrides[get_metrics_use_case] = lambda: bad_uc

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/metrics/bad-id")
    assert response.status_code == 404


async def test_get_queries_success(client_with_fakes):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/queries/fake-id")
    assert response.status_code == 200
    data = response.json()
    assert "slow_queries" in data
    assert "frequent_queries" in data
    assert "heaviest_queries" in data


async def test_get_recommendations_success(client_with_fakes):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/recommendations/fake-id")
    assert response.status_code == 200
    recs = response.json()["recommendations"]
    assert len(recs) == 1
    assert recs[0]["severity"] == "high"

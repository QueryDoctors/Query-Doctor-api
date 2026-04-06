from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config import get_settings
from app.infrastructure.detection.scheduler import DetectionScheduler
from app.presentation.routers import connection, metrics, queries, recommendations
from app.presentation.routers import saved_connections, snapshots, logs
from app.presentation.routers import incidents as incidents_router
from app.presentation.dependencies import (
    get_app_pg_manager,
    get_ch_manager,
    get_pool_manager,
    get_incident_config,
    _incident_engine,
    _calculator,
)
from app.infrastructure.persistence.repositories.ch_baseline_repository import ChBaselineRepository
from app.infrastructure.persistence.repositories.pg_incident_repository import PgIncidentRepository
from app.infrastructure.persistence.repositories.pg_muted_query_repository import PgMutedQueryRepository
from app.infrastructure.persistence.repositories.pg_anomaly_tracking_repository import PgAnomalyTrackingRepository
from app.infrastructure.database.repositories.pg_query_repository import PgQueryRepository
from app.application.use_cases.run_detection_cycle import RunDetectionCycleUseCase

# ─── App-level singletons (shared across requests) ───────────────────────────
_app_pg_manager = get_app_pg_manager()
_ch_manager = get_ch_manager()
_pool_manager = get_pool_manager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    # Startup: connect to databases
    await _app_pg_manager.connect(settings)
    print(f"[startup] env={settings.env.value} | app DB connected")

    await _ch_manager.connect(settings)
    print(f"[startup] ClickHouse connected (db={settings.clickhouse_db})")

    # Build detection use case with singleton repos
    config = get_incident_config()
    detection_use_case = RunDetectionCycleUseCase(
        query_repo=PgQueryRepository(_pool_manager),
        baseline_repo=ChBaselineRepository(_ch_manager),
        incident_repo=PgIncidentRepository(_app_pg_manager),
        muted_repo=PgMutedQueryRepository(_app_pg_manager),
        anomaly_repo=PgAnomalyTrackingRepository(_app_pg_manager),
        engine=_incident_engine,
        calculator=_calculator,
        config=config,
    )
    scheduler = DetectionScheduler(
        detection_use_case=detection_use_case,
        pool_manager=_pool_manager,
        interval_seconds=settings.detection_interval_seconds,
    )
    await scheduler.start()

    yield

    # Shutdown
    await scheduler.stop()
    await _ch_manager.close()
    print("[shutdown] ClickHouse closed")
    await _app_pg_manager.close()
    print("[shutdown] app DB pool closed")


# ─── FastAPI app ──────────────────────────────────────────────────────────────
# Settings loaded lazily inside lifespan — safe to import in tests without .env
app = FastAPI(
    title="PostgreSQL Performance Advisor",
    version="1.0.0",
    description="Insight-driven PostgreSQL performance analysis tool",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connection.router)
app.include_router(metrics.router)
app.include_router(queries.router)
app.include_router(recommendations.router)
app.include_router(saved_connections.router)
app.include_router(snapshots.router)
app.include_router(logs.router)
app.include_router(incidents_router.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}

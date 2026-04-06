from fastapi import Depends

from app.infrastructure.database.pool_manager import PoolManager
from app.infrastructure.database.repositories.pg_connection_repository import PgConnectionRepository
from app.infrastructure.database.repositories.pg_metrics_repository import PgMetricsRepository
from app.infrastructure.database.repositories.pg_query_repository import PgQueryRepository
from app.infrastructure.persistence.pg_manager import AppPgManager
from app.infrastructure.persistence.ch_manager import ClickHouseManager
from app.infrastructure.persistence.encryptor import Encryptor
from app.infrastructure.persistence.repositories.pg_connection_store_repository import PgConnectionStoreRepository
from app.infrastructure.persistence.repositories.pg_snapshot_repository import PgSnapshotRepository
from app.infrastructure.persistence.repositories.pg_incident_repository import PgIncidentRepository
from app.infrastructure.persistence.repositories.ch_baseline_repository import ChBaselineRepository
from app.infrastructure.persistence.repositories.pg_muted_query_repository import PgMutedQueryRepository
from app.infrastructure.persistence.repositories.pg_anomaly_tracking_repository import PgAnomalyTrackingRepository
from app.infrastructure.config import get_settings
from app.domain.services.recommendation_engine import RecommendationEngine
from app.domain.services.incident_engine import IncidentEngine
from app.domain.services.baseline_calculator import BaselineCalculator
from app.domain.value_objects.incident_config import IncidentConfig
from app.application.use_cases.connect_database import ConnectDatabaseUseCase
from app.application.use_cases.get_metrics import GetMetricsUseCase
from app.application.use_cases.get_queries import GetQueriesUseCase
from app.application.use_cases.get_recommendations import GetRecommendationsUseCase
from app.application.use_cases.save_saved_connection import SaveSavedConnectionUseCase
from app.application.use_cases.get_saved_connection import GetSavedConnectionUseCase
from app.application.use_cases.list_saved_connections import ListSavedConnectionsUseCase
from app.application.use_cases.delete_saved_connection import DeleteSavedConnectionUseCase
from app.application.use_cases.save_snapshot import SaveSnapshotUseCase
from app.application.use_cases.get_snapshot import GetSnapshotUseCase
from app.application.use_cases.list_snapshots import ListSnapshotsUseCase
from app.application.use_cases.get_incidents import GetIncidentsUseCase
from app.application.use_cases.acknowledge_incident import AcknowledgeIncidentUseCase
from app.application.use_cases.resolve_incident import ResolveIncidentUseCase
from app.application.use_cases.mute_query import MuteQueryUseCase
from app.application.use_cases.unmute_query import UnmuteQueryUseCase
from app.application.use_cases.run_detection_cycle import RunDetectionCycleUseCase

# Singleton — one pool manager for the lifetime of the process
_pool_manager = PoolManager()
_engine = RecommendationEngine()
_incident_engine = IncidentEngine()
_calculator = BaselineCalculator()

# App-DB singletons — shared with main.py via import
_app_pg_manager = AppPgManager()
_ch_manager = ClickHouseManager()


def get_pool_manager() -> PoolManager:
    return _pool_manager


def get_app_pg_manager() -> AppPgManager:
    return _app_pg_manager


def get_ch_manager() -> ClickHouseManager:
    return _ch_manager


def get_encryptor() -> Encryptor:
    return Encryptor(get_settings().encryption_key)


def get_connection_store_repo(
    manager: AppPgManager = Depends(get_app_pg_manager),
    encryptor: Encryptor = Depends(get_encryptor),
) -> PgConnectionStoreRepository:
    return PgConnectionStoreRepository(manager, encryptor)


def get_snapshot_repo(
    manager: AppPgManager = Depends(get_app_pg_manager),
) -> PgSnapshotRepository:
    return PgSnapshotRepository(manager)


# ── Monitoring use cases ──────────────────────────────────────────────────────

def get_connect_use_case(
    pool_manager: PoolManager = Depends(get_pool_manager),
) -> ConnectDatabaseUseCase:
    return ConnectDatabaseUseCase(PgConnectionRepository(pool_manager))


def get_metrics_use_case(
    pool_manager: PoolManager = Depends(get_pool_manager),
) -> GetMetricsUseCase:
    return GetMetricsUseCase(PgMetricsRepository(pool_manager))


def get_queries_use_case(
    pool_manager: PoolManager = Depends(get_pool_manager),
) -> GetQueriesUseCase:
    return GetQueriesUseCase(PgQueryRepository(pool_manager))


def get_recommendations_use_case(
    pool_manager: PoolManager = Depends(get_pool_manager),
) -> GetRecommendationsUseCase:
    return GetRecommendationsUseCase(
        PgMetricsRepository(pool_manager),
        PgQueryRepository(pool_manager),
        _engine,
    )


# ── Persistence use cases ─────────────────────────────────────────────────────

def get_save_saved_connection_use_case(
    repo: PgConnectionStoreRepository = Depends(get_connection_store_repo),
) -> SaveSavedConnectionUseCase:
    return SaveSavedConnectionUseCase(repo)


def get_get_saved_connection_use_case(
    repo: PgConnectionStoreRepository = Depends(get_connection_store_repo),
) -> GetSavedConnectionUseCase:
    return GetSavedConnectionUseCase(repo)


def get_list_saved_connections_use_case(
    repo: PgConnectionStoreRepository = Depends(get_connection_store_repo),
) -> ListSavedConnectionsUseCase:
    return ListSavedConnectionsUseCase(repo)


def get_delete_saved_connection_use_case(
    repo: PgConnectionStoreRepository = Depends(get_connection_store_repo),
) -> DeleteSavedConnectionUseCase:
    return DeleteSavedConnectionUseCase(repo)


def get_save_snapshot_use_case(
    pool_manager: PoolManager = Depends(get_pool_manager),
    snapshot_repo: PgSnapshotRepository = Depends(get_snapshot_repo),
) -> SaveSnapshotUseCase:
    return SaveSnapshotUseCase(
        PgMetricsRepository(pool_manager),
        PgQueryRepository(pool_manager),
        snapshot_repo,
        _engine,
    )


def get_get_snapshot_use_case(
    repo: PgSnapshotRepository = Depends(get_snapshot_repo),
) -> GetSnapshotUseCase:
    return GetSnapshotUseCase(repo)


def get_list_snapshots_use_case(
    repo: PgSnapshotRepository = Depends(get_snapshot_repo),
) -> ListSnapshotsUseCase:
    return ListSnapshotsUseCase(repo)


# ── Logs use case ─────────────────────────────────────────────────────────────
from app.application.use_cases.get_live_logs import GetLiveLogsUseCase
from app.infrastructure.database.repositories.pg_log_repository import PgLogRepository


def get_live_logs_use_case(
    pool_manager: PoolManager = Depends(get_pool_manager),
) -> GetLiveLogsUseCase:
    return GetLiveLogsUseCase(PgLogRepository(pool_manager))


# ── Incident use cases ────────────────────────────────────────────────────────

def get_incident_repo(
    manager: AppPgManager = Depends(get_app_pg_manager),
) -> PgIncidentRepository:
    return PgIncidentRepository(manager)


def get_baseline_repo(
    ch: ClickHouseManager = Depends(get_ch_manager),
) -> ChBaselineRepository:
    return ChBaselineRepository(ch)


def get_muted_query_repo(
    manager: AppPgManager = Depends(get_app_pg_manager),
) -> PgMutedQueryRepository:
    return PgMutedQueryRepository(manager)


def get_anomaly_tracking_repo(
    manager: AppPgManager = Depends(get_app_pg_manager),
) -> PgAnomalyTrackingRepository:
    return PgAnomalyTrackingRepository(manager)


def get_incident_config() -> IncidentConfig:
    s = get_settings()
    return IncidentConfig(
        min_calls_per_minute=s.incident_min_calls_per_minute,
        min_spike_duration_seconds=s.incident_min_spike_duration_seconds,
        incident_trigger_minutes=s.incident_trigger_minutes,
        cooldown_minutes=s.incident_cooldown_minutes,
        auto_resolve_minutes=s.incident_auto_resolve_minutes,
        baseline_window_minutes=s.incident_baseline_window_minutes,
        detection_interval_seconds=s.detection_interval_seconds,
    )


def get_incidents_use_case(
    repo: PgIncidentRepository = Depends(get_incident_repo),
) -> GetIncidentsUseCase:
    return GetIncidentsUseCase(repo)


def get_acknowledge_incident_use_case(
    repo: PgIncidentRepository = Depends(get_incident_repo),
) -> AcknowledgeIncidentUseCase:
    return AcknowledgeIncidentUseCase(repo)


def get_resolve_incident_use_case(
    repo: PgIncidentRepository = Depends(get_incident_repo),
) -> ResolveIncidentUseCase:
    return ResolveIncidentUseCase(repo)


def get_mute_query_use_case(
    repo: PgMutedQueryRepository = Depends(get_muted_query_repo),
) -> MuteQueryUseCase:
    return MuteQueryUseCase(repo)


def get_unmute_query_use_case(
    repo: PgMutedQueryRepository = Depends(get_muted_query_repo),
) -> UnmuteQueryUseCase:
    return UnmuteQueryUseCase(repo)


def get_detection_use_case(
    pool_manager: PoolManager = Depends(get_pool_manager),
    baseline_repo: ChBaselineRepository = Depends(get_baseline_repo),
    incident_repo: PgIncidentRepository = Depends(get_incident_repo),
    muted_repo: PgMutedQueryRepository = Depends(get_muted_query_repo),
    anomaly_repo: PgAnomalyTrackingRepository = Depends(get_anomaly_tracking_repo),
) -> RunDetectionCycleUseCase:
    config = get_incident_config()
    return RunDetectionCycleUseCase(
        query_repo=PgQueryRepository(pool_manager),
        baseline_repo=baseline_repo,
        incident_repo=incident_repo,
        muted_repo=muted_repo,
        anomaly_repo=anomaly_repo,
        engine=_incident_engine,
        calculator=_calculator,
        config=config,
    )

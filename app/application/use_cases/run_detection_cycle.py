"""
RunDetectionCycleUseCase — orchestrates the full detection pipeline for one db_id.
Called every 10s by the DetectionScheduler.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List

from app.domain.entities.incident import Incident
from app.domain.entities.query_latency_snapshot import QueryLatencySnapshot
from app.domain.repositories.anomaly_tracking_repository import IAnomalyTrackingRepository
from app.domain.repositories.baseline_repository import IBaselineRepository
from app.domain.repositories.incident_repository import IIncidentRepository
from app.domain.repositories.muted_query_repository import IMutedQueryRepository
from app.domain.repositories.query_repository import IQueryRepository
from app.domain.services.baseline_calculator import BaselineCalculator
from app.domain.services.incident_engine import IncidentEngine
from app.domain.value_objects.incident_config import IncidentConfig
from app.domain.value_objects.incident_status import IncidentStatus
from app.infrastructure.detection.query_hasher import compute_query_hash

logger = logging.getLogger(__name__)


class RunDetectionCycleUseCase:

    def __init__(
        self,
        query_repo: IQueryRepository,
        baseline_repo: IBaselineRepository,
        incident_repo: IIncidentRepository,
        muted_repo: IMutedQueryRepository,
        anomaly_repo: IAnomalyTrackingRepository,
        engine: IncidentEngine,
        calculator: BaselineCalculator,
        config: IncidentConfig,
    ) -> None:
        self._query_repo = query_repo
        self._baseline_repo = baseline_repo
        self._incident_repo = incident_repo
        self._muted_repo = muted_repo
        self._anomaly_repo = anomaly_repo
        self._engine = engine
        self._calculator = calculator
        self._config = config

    async def execute(self, db_id: str) -> None:
        now = datetime.now(tz=timezone.utc)

        # 1. Fetch all query stats (deduplicated by query_hash)
        try:
            slow = await self._query_repo.fetch_slow(db_id)
            frequent = await self._query_repo.fetch_frequent(db_id)
            heaviest = await self._query_repo.fetch_heaviest(db_id)
        except Exception as exc:
            logger.warning(f"[detection] {db_id}: failed to fetch queries: {exc}")
            return

        # Merge and deduplicate by normalized query hash
        seen_hashes: set = set()
        all_queries = []
        for q in slow + frequent + heaviest:
            h = compute_query_hash(q.query)
            if h not in seen_hashes:
                seen_hashes.add(h)
                all_queries.append((h, q))

        # 2. Save latency snapshots to ClickHouse + process each query
        for query_hash, q in all_queries:
            if q.mean_time_ms is None or q.mean_time_ms <= 0:
                continue  # AC5: ignore missing data

            # Estimate calls/min from calls (pg_stat_statements is cumulative;
            # we use calls directly as a rough proxy for recent frequency)
            calls_per_min = float(q.calls) if q.calls else 0.0

            snapshot = QueryLatencySnapshot(
                db_id=db_id,
                query_hash=query_hash,
                query_text=q.query,
                mean_latency_ms=q.mean_time_ms,
                calls=q.calls,
                calls_per_minute=calls_per_min,
                captured_at=now,
            )
            try:
                await self._baseline_repo.save_snapshot(snapshot)
            except Exception as exc:
                logger.warning(f"[detection] {db_id}: failed to save snapshot: {exc}")
                continue

            await self._process_query(db_id, query_hash, q.query, q.mean_time_ms, calls_per_min, now)

        # 3. Auto-resolve open incidents where latency returned to normal
        await self._check_auto_resolve(db_id, seen_hashes, now)

        # 4. Clean up stale anomaly tracking entries (older than 3× trigger window)
        await self._anomaly_repo.delete_stale(self._config.incident_trigger_minutes * 3)

    async def _process_query(
        self,
        db_id: str,
        query_hash: str,
        query_text: str,
        latency_ms: float,
        calls_per_min: float,
        now: datetime,
    ) -> None:
        # Check mute/whitelist
        is_muted = await self._muted_repo.is_muted(query_hash, db_id)
        is_whitelisted = await self._muted_repo.is_whitelisted(query_hash, db_id)

        # Get baseline p95
        baseline_ms = await self._baseline_repo.get_p95(
            db_id, query_hash, self._config.baseline_window_minutes
        )

        # AC5 / AC6: no baseline yet → log and skip
        if baseline_ms is None:
            logger.debug(f"[detection] {db_id}/{query_hash}: no baseline yet, skipping")
            return

        # Check if abnormal
        if not self._engine.is_abnormal(latency_ms, baseline_ms):
            # Latency is normal — clear any anomaly tracking
            await self._anomaly_repo.delete(db_id, query_hash)
            return

        # Compute spike duration from anomaly tracking
        tracking = await self._anomaly_repo.get(db_id, query_hash)
        if tracking is None:
            first_seen = now
        else:
            first_seen, _ = tracking

        spike_duration_s = (now - first_seen).total_seconds()

        # Apply noise filter
        if self._engine.should_filter(
            calls_per_min, spike_duration_s, is_muted, is_whitelisted, self._config
        ):
            # Still update last_seen so we track the spike start time
            await self._anomaly_repo.upsert(db_id, query_hash, first_seen, now)
            return

        # Update anomaly tracking
        await self._anomaly_repo.upsert(db_id, query_hash, first_seen, now)

        # AC3: trigger only if persists ≥ incident_trigger_minutes
        trigger_duration_s = self._config.incident_trigger_minutes * 60
        if spike_duration_s < trigger_duration_s:
            return

        # AC13: cooldown — don't create new incident within cooldown window
        recent = await self._incident_repo.find_recent_for_query(
            db_id, query_hash, self._config.cooldown_minutes
        )
        if recent and recent.status == IncidentStatus.RESOLVED:
            return  # Still in cooldown after a resolved incident

        # AC12: merge — update existing active incident instead of creating new
        active = await self._incident_repo.find_active_for_query(db_id, query_hash)
        if active:
            ratio = self._engine.compute_ratio(latency_ms, baseline_ms)
            new_severity = self._engine.classify_severity(latency_ms, baseline_ms, calls_per_min, self._config)
            # AC19: escalate severity if worse
            if new_severity.sort_key() > active.severity.sort_key():
                await self._incident_repo.update_severity(active.id, new_severity, latency_ms, ratio, now)
            return

        # Create new incident
        ratio = self._engine.compute_ratio(latency_ms, baseline_ms)
        severity = self._engine.classify_severity(latency_ms, baseline_ms, calls_per_min, self._config)

        incident = Incident(
            id=str(uuid.uuid4()),
            db_id=db_id,
            query_hash=query_hash,
            query_text=query_text,
            severity=severity,
            status=IncidentStatus.OPEN,
            start_time=first_seen,
            last_updated=now,
            current_latency_ms=latency_ms,
            baseline_latency_ms=baseline_ms,
            latency_ratio=ratio,
            calls_per_minute=calls_per_min,
        )
        await self._incident_repo.create(incident)
        logger.info(f"[detection] NEW incident: db={db_id} hash={query_hash} severity={severity.value} ratio={ratio}x")

    async def _check_auto_resolve(self, db_id: str, current_hashes: set, now: datetime) -> None:
        """AC15: Auto-resolve open incidents where query latency returned to normal."""
        open_incidents = await self._incident_repo.get_open_incidents(db_id)
        for incident in open_incidents:
            # If this query_hash is not abnormal anymore (not in current cycle's abnormal set)
            tracking = await self._anomaly_repo.get(db_id, incident.query_hash)
            if tracking is None:
                # No anomaly tracking entry = latency is normal again
                # Check if it's been normal long enough
                last_updated = incident.last_updated
                normal_duration_s = (now - last_updated).total_seconds()
                if normal_duration_s >= self._config.auto_resolve_minutes * 60:
                    await self._incident_repo.update_status(
                        incident.id, IncidentStatus.RESOLVED, now
                    )
                    logger.info(f"[detection] AUTO-RESOLVED incident {incident.id}")

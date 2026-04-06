import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.domain.entities.incident import Incident
from app.domain.repositories.incident_repository import IIncidentRepository
from app.domain.value_objects.incident_status import IncidentStatus
from app.domain.value_objects.severity import Severity
from app.infrastructure.persistence.pg_manager import AppPgManager

_SEVERITY_ORDER = "CASE severity WHEN 'critical' THEN 4 WHEN 'high' THEN 3 WHEN 'medium' THEN 2 ELSE 1 END"


class PgIncidentRepository(IIncidentRepository):

    def __init__(self, manager: AppPgManager) -> None:
        self._manager = manager

    async def create(self, incident: Incident) -> Incident:
        async with self._manager.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO incidents (
                    id, db_id, query_hash, query_text, severity, status,
                    start_time, last_updated, current_latency_ms, baseline_latency_ms,
                    latency_ratio, calls_per_minute, resolved_at, acknowledged_at
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
            """,
                incident.id, incident.db_id, incident.query_hash, incident.query_text,
                incident.severity.value, incident.status.value,
                incident.start_time, incident.last_updated,
                incident.current_latency_ms, incident.baseline_latency_ms,
                incident.latency_ratio, incident.calls_per_minute,
                incident.resolved_at, incident.acknowledged_at,
            )
        return incident

    async def get_by_id(self, incident_id: str) -> Optional[Incident]:
        async with self._manager.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM incidents WHERE id = $1", incident_id
            )
        return self._to_entity(row) if row else None

    async def list_by_db(self, db_id: str, limit: int = 50, offset: int = 0) -> List[Incident]:
        async with self._manager.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT * FROM incidents
                WHERE db_id = $1
                ORDER BY {_SEVERITY_ORDER} DESC, start_time DESC
                LIMIT $2 OFFSET $3
            """, db_id, limit, offset)
        return [self._to_entity(r) for r in rows]

    async def count_by_db(self, db_id: str) -> int:
        async with self._manager.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT COUNT(*) FROM incidents WHERE db_id = $1", db_id
            )

    async def update_status(
        self, incident_id: str, status: IncidentStatus, timestamp: datetime
    ) -> None:
        col = "acknowledged_at" if status == IncidentStatus.INVESTIGATING else "resolved_at"
        async with self._manager.pool.acquire() as conn:
            await conn.execute(f"""
                UPDATE incidents
                SET status = $1, last_updated = $2, {col} = $3
                WHERE id = $4
            """, status.value, timestamp, timestamp, incident_id)

    async def update_severity(
        self, incident_id: str, severity: Severity, latency_ms: float, ratio: float, last_updated: datetime
    ) -> None:
        async with self._manager.pool.acquire() as conn:
            await conn.execute("""
                UPDATE incidents
                SET severity = $1, current_latency_ms = $2, latency_ratio = $3, last_updated = $4
                WHERE id = $5
            """, severity.value, latency_ms, ratio, last_updated, incident_id)

    async def find_active_for_query(self, db_id: str, query_hash: str) -> Optional[Incident]:
        async with self._manager.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM incidents
                WHERE db_id = $1 AND query_hash = $2
                  AND status IN ('open', 'investigating')
                ORDER BY start_time DESC
                LIMIT 1
            """, db_id, query_hash)
        return self._to_entity(row) if row else None

    async def find_recent_for_query(
        self, db_id: str, query_hash: str, within_minutes: int
    ) -> Optional[Incident]:
        async with self._manager.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM incidents
                WHERE db_id = $1 AND query_hash = $2
                  AND start_time > now() - ($3 * interval '1 minute')
                ORDER BY start_time DESC
                LIMIT 1
            """, db_id, query_hash, within_minutes)
        return self._to_entity(row) if row else None

    async def get_open_incidents(self, db_id: str) -> List[Incident]:
        async with self._manager.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM incidents
                WHERE db_id = $1 AND status IN ('open', 'investigating')
                ORDER BY start_time ASC
            """, db_id)
        return [self._to_entity(r) for r in rows]

    def _to_entity(self, row) -> Incident:
        return Incident(
            id=row["id"],
            db_id=row["db_id"],
            query_hash=row["query_hash"],
            query_text=row["query_text"],
            severity=Severity(row["severity"]),
            status=IncidentStatus(row["status"]),
            start_time=row["start_time"],
            last_updated=row["last_updated"],
            current_latency_ms=float(row["current_latency_ms"]),
            baseline_latency_ms=float(row["baseline_latency_ms"]),
            latency_ratio=float(row["latency_ratio"]),
            calls_per_minute=float(row["calls_per_minute"]),
            resolved_at=row["resolved_at"],
            acknowledged_at=row["acknowledged_at"],
        )

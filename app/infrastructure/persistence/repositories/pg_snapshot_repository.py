from typing import List, Optional

from app.domain.repositories.snapshot_repository import ISnapshotRepository
from app.domain.entities.snapshot import Snapshot, SnapshotQuery, SnapshotRecommendation
from app.infrastructure.persistence.pg_manager import AppPgManager


class PgSnapshotRepository(ISnapshotRepository):
    def __init__(self, manager: AppPgManager) -> None:
        self._manager = manager

    async def save(self, snapshot: Snapshot) -> Snapshot:
        async with self._manager.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO snapshots
                        (id, connection_id, captured_at, active_connections, qps, avg_query_time_ms, total_queries)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    snapshot.id, snapshot.connection_id, snapshot.captured_at,
                    snapshot.active_connections, snapshot.qps,
                    snapshot.avg_query_time_ms, snapshot.total_queries,
                )

                for q in snapshot.queries:
                    await conn.execute("""
                        INSERT INTO snapshot_queries
                            (id, snapshot_id, category, query, mean_time_ms, calls, total_time_ms, rows)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                        q.id, snapshot.id, q.category, q.query,
                        q.mean_time_ms, q.calls, q.total_time_ms, q.rows,
                    )

                for r in snapshot.recommendations:
                    await conn.execute("""
                        INSERT INTO snapshot_recommendations
                            (id, snapshot_id, problem, impact, suggestion, severity)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                        r.id, snapshot.id, r.problem,
                        r.impact, r.suggestion, r.severity,
                    )
        return snapshot

    async def get_by_id(self, snapshot_id: str) -> Optional[Snapshot]:
        async with self._manager.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM snapshots WHERE id = $1", snapshot_id)
            if not row:
                return None
            queries = await conn.fetch(
                "SELECT * FROM snapshot_queries WHERE snapshot_id = $1", snapshot_id
            )
            recs = await conn.fetch(
                "SELECT * FROM snapshot_recommendations WHERE snapshot_id = $1", snapshot_id
            )
        return self._to_entity(row, queries, recs)

    async def list_by_connection(self, connection_id: str) -> List[Snapshot]:
        async with self._manager.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM snapshots
                WHERE connection_id = $1
                ORDER BY captured_at DESC
                LIMIT 50
            """, connection_id)
            result = []
            for row in rows:
                queries = await conn.fetch(
                    "SELECT * FROM snapshot_queries WHERE snapshot_id = $1", row["id"]
                )
                recs = await conn.fetch(
                    "SELECT * FROM snapshot_recommendations WHERE snapshot_id = $1", row["id"]
                )
                result.append(self._to_entity(row, queries, recs))
        return result

    def _to_entity(self, row, query_rows, rec_rows) -> Snapshot:
        return Snapshot(
            id=row["id"],
            connection_id=row["connection_id"],
            captured_at=row["captured_at"],
            active_connections=row["active_connections"],
            qps=float(row["qps"]) if row["qps"] else None,
            avg_query_time_ms=float(row["avg_query_time_ms"]) if row["avg_query_time_ms"] else None,
            total_queries=row["total_queries"],
            queries=[
                SnapshotQuery(
                    id=q["id"],
                    category=q["category"],
                    query=q["query"],
                    mean_time_ms=float(q["mean_time_ms"]) if q["mean_time_ms"] else None,
                    calls=q["calls"],
                    total_time_ms=float(q["total_time_ms"]) if q["total_time_ms"] else None,
                    rows=q["rows"],
                )
                for q in query_rows
            ],
            recommendations=[
                SnapshotRecommendation(
                    id=r["id"],
                    problem=r["problem"],
                    impact=r["impact"],
                    suggestion=r["suggestion"],
                    severity=r["severity"],
                )
                for r in rec_rows
            ],
        )

from app.domain.repositories.metrics_repository import IMetricsRepository
from app.domain.value_objects.database_metrics import DatabaseMetrics
from app.infrastructure.database.pool_manager import PoolManager


class PgMetricsRepository(IMetricsRepository):
    def __init__(self, pool_manager: PoolManager) -> None:
        self._pool_manager = pool_manager

    async def fetch(self, db_id: str) -> DatabaseMetrics:
        pool = self._pool_manager.get(db_id)
        async with pool.acquire() as conn:
            active_connections = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity"
            )

            row = await conn.fetchrow("""
                SELECT
                    coalesce(sum(calls), 0)::bigint AS total_queries,
                    greatest(
                        extract(epoch FROM (now() - pg_postmaster_start_time()))::float,
                        1
                    ) AS uptime_seconds
                FROM pg_stat_statements
            """)

            total_queries = int(row["total_queries"])
            qps = round(total_queries / float(row["uptime_seconds"]), 2)

            avg_query_time = await conn.fetchval("""
                SELECT coalesce(round(avg(mean_exec_time)::numeric, 2), 0)
                FROM pg_stat_statements
                WHERE calls > 0
            """)

        return DatabaseMetrics(
            active_connections=int(active_connections),
            qps=qps,
            avg_query_time_ms=float(avg_query_time),
            total_queries=total_queries,
        )

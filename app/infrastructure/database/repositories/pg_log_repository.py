from app.domain.entities.log_entry import LogEntry
from app.domain.repositories.log_repository import ILogRepository
from app.infrastructure.database.pool_manager import PoolManager


class PgLogRepository(ILogRepository):
    def __init__(self, pool_manager: PoolManager) -> None:
        self._pool_manager = pool_manager

    async def fetch(self, db_id: str) -> list[LogEntry]:
        pool = self._pool_manager.get(db_id)
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    pid,
                    COALESCE(usename, '')           AS username,
                    COALESCE(application_name, '')  AS application_name,
                    COALESCE(state, 'unknown')       AS state,
                    LEFT(COALESCE(query, ''), 500)   AS query,
                    CASE
                        WHEN query_start IS NOT NULL
                        THEN ROUND(
                            EXTRACT(EPOCH FROM (now() - query_start))::numeric * 1000,
                            2
                        )::float
                        ELSE NULL
                    END                             AS duration_ms,
                    wait_event_type,
                    wait_event,
                    query_start
                FROM pg_stat_activity
                WHERE datname = current_database()
                  AND pid != pg_backend_pid()
                  AND state IS NOT NULL
                  AND state != 'idle'
                ORDER BY
                    CASE state
                        WHEN 'active'                       THEN 0
                        WHEN 'idle in transaction'          THEN 1
                        WHEN 'idle in transaction (aborted)' THEN 2
                        ELSE 3
                    END,
                    duration_ms DESC NULLS LAST
                LIMIT 100
            """)

        return [
            LogEntry(
                pid=row["pid"],
                username=row["username"],
                application_name=row["application_name"],
                state=row["state"],
                query=row["query"] or None,
                duration_ms=row["duration_ms"],
                wait_event_type=row["wait_event_type"],
                wait_event=row["wait_event"],
                query_start=row["query_start"],
            )
            for row in rows
        ]

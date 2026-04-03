# Memory: capture-snapshot

## Persisted State

- `snapshots` table: id, connection_id (FK), captured_at, active_connections, qps, avg_query_time_ms, total_queries
- `snapshot_queries` table: id, snapshot_id (FK), category, query, mean_time_ms, calls, total_time_ms, rows
- `snapshot_recommendations` table: id, snapshot_id (FK), problem, impact, suggestion, severity

## Known State

- Snapshot save uses a single `asyncpg` connection with `conn.transaction()` — all 3 inserts atomic
- `PgSnapshotRepository` uses `AppPgManager` (advisor_db), not `PoolManager` (monitored DB)
- `SaveSnapshotUseCase` uses BOTH: `PgMetricsRepository` + `PgQueryRepository` (monitored DB) AND `PgSnapshotRepository` (advisor_db)

## Edge Cases

- If `pg_stat_statements` is not enabled on the monitored DB: queries list will be empty
- If monitored DB has zero statements: recommendations list may be empty
- `rows` field on snapshot_queries is nullable — some queries don't return row counts

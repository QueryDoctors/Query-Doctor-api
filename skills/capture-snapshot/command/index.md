# Command: capture-snapshot (Backend)

## Files (already implemented)

```
domain/entities/snapshot.py                                    ← Snapshot, SnapshotQuery, SnapshotRecommendation
domain/repositories/snapshot_repository.py                     ← ISnapshotRepository (ABC)
application/dtos/snapshot_dto.py                               ← SnapshotResult, SnapshotQueryDTO, SnapshotRecommendationDTO
application/use_cases/save_snapshot.py                         ← SaveSnapshotUseCase
infrastructure/persistence/repositories/pg_snapshot_repository.py ← PgSnapshotRepository
presentation/schemas/snapshot_schema.py                        ← SnapshotResponse, SnapshotQuerySchema, SnapshotRecommendationSchema
presentation/routers/snapshots.py                              ← POST /snapshots/{db_id}
presentation/dependencies.py                                   ← get_save_snapshot_use_case
app/main.py                                                    ← snapshots.router registered
```

## Implementation Notes

**Use Case composition** (`SaveSnapshotUseCase.__init__`):
- `metrics_repo: IMetricsRepository` — from `infrastructure/database/` (monitored DB)
- `query_repo: IQueryRepository` — from `infrastructure/database/` (monitored DB)
- `snapshot_repo: ISnapshotRepository` — from `infrastructure/persistence/` (advisor_db)
- `engine: RecommendationEngine` — singleton from dependencies.py

**Persistence** (`PgSnapshotRepository.save`):
- One `asyncpg` connection, one `conn.transaction()`
- Insert order: snapshot → snapshot_queries (per item) → snapshot_recommendations (per item)
- All IDs are `str(uuid.uuid4())` generated in use case before calling repo

**DI wiring** (`dependencies.py`):
- `get_save_snapshot_use_case` composes `PgMetricsRepository(pool_manager)` + `PgQueryRepository(pool_manager)` + `PgSnapshotRepository(app_pg_manager)` + `_engine`

## Response Shape

```
POST /snapshots/{db_id}?connection_id=<uuid>

201 SnapshotResponse {
  id, connection_id, captured_at,
  active_connections?, qps?, avg_query_time_ms?, total_queries?,
  queries: [{ id, category, query, mean_time_ms?, calls?, total_time_ms?, rows? }],
  recommendations: [{ id, problem, impact, suggestion, severity }]
}

404 { detail: "Active database connection not found" }  ← db_id not in PoolManager
500 { detail: "<error message>" }
```

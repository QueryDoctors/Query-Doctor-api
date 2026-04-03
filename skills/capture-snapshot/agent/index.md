# Agent: capture-snapshot

## Orchestration (SaveSnapshotUseCase)

1. Fetch live metrics → `IMetricsRepository.fetch(db_id)`
2. Fetch slow queries → `IQueryRepository.fetch_slow(db_id)`
3. Fetch frequent queries → `IQueryRepository.fetch_frequent(db_id)`
4. Fetch heaviest queries → `IQueryRepository.fetch_heaviest(db_id)`
5. Run recommendation engine → `RecommendationEngine.generate(metrics, slow, frequent, heaviest)`
6. Build `Snapshot` entity with generated UUID + UTC timestamp
7. Persist → `ISnapshotRepository.save(snapshot)` (atomic transaction)
8. Return `SnapshotResult` DTO

## Error Paths

- `db_id` not in PoolManager → `KeyError` → HTTP 404
- asyncpg connection failure → `Exception` → HTTP 500
- `connection_id` FK violation → `Exception` → HTTP 500

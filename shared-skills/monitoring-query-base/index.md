---
name: monitoring-query-base
type: shared-skill
layer: backend
version: 1.0
last_updated: 2026-04-03
used_by: [capture-snapshot]
---

# Shared Skill: monitoring-query-base

Reusable pattern for any feature that queries the user's monitored PostgreSQL via PoolManager.

## Pattern: db_id Lookup + 404

```python
@router.get("/{db_id}", ...)
async def my_endpoint(db_id: str, use_case = Depends(...)):
    try:
        result = await use_case.execute(db_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Active database connection not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
```

- `KeyError` raised by `PoolManager` when `db_id` not in pool → always 404
- All other exceptions → 500

## Pattern: PoolManager Injection

```python
class PgXxxRepository(IXxxRepository):
    def __init__(self, pool_manager: PoolManager) -> None:
        self._pool_manager = pool_manager

    async def fetch(self, db_id: str):
        pool = self._pool_manager.get(db_id)  # raises KeyError if missing
        async with pool.acquire() as conn:
            return await conn.fetch(QUERY)
```

## Pattern: SQL Query Rules

- All SQL: parameterized with `$1`, `$2` — never f-strings
- All queries target `pg_stat_statements` — validate it exists on connect
- Normalize query text: strip literals and numbers before display

## Files Involved

- `infrastructure/database/pool_manager.py` — PoolManager
- `infrastructure/database/repositories/pg_xxx_repository.py` — concrete repo
- `domain/repositories/xxx_repository.py` — IXxxRepository ABC
- `presentation/dependencies.py` — `get_pool_manager()` + repo DI provider

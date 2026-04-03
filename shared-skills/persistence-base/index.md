---
name: persistence-base
type: shared-skill
layer: backend
version: 1.0
last_updated: 2026-04-03
used_by: [capture-snapshot]
---

# Shared Skill: persistence-base

Reusable pattern for any feature that writes to advisor_db via AppPgManager.

## Pattern: Atomic Multi-Table Insert

```
async def save(entity) -> Entity:
    async with self._manager.pool.acquire() as conn:
        async with conn.transaction():
            # 1. INSERT parent row
            # 2. INSERT child rows (loop)
            # 3. INSERT related rows (loop)
    return entity
```

**Rules:**
- Always use `conn.transaction()` — all inserts atomic or none
- Insert order: parent → children (FK constraint direction)
- All IDs: `str(uuid.uuid4())` generated in use case before calling repo
- `captured_at` / `created_at`: `datetime.now(timezone.utc)` in use case

## Pattern: AppPgManager Injection

```python
class PgXxxRepository(IXxxRepository):
    def __init__(self, manager: AppPgManager) -> None:
        self._manager = manager
```

- `AppPgManager` singleton shared via `get_app_pg_manager()` in `dependencies.py`
- `manager.pool` raises `RuntimeError` if not connected — surfaces as 500

## Pattern: UUID Entity Construction (use case level)

```python
entity = MyEntity(
    id=str(uuid.uuid4()),
    created_at=datetime.now(timezone.utc),
    # ... other fields from input DTO
)
saved = await self._repo.save(entity)
return _to_dto(saved)
```

## Files Involved

- `infrastructure/persistence/pg_manager.py` — AppPgManager
- `infrastructure/persistence/repositories/pg_xxx_repository.py` — concrete repo
- `domain/repositories/xxx_repository.py` — IXxxRepository ABC
- `presentation/dependencies.py` — `get_app_pg_manager()` + repo DI provider

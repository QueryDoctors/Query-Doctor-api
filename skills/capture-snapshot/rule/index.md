# Rules: capture-snapshot

## Domain Rules

> See `backend/shared-skills/domain-rules-base/index.md` — all 5 thresholds and severity values are defined there.
> Do not duplicate them here.

## Persistence Rules

- Snapshot save is atomic — uses `conn.transaction()` across 3 tables
- Category values: `slow` | `frequent` | `heaviest` (CHECK constraint enforced in DB)
- Severity values: `high` | `medium` | `low` (CHECK constraint enforced in DB)
- `connection_id` must reference an existing row in `connections` table

## API Constraints

- `db_id` must be registered in `PoolManager` (active monitored connection)
- `connection_id` passed as query param — not in body
- Returns 404 if `db_id` not found in pool (raises KeyError)

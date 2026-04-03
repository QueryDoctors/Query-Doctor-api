---
version: 1.0
last_updated: 2026-04-03
extends:
  - backend/shared-skills/monitoring-query-base   ← db_id lookup, KeyError→404, PoolManager injection
  - backend/shared-skills/persistence-base        ← atomic tx, UUID gen, AppPgManager injection
  - backend/shared-skills/domain-rules-base       ← recommendation thresholds, severity enum
note: Do NOT duplicate patterns from extended shared-skills. Only document what is unique to this feature.
---

# Skill: capture-snapshot

**Capability**: Capture a full performance snapshot for a connected PostgreSQL database — metrics, categorized queries, and recommendations — and persist it to advisor_db.

**Endpoint**: `POST /snapshots/{db_id}?connection_id={connection_id}`

**Domain Entities**: `Snapshot`, `SnapshotQuery`, `SnapshotRecommendation`

**Repository Interface**: `ISnapshotRepository`

**Use Case**: `SaveSnapshotUseCase`

**Concrete Repo**: `PgSnapshotRepository`

**DI Provider**: `get_save_snapshot_use_case`

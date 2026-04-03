---
name: domain-rules-base
type: shared-skill
layer: backend
version: 1.0
last_updated: 2026-04-03
used_by: [capture-snapshot]
---

# Shared Skill: domain-rules-base

Canonical recommendation engine thresholds and severity values. Single source of truth for domain logic — never duplicate these in skill rule files.

## Recommendation Engine Rules

| Rule | Condition | Severity |
|------|-----------|----------|
| Slow query | `mean_time_ms > 200` AND `calls > 100` | `high` |
| High total time | top of heaviest list | `medium` |
| Full table scan | `rows / calls > 10_000` | `high` |
| Too many connections | `active_connections > 80` | `high` |
| Low QPS + high latency | `qps < 10` AND `avg_query_time_ms > 500` | `medium` |

## Severity Values (backend canonical)

```python
class Severity(str, Enum):
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"
```

Stored as lowercase strings in DB. FE maps to `critical / warning / info` in service layer.

## DB Constraints (enforced by CHECK in schema)

```sql
CHECK (category IN ('slow', 'frequent', 'heaviest'))
CHECK (severity  IN ('high', 'medium', 'low'))
```

Any new feature adding recommendations MUST use these exact values.

## Engine Location

`domain/services/recommendation_engine.py` — pure function, zero I/O.
Input: `DatabaseMetrics` + `List[QueryStat]`
Output: `List[Recommendation]`

Do NOT add new rule files to individual skills. Add rules to the engine and reference this shared skill.

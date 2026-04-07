"""
Demo seed script — populates ClickHouse + PostgreSQL with realistic history.

Usage:
    cd backend
    source venv/bin/activate
    ENV_FILE=.env.local python scripts/seed_demo.py

What it creates:
  - ClickHouse: 12h of query latency snapshots (every 10s) for 5 demo queries
  - PostgreSQL incidents: 3 demo incidents (open, investigating, resolved)
  - PostgreSQL connections: 1 demo connection so detector sees monitored_dbs=1
"""
import os
import uuid
import hashlib
import re
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Load env ──────────────────────────────────────────────────────────────────
env_file = os.environ.get("ENV_FILE", ".env.local")
if Path(env_file).exists():
    for line in Path(env_file).read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

import clickhouse_connect
import asyncpg
import asyncio
from cryptography.fernet import Fernet

# ── Config ────────────────────────────────────────────────────────────────────
CH_HOST     = os.getenv("CLICKHOUSE_HOST", "localhost")
CH_PORT     = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CH_DB       = os.getenv("CLICKHOUSE_DB", "query-doctor-local")
CH_USER     = os.getenv("CLICKHOUSE_USER", "admin")
CH_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "admin123")
PG_DSN      = os.getenv("APP_DATABASE_URL")
ENC_KEY     = os.getenv("ENCRYPTION_KEY")

DEMO_DB_ID   = "demo-" + str(uuid.uuid4())[:8]
DEMO_DB_NAME = "demo-postgres"

# ── Demo queries ──────────────────────────────────────────────────────────────
QUERIES = [
    {
        "text": "SELECT u.*, p.* FROM users u JOIN profiles p ON u.id = p.user_id WHERE u.created_at > $1 ORDER BY u.id DESC",
        "base_ms": 820,   # already slow — will show as at-risk
        "spike_at": 3,    # hour offset when spike happens
    },
    {
        "text": "SELECT count(*) FROM orders WHERE status = $1 AND created_at BETWEEN $2 AND $3",
        "base_ms": 45,
        "spike_at": None,
    },
    {
        "text": "UPDATE sessions SET last_seen = $1, metadata = $2 WHERE token = $3",
        "base_ms": 12,
        "spike_at": None,
    },
    {
        "text": "SELECT p.id, p.name, avg(r.score) FROM products p LEFT JOIN reviews r ON p.id = r.product_id GROUP BY p.id, p.name HAVING count(r.id) > $1 ORDER BY avg(r.score) DESC LIMIT $2",
        "base_ms": 380,
        "spike_at": 8,    # spikes at hour 8 (most recent — should trigger incident)
    },
    {
        "text": "DELETE FROM audit_logs WHERE created_at < $1 AND archived = $2",
        "base_ms": 95,
        "spike_at": None,
    },
]


def normalize_query(q: str) -> str:
    n = re.sub(r"'[^']*'", "?", q)
    n = re.sub(r"\b\d+\b", "?", n)
    return " ".join(n.lower().split())


def query_hash(q: str) -> str:
    return hashlib.sha256(normalize_query(q).encode()).hexdigest()[:16]


# ── ClickHouse seed ───────────────────────────────────────────────────────────
def seed_clickhouse():
    client = clickhouse_connect.get_client(
        host=CH_HOST, port=CH_PORT,
        username=CH_USER, password=CH_PASSWORD,
    )
    now = datetime.now(tz=timezone.utc)
    interval_s = 10
    hours_back  = 12
    total_rows  = (hours_back * 3600) // interval_s  # 4320 rows per query

    print(f"[clickhouse] seeding {total_rows} snapshots × {len(QUERIES)} queries …")

    rows = []
    for q in QUERIES:
        h = query_hash(q["text"])
        for i in range(total_rows):
            ts = now - timedelta(seconds=interval_s * (total_rows - i))
            hour_offset = (now - ts).total_seconds() / 3600

            # Simulate a latency spike at spike_at hour
            if q["spike_at"] and abs(hour_offset - q["spike_at"]) < 0.5:
                jitter_ms = q["base_ms"] * random.uniform(4, 7)
            else:
                jitter_ms = q["base_ms"] * random.uniform(0.8, 1.3)

            calls = random.randint(50, 300)
            rows.append([
                DEMO_DB_ID,
                h,
                q["text"],
                round(jitter_ms, 4),
                calls,
                float(calls),
                ts.replace(tzinfo=None),   # ClickHouse DateTime — no tz
            ])

    client.insert(
        f"`{CH_DB}`.query_latency_snapshots",
        rows,
        column_names=["db_id", "query_hash", "query_text",
                      "mean_latency_ms", "calls", "calls_per_minute", "captured_at"],
    )
    print(f"[clickhouse] inserted {len(rows)} rows ✓")


# ── PostgreSQL seed ───────────────────────────────────────────────────────────
async def seed_postgres():
    conn = await asyncpg.connect(dsn=PG_DSN, ssl="disable")
    fernet = Fernet(ENC_KEY.encode())
    now = datetime.now(tz=timezone.utc)

    # 1. Demo connection (so detector sees monitored_dbs=1)
    existing = await conn.fetchval(
        "SELECT id FROM connections WHERE name = $1", DEMO_DB_NAME
    )
    if existing:
        print(f"[postgres] demo connection already exists ({existing}) — skipping")
        conn_id = existing
    else:
        conn_id = str(uuid.uuid4())
        encrypted_pw = fernet.encrypt(b"demo-password").decode()
        await conn.execute("""
            INSERT INTO connections (id, name, host, port, database, db_user, password, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, conn_id, DEMO_DB_NAME, "localhost", 5432,
            "demo_db", "demo_user", encrypted_pw, now)
        print(f"[postgres] demo connection created: {conn_id}")

    # Use the real conn_id as db_id for incidents
    db_id = conn_id

    # 2. Demo incidents
    incident_specs = [
        {
            "query": QUERIES[0]["text"],
            "severity": "high",
            "status": "open",
            "latency": 4800.0,
            "baseline": 820.0,
            "ago_min": 3,
        },
        {
            "query": QUERIES[3]["text"],
            "severity": "critical",
            "status": "investigating",
            "latency": 12400.0,
            "baseline": 380.0,
            "ago_min": 25,
        },
        {
            "query": QUERIES[1]["text"],
            "severity": "medium",
            "status": "resolved",
            "latency": 920.0,
            "baseline": 45.0,
            "ago_min": 90,
        },
    ]

    created = 0
    for spec in incident_specs:
        h = query_hash(spec["query"])
        exists = await conn.fetchval(
            "SELECT id FROM incidents WHERE db_id=$1 AND query_hash=$2 AND status=$3",
            db_id, h, spec["status"],
        )
        if exists:
            continue
        start = now - timedelta(minutes=spec["ago_min"])
        ratio = round(spec["latency"] / spec["baseline"], 2)
        inc_id = str(uuid.uuid4())
        resolved_at = (now - timedelta(minutes=5)) if spec["status"] == "resolved" else None
        acknowledged_at = now if spec["status"] == "investigating" else None
        await conn.execute("""
            INSERT INTO incidents (
                id, db_id, query_hash, query_text, severity, status,
                start_time, last_updated, current_latency_ms, baseline_latency_ms,
                latency_ratio, calls_per_minute, resolved_at, acknowledged_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
        """,
            inc_id, db_id, h, spec["query"],
            spec["severity"], spec["status"],
            start, now,
            spec["latency"], spec["baseline"],
            ratio, 180.0,
            resolved_at, acknowledged_at,
        )
        created += 1

    print(f"[postgres] created {created} demo incidents ✓")
    await conn.close()


async def main():
    seed_clickhouse()
    await seed_postgres()
    print("\n✓ Seed complete. Refresh the dashboard.")
    print(f"  demo db_id (for ClickHouse queries): {DEMO_DB_ID}")
    print(f"  use the real connection id from the incidents table for API calls")


if __name__ == "__main__":
    asyncio.run(main())

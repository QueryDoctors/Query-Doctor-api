"""
ClickHouse migration runner.

Usage:
    ENV_FILE=.env.local python -m clickhouse_migrations.runner
    ENV_FILE=.env.dev    python -m clickhouse_migrations.runner
    ENV_FILE=.env.prod   python -m clickhouse_migrations.runner
"""
import os
import sys
from pathlib import Path

import clickhouse_connect

MIGRATIONS_DIR = Path(__file__).parent / "versions"
TRACKING_TABLE = "system.ch_migrations"


def get_client():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "admin"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "admin123"),
    )


def ensure_tracking_table(client) -> None:
    client.command(f"""
        CREATE TABLE IF NOT EXISTS {TRACKING_TABLE} (
            version UInt32,
            name    String,
            applied_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        ORDER BY version
    """)


def get_applied_versions(client) -> set:
    try:
        result = client.query(f"SELECT version FROM {TRACKING_TABLE}")
        return {row[0] for row in result.result_rows}
    except Exception:
        return set()


def run() -> None:
    db_name = os.getenv("CLICKHOUSE_DB", "query-doctor-local")
    print(f"[clickhouse-migrate] target db: {db_name}")

    client = get_client()
    ensure_tracking_table(client)
    applied = get_applied_versions(client)

    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not sql_files:
        print("[clickhouse-migrate] no migration files found")
        return

    for f in sql_files:
        version = int(f.stem.split("_")[0])
        if version in applied:
            print(f"  skip  {f.name}")
            continue

        print(f"  apply {f.name}")
        sql = f.read_text().replace("{{DB}}", db_name)

        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                client.command(stmt)

        client.insert(
            TRACKING_TABLE,
            [[version, f.stem]],
            column_names=["version", "name"],
        )
        print(f"  done  {f.name}")

    print("[clickhouse-migrate] all migrations applied")


if __name__ == "__main__":
    # Load env file if ENV_FILE is set
    env_file = os.environ.get("ENV_FILE", ".env.local")
    if Path(env_file).exists():
        for line in Path(env_file).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                # Strip inline comments (e.g. "8123  # HTTP port")
                val = val.split("#")[0].strip()
                os.environ.setdefault(key.strip(), val)

    run()

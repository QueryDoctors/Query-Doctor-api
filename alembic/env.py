"""
Alembic migration environment.
Uses psycopg2 (sync) for migrations. asyncpg is used at runtime only.
No ORM models — all migrations are written manually.

Usage:
    ENV_FILE=.env.local venv/bin/alembic upgrade head
    ENV_FILE=.env.dev   venv/bin/alembic upgrade head
    ENV_FILE=.env.prod  venv/bin/alembic upgrade head
    ENV_FILE=.env.local venv/bin/alembic revision -m "describe_change"
"""
import os
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from alembic import context

# ─── Load correct env file ────────────────────────────────────────────────────
env_file = os.environ.get("ENV_FILE", ".env.local")
load_dotenv(Path(env_file), override=True)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No ORM — migrations are written manually with op.create_table / op.add_column
target_metadata = None

# ─── Use psycopg2 sync URL for Alembic ───────────────────────────────────────
_raw_url = os.environ["APP_DATABASE_URL"]
# Strip asyncpg dialect if present, ensure standard postgresql:// for psycopg2
_sync_url = _raw_url.replace("postgresql+asyncpg://", "postgresql://", 1)
config.set_main_option("sqlalchemy.url", _sync_url)


def run_migrations_offline() -> None:
    """Generate SQL script without connecting (useful for review before apply)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to DB and apply pending migrations."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

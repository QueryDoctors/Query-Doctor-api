import os
from enum import Enum
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    PROD = "prod"


class Settings(BaseSettings):
    # ─── App identity ──────────────────────────────────────────────────────────
    env: Environment = Environment.LOCAL

    # ─── App database ──────────────────────────────────────────────────────────
    app_database_url: str

    # ─── Encryption ────────────────────────────────────────────────────────────
    encryption_key: str

    # ─── Server ────────────────────────────────────────────────────────────────
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ─── SQLAlchemy tuning ─────────────────────────────────────────────────────
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False           # True in local/dev only — set per env file

    # ─── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:3000"]

    # ─── ClickHouse (HTTP port 8123) ───────────────────────────────────────────
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_db: str = "query-doctor-local"
    clickhouse_user: str = "admin"
    clickhouse_password: str = "admin123"

    # ─── Incident Detection ────────────────────────────────────────────────────
    incident_min_calls_per_minute: int = 20
    incident_min_spike_duration_seconds: int = 30
    incident_trigger_minutes: int = 2
    incident_cooldown_minutes: int = 5
    incident_auto_resolve_minutes: int = 5
    incident_baseline_window_minutes: int = 10
    detection_interval_seconds: int = 10

    model_config = SettingsConfigDict(
        # env_file is set dynamically in get_settings() via ENV_FILE env var
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def async_database_url(self) -> str:
        """Convert standard postgres:// URL to asyncpg dialect for SQLAlchemy."""
        return self.app_database_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )

    @property
    def is_local(self) -> bool:
        return self.env == Environment.LOCAL

    @property
    def is_prod(self) -> bool:
        return self.env == Environment.PROD


@lru_cache
def get_settings() -> Settings:
    env_file = os.environ.get("ENV_FILE", ".env.local")
    return Settings(_env_file=env_file)  # type: ignore[call-arg]

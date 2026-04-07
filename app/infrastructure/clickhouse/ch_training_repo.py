"""ClickHouse repository for writing training events."""
import asyncio
from datetime import datetime, timezone

import clickhouse_connect

from app.infrastructure.config import Settings


class ChTrainingRepo:
    """Appends training event rows to ClickHouse for later AI model training.

    All writes are best-effort — callers should fire-and-forget via
    asyncio.create_task(asyncio.to_thread(repo.write_outcome, ...))
    so HTTP responses are never delayed.
    """

    def __init__(self, settings: Settings) -> None:
        self._client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_db,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
        )
        self._db = settings.clickhouse_db

    def write_outcome(
        self,
        incident_id: str,
        event_type: str,  # acknowledged | resolved | muted | whitelisted
        db_id: str,
        query_hash: str,
        resolution_time_s: int = 0,
    ) -> None:
        """Append an outcome event row for an existing incident."""
        self._client.insert(
            f"`{self._db}`.training_events",
            [[
                incident_id,
                event_type,
                db_id,
                query_hash,
                "",       # query_text — not needed for outcome rows
                0.0,      # mean_latency_ms
                0.0,      # baseline_latency_ms
                0.0,      # latency_ratio
                0.0,      # calls_per_minute
                0,        # spike_duration_s
                0,        # active_connections
                0.0,      # p95_baseline_ms
                0,        # prior_incident_count
                "",       # severity_fired
                resolution_time_s,
                datetime.now(tz=timezone.utc),
            ]],
            column_names=[
                "incident_id", "event_type", "db_id", "query_hash", "query_text",
                "mean_latency_ms", "baseline_latency_ms", "latency_ratio", "calls_per_minute",
                "spike_duration_s", "active_connections", "p95_baseline_ms",
                "prior_incident_count", "severity_fired", "resolution_time_s", "captured_at",
            ],
        )

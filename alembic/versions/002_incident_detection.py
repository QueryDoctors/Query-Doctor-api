"""incident detection tables

Revision ID: 002
Revises: 001
Create Date: 2026-04-06 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Incidents ─────────────────────────────────────────────────────────────
    op.create_table(
        "incidents",
        sa.Column("id",                  sa.String(),                nullable=False, primary_key=True),
        sa.Column("db_id",               sa.String(),                nullable=False),
        sa.Column("query_hash",          sa.String(),                nullable=False),
        sa.Column("query_text",          sa.Text(),                  nullable=False),
        sa.Column("severity",            sa.String(),                nullable=False),
        sa.Column("status",              sa.String(),                nullable=False, server_default="open"),
        sa.Column("start_time",          sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_updated",        sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_latency_ms",  sa.Float(),                 nullable=False),
        sa.Column("baseline_latency_ms", sa.Float(),                 nullable=False),
        sa.Column("latency_ratio",       sa.Float(),                 nullable=False),
        sa.Column("calls_per_minute",    sa.Float(),                 nullable=False),
        sa.Column("resolved_at",         sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_at",     sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "severity IN ('critical','high','medium','low')",
            name="ck_incidents_severity",
        ),
        sa.CheckConstraint(
            "status IN ('open','investigating','resolved')",
            name="ck_incidents_status",
        ),
    )
    op.create_index("ix_incidents_db_status",    "incidents", ["db_id", "status"])
    op.create_index("ix_incidents_db_hash",      "incidents", ["db_id", "query_hash"])
    op.create_index("ix_incidents_start_time",   "incidents", ["start_time"])

    # ── Muted / whitelisted queries ───────────────────────────────────────────
    op.create_table(
        "muted_queries",
        sa.Column("query_hash",    sa.String(),                nullable=False),
        sa.Column("db_id",         sa.String(),                nullable=False),
        sa.Column("muted_at",      sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_whitelisted", sa.Boolean(),              server_default=sa.text("false"), nullable=False),
        sa.PrimaryKeyConstraint("query_hash", "db_id", name="pk_muted_queries"),
    )

    # ── Anomaly tracking (per-query abnormal window) ──────────────────────────
    op.create_table(
        "anomaly_tracking",
        sa.Column("query_hash",   sa.String(),                nullable=False),
        sa.Column("db_id",        sa.String(),                nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at",  sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("query_hash", "db_id", name="pk_anomaly_tracking"),
    )


def downgrade() -> None:
    op.drop_table("anomaly_tracking")
    op.drop_table("muted_queries")
    op.drop_index("ix_incidents_start_time", "incidents")
    op.drop_index("ix_incidents_db_hash",    "incidents")
    op.drop_index("ix_incidents_db_status",  "incidents")
    op.drop_table("incidents")

"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Saved DB connections ──────────────────────────────────────────────────
    op.create_table(
        "connections",
        sa.Column("id",         sa.String(),                nullable=False, primary_key=True),
        sa.Column("name",       sa.String(),                nullable=False),
        sa.Column("host",       sa.String(),                nullable=False),
        sa.Column("port",       sa.Integer(),               nullable=False, server_default="5432"),
        sa.Column("database",   sa.String(),                nullable=False),
        sa.Column("db_user",    sa.String(),                nullable=False),
        sa.Column("password",   sa.String(),                nullable=False),  # Fernet-encrypted
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_used",  sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name", name="uq_connections_name"),
    )

    # ── Analysis snapshots ────────────────────────────────────────────────────
    op.create_table(
        "snapshots",
        sa.Column("id",                 sa.String(),                nullable=False, primary_key=True),
        sa.Column("connection_id",      sa.String(),                nullable=False),
        sa.Column("captured_at",        sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("active_connections", sa.Integer(),               nullable=True),
        sa.Column("qps",                sa.Numeric(10, 2),          nullable=True),
        sa.Column("avg_query_time_ms",  sa.Numeric(10, 2),          nullable=True),
        sa.Column("total_queries",      sa.BigInteger(),            nullable=True),
        sa.ForeignKeyConstraint(["connection_id"], ["connections.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_snapshots_connection_id", "snapshots", ["connection_id"])
    op.create_index("ix_snapshots_captured_at",   "snapshots", ["captured_at"])

    # ── Query stats per snapshot ──────────────────────────────────────────────
    op.create_table(
        "snapshot_queries",
        sa.Column("id",            sa.String(),       nullable=False, primary_key=True),
        sa.Column("snapshot_id",   sa.String(),       nullable=False),
        sa.Column("category",      sa.String(),       nullable=False),  # slow|frequent|heaviest
        sa.Column("query",         sa.Text(),         nullable=False),
        sa.Column("mean_time_ms",  sa.Numeric(10, 2), nullable=True),
        sa.Column("calls",         sa.BigInteger(),   nullable=True),
        sa.Column("total_time_ms", sa.Numeric(10, 2), nullable=True),
        sa.Column("rows",          sa.BigInteger(),   nullable=True),
        sa.ForeignKeyConstraint(["snapshot_id"], ["snapshots.id"], ondelete="CASCADE"),
        sa.CheckConstraint("category IN ('slow','frequent','heaviest')", name="ck_sq_category"),
    )
    op.create_index("ix_snapshot_queries_snapshot_id", "snapshot_queries", ["snapshot_id"])

    # ── Recommendations per snapshot ──────────────────────────────────────────
    op.create_table(
        "snapshot_recommendations",
        sa.Column("id",          sa.String(), nullable=False, primary_key=True),
        sa.Column("snapshot_id", sa.String(), nullable=False),
        sa.Column("problem",     sa.Text(),   nullable=False),
        sa.Column("impact",      sa.Text(),   nullable=False),
        sa.Column("suggestion",  sa.Text(),   nullable=False),
        sa.Column("severity",    sa.String(), nullable=False),  # high|medium|low
        sa.ForeignKeyConstraint(["snapshot_id"], ["snapshots.id"], ondelete="CASCADE"),
        sa.CheckConstraint("severity IN ('high','medium','low')", name="ck_sr_severity"),
    )
    op.create_index("ix_snapshot_recs_snapshot_id", "snapshot_recommendations", ["snapshot_id"])


def downgrade() -> None:
    op.drop_table("snapshot_recommendations")
    op.drop_table("snapshot_queries")
    op.drop_table("snapshots")
    op.drop_table("connections")

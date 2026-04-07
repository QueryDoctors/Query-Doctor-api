"""scope saved connections to user

Revision ID: 004
Revises: 003
Create Date: 2026-04-07 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id — nullable first so existing rows don't fail
    op.add_column("connections", sa.Column("user_id", sa.String(), nullable=True))

    # Drop old global unique constraint on name (was per-app, now must be per-user)
    op.drop_constraint("uq_connections_name", "connections", type_="unique")

    # New unique constraint: name is unique per user
    op.create_unique_constraint("uq_connections_name_user", "connections", ["name", "user_id"])

    # Index for fast per-user lookups
    op.create_index("ix_connections_user_id", "connections", ["user_id"])

    # FK to users (set null on user delete — keeps historical connection rows)
    op.create_foreign_key(
        "fk_connections_user_id",
        "connections", "users",
        ["user_id"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_connections_user_id", "connections", type_="foreignkey")
    op.drop_index("ix_connections_user_id", table_name="connections")
    op.drop_constraint("uq_connections_name_user", "connections", type_="unique")
    op.create_unique_constraint("uq_connections_name", "connections", ["name"])
    op.drop_column("connections", "user_id")

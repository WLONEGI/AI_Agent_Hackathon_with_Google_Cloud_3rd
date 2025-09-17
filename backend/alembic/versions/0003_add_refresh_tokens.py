"""add user refresh tokens

Revision ID: 0003_add_refresh_tokens
Revises: 0002_add_users_projects_assets
Create Date: 2025-09-17 12:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0003_add_refresh_tokens"
down_revision = "0002_add_users_projects_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_refresh_tokens_user", ondelete="CASCADE"),
    )

    op.create_index("ix_user_refresh_tokens_user_id", "user_refresh_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_refresh_tokens_user_id", table_name="user_refresh_tokens")
    op.drop_table("user_refresh_tokens")

"""Add user_account and user_refresh_token tables

Revision ID: 0006_add_user_tables
Revises: 0005_rename_manga_asset_metadata
Create Date: 2025-09-19 14:15:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0006_add_user_tables"
down_revision = "0005_rename_manga_asset_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("firebase_uid", sa.String(length=128), nullable=False, unique=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("account_type", sa.String(length=32), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("firebase_claims", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create user_refresh_tokens table
    op.create_table(
        "user_refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Add foreign key constraint to manga_sessions.user_id
    op.create_foreign_key(
        "fk_manga_sessions_user_id",
        "manga_sessions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL"
    )

    # Create indexes
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_user_refresh_tokens_user_id", "user_refresh_tokens", ["user_id"])
    op.create_index("ix_user_refresh_tokens_token_hash", "user_refresh_tokens", ["token_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_refresh_tokens_token_hash", table_name="user_refresh_tokens")
    op.drop_index("ix_user_refresh_tokens_user_id", table_name="user_refresh_tokens")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_firebase_uid", table_name="users")
    op.drop_constraint("fk_manga_sessions_user_id", "manga_sessions", type_="foreignkey")
    op.drop_table("user_refresh_tokens")
    op.drop_table("users")
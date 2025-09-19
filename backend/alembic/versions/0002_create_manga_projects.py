"""create manga_projects table

Revision ID: 0002_create_manga_projects
Revises: 0001_initial
Create Date: 2025-09-17 06:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0002_create_manga_projects"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "manga_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),  # This will be renamed in 0004
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("total_pages", sa.Integer(), nullable=True),
        sa.Column("style", sa.String(length=64), nullable=True),
        sa.Column("visibility", sa.String(length=32), nullable=False, server_default="private"),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Add manga_assets table that references manga_projects
    op.create_table(
        "manga_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("manga_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("manga_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("phase", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),  # This will be renamed in 0005
        sa.Column("quality_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index("ix_manga_projects_user_id", "manga_projects", ["user_id"], unique=False)
    op.create_index("ix_manga_projects_status", "manga_projects", ["status"], unique=False)
    op.create_index("ix_manga_assets_project_id", "manga_assets", ["project_id"], unique=False)
    op.create_index("ix_manga_assets_session_id", "manga_assets", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_manga_assets_session_id", table_name="manga_assets")
    op.drop_index("ix_manga_assets_project_id", table_name="manga_assets")
    op.drop_index("ix_manga_projects_status", table_name="manga_projects")
    op.drop_index("ix_manga_projects_user_id", table_name="manga_projects")
    op.drop_table("manga_assets")
    op.drop_table("manga_projects")
"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2025-09-17 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "manga_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("current_phase", sa.Integer(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("session_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "preview_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase", sa.Integer(), nullable=False),
        sa.Column("parent_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("preview_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version_data", sa.JSON(), nullable=True),
        sa.Column("change_description", sa.String(length=255), nullable=True),
        sa.Column("quality_level", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "phase_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("content", sa.JSON(), nullable=True),
        sa.Column("quality_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("preview_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("preview_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "preview_cache_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("cache_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("preview_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase", sa.Integer(), nullable=False),
        sa.Column("quality_level", sa.Integer(), nullable=False),
        sa.Column("signed_url", sa.String(length=2048), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False, server_default="application/json"),
        sa.Column("file_size", sa.Numeric(12, 0), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("last_accessed", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "user_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase", sa.Integer(), nullable=False),
        sa.Column("feedback_type", sa.String(length=32), nullable=False, server_default="natural_language"),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("sentiment_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "generated_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("signed_url", sa.String(length=2048), nullable=True),
        sa.Column("image_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_phase_results_session_phase", "phase_results", ["session_id", "phase"], unique=False)
    op.create_index("ix_preview_versions_session_phase", "preview_versions", ["session_id", "phase"], unique=False)
    op.create_index("ix_user_feedback_session_phase", "user_feedback", ["session_id", "phase"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_feedback_session_phase", table_name="user_feedback")
    op.drop_index("ix_preview_versions_session_phase", table_name="preview_versions")
    op.drop_index("ix_phase_results_session_phase", table_name="phase_results")
    op.drop_table("generated_images")
    op.drop_table("user_feedback")
    op.drop_table("preview_cache_metadata")
    op.drop_table("phase_results")
    op.drop_table("preview_versions")
    op.drop_table("manga_sessions")

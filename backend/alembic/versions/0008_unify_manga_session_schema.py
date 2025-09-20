"""Unify manga_session schema with application model

Revision ID: 0008_unify_manga_session_schema
Revises: 0007_add_hitl_tables
Create Date: 2025-09-20 14:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0008_unify_manga_session_schema"
down_revision = "0007_add_hitl_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to manga_sessions table to match application model"""

    # Add missing columns that exist in app model but not in DB
    op.add_column("manga_sessions", sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True, unique=True))
    op.add_column("manga_sessions", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("manga_sessions", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("manga_sessions", sa.Column("session_metadata", sa.JSON(), nullable=True))

    # Add missing columns that exist in DB schema but not in app model
    op.add_column("manga_sessions", sa.Column("text", sa.Text(), nullable=True))
    op.add_column("manga_sessions", sa.Column("ai_auto_settings", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("manga_sessions", sa.Column("feedback_mode", sa.JSON(), nullable=True))
    op.add_column("manga_sessions", sa.Column("options", sa.JSON(), nullable=True))
    op.add_column("manga_sessions", sa.Column("estimated_completion_time", sa.DateTime(timezone=True), nullable=True))
    op.add_column("manga_sessions", sa.Column("actual_completion_time", sa.DateTime(timezone=True), nullable=True))
    op.add_column("manga_sessions", sa.Column("total_phases", sa.Integer(), nullable=True, server_default="5"))
    op.add_column("manga_sessions", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("manga_sessions", sa.Column("websocket_channel", sa.String(length=255), nullable=True))

    # Add foreign key constraints
    op.create_foreign_key(
        "fk_manga_sessions_project_id",
        "manga_sessions",
        "manga_projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL"
    )

    # Create indexes for performance
    op.create_index("ix_manga_sessions_request_id", "manga_sessions", ["request_id"], unique=True)
    op.create_index("ix_manga_sessions_project_id", "manga_sessions", ["project_id"], unique=False)

    # Generate request_id for existing records
    op.execute("""
        UPDATE manga_sessions
        SET request_id = gen_random_uuid()
        WHERE request_id IS NULL
    """)

    # Make request_id NOT NULL after populating existing records
    op.alter_column("manga_sessions", "request_id", nullable=False)


def downgrade() -> None:
    """Remove added columns to revert to original schema"""

    # Drop indexes
    op.drop_index("ix_manga_sessions_project_id", table_name="manga_sessions")
    op.drop_index("ix_manga_sessions_request_id", table_name="manga_sessions")

    # Drop foreign key constraint
    op.drop_constraint("fk_manga_sessions_project_id", "manga_sessions", type_="foreignkey")

    # Drop added columns
    op.drop_column("manga_sessions", "websocket_channel")
    op.drop_column("manga_sessions", "error_message")
    op.drop_column("manga_sessions", "total_phases")
    op.drop_column("manga_sessions", "actual_completion_time")
    op.drop_column("manga_sessions", "estimated_completion_time")
    op.drop_column("manga_sessions", "options")
    op.drop_column("manga_sessions", "feedback_mode")
    op.drop_column("manga_sessions", "ai_auto_settings")
    op.drop_column("manga_sessions", "text")
    op.drop_column("manga_sessions", "session_metadata")
    op.drop_column("manga_sessions", "retry_count")
    op.drop_column("manga_sessions", "project_id")
    op.drop_column("manga_sessions", "request_id")
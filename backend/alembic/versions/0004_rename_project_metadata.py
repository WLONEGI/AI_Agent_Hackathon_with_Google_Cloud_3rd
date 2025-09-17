"""rename metadata column to project_metadata

Revision ID: 0004_rename_project_metadata
Revises: 0003_add_refresh_tokens
Create Date: 2025-09-17 12:45:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0004_rename_project_metadata"
down_revision = "0003_add_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("manga_projects") as batch_op:
        batch_op.alter_column("metadata", new_column_name="project_metadata")


def downgrade() -> None:
    with op.batch_alter_table("manga_projects") as batch_op:
        batch_op.alter_column("project_metadata", new_column_name="metadata")

"""rename manga_assets.metadata to asset_metadata

Revision ID: 0005_rename_manga_asset_metadata
Revises: 0004_rename_project_metadata
Create Date: 2025-09-17 13:00:00
"""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "0005_rename_manga_asset_metadata"
down_revision = "0004_rename_project_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("manga_assets") as batch_op:
        batch_op.alter_column("metadata", new_column_name="asset_metadata")


def downgrade() -> None:
    with op.batch_alter_table("manga_assets") as batch_op:
        batch_op.alter_column("asset_metadata", new_column_name="metadata")

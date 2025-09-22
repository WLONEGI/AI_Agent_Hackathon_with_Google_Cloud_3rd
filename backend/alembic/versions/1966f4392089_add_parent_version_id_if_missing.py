"""add_parent_version_id_if_missing

Revision ID: 1966f4392089
Revises: 0010_fix_schema_inconsistencies
Create Date: 2025-09-22 05:34:10.069631
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1966f4392089"
down_revision = "0010_fix_schema_inconsistencies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add parent_version_id column to preview_versions table if it doesn't exist"""

    connection = op.get_bind()

    # Check if parent_version_id column exists
    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'preview_versions'
        AND column_name = 'parent_version_id'
    """))

    if result.scalar() == 0:
        print("Adding missing parent_version_id column to preview_versions table...")
        op.add_column("preview_versions", sa.Column(
            "parent_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("preview_versions.id", ondelete="SET NULL"),
            nullable=True
        ))
        print("Successfully added parent_version_id column")
    else:
        print("parent_version_id column already exists, skipping...")


def downgrade() -> None:
    """Remove parent_version_id column if it exists"""

    connection = op.get_bind()

    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'preview_versions'
        AND column_name = 'parent_version_id'
    """))

    if result.scalar() > 0:
        op.drop_column("preview_versions", "parent_version_id")

"""create_manga_assets_table

Revision ID: 0a00af6fd715
Revises: 1966f4392089
Create Date: 2025-09-22 10:41:27.703375
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0a00af6fd715"
down_revision = "1966f4392089"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create manga_assets table based on MangaAsset model"""

    connection = op.get_bind()

    # Check if manga_assets table already exists
    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = 'manga_assets'
        AND table_schema = 'public'
    """))

    if result.scalar() == 0:
        print("Creating manga_assets table...")

        op.create_table(
            "manga_assets",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                     server_default=sa.text("gen_random_uuid()")),
            sa.Column("project_id", postgresql.UUID(as_uuid=True),
                     sa.ForeignKey("manga_projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("asset_type", sa.String(length=32), nullable=False),
            sa.Column("storage_path", sa.String(length=512), nullable=False),
            sa.Column("signed_url", sa.String(length=2048), nullable=True),
            sa.Column("asset_metadata", sa.JSON(), nullable=True),
            sa.Column("size_bytes", sa.Numeric(16, 0), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

        # Create indexes for better performance
        op.create_index("ix_manga_assets_project_id", "manga_assets", ["project_id"])
        op.create_index("ix_manga_assets_asset_type", "manga_assets", ["asset_type"])
        op.create_index("ix_manga_assets_created_at", "manga_assets", ["created_at"])

        # Grant privileges to manga_user
        connection.execute(sa.text("GRANT ALL PRIVILEGES ON TABLE manga_assets TO manga_user"))

        print("Successfully created manga_assets table with indexes and granted privileges")
    else:
        print("manga_assets table already exists, granting privileges...")
        # Grant privileges to manga_user even if table exists
        try:
            connection.execute(sa.text("GRANT ALL PRIVILEGES ON TABLE manga_assets TO manga_user"))
            print("Successfully granted privileges to manga_user")
        except Exception as e:
            print(f"Warning: Could not grant privileges - {e}")


def downgrade() -> None:
    """Drop manga_assets table if it exists"""

    connection = op.get_bind()

    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = 'manga_assets'
        AND table_schema = 'public'
    """))

    if result.scalar() > 0:
        print("Dropping manga_assets table...")
        op.drop_table("manga_assets")
        print("Successfully dropped manga_assets table")
    else:
        print("manga_assets table does not exist, nothing to drop")

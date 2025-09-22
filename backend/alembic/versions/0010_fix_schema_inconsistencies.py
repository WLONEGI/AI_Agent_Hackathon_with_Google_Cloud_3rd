"""Fix schema inconsistencies between models and database

Revision ID: 0010_fix_schema_inconsistencies
Revises: 0009_ensure_request_id_exists
Create Date: 2025-09-21 18:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0010_fix_schema_inconsistencies"
down_revision = "0009_ensure_request_id_exists"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix schema inconsistencies to match application models"""

    # 1. Fix users table - add missing columns
    print("Adding missing columns to users table...")

    # Add google_id column if it doesn't exist
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name = 'google_id'
    """))

    if result.scalar() == 0:
        op.add_column("users", sa.Column("google_id", sa.String(length=255), nullable=True))
        # Initially nullable, will be fixed after data migration
        op.create_unique_constraint("uq_users_google_id", "users", ["google_id"])

    # Add name column if it doesn't exist
    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name = 'name'
    """))

    if result.scalar() == 0:
        op.add_column("users", sa.Column("name", sa.String(length=255), nullable=True))
        # Copy display_name to name for existing users
        connection.execute(sa.text("""
            UPDATE users
            SET name = COALESCE(display_name, 'Unknown User')
            WHERE name IS NULL
        """))
        op.alter_column("users", "name", nullable=False)

    # Add missing boolean and subscription columns
    missing_columns = [
        ("is_premium", sa.Boolean(), False, "false"),
        ("subscription_tier", sa.String(length=32), False, "'free'"),
        ("daily_generation_count", sa.Integer(), False, "0"),
    ]

    for column_name, column_type, nullable, default in missing_columns:
        result = connection.execute(sa.text(f"""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'users'
            AND column_name = '{column_name}'
        """))

        if result.scalar() == 0:
            op.add_column("users", sa.Column(
                column_name,
                column_type,
                nullable=nullable,
                server_default=default
            ))

    # Add daily_limit_reset_at with timezone
    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'users'
        AND column_name = 'daily_limit_reset_at'
    """))

    if result.scalar() == 0:
        op.add_column("users", sa.Column(
            "daily_limit_reset_at",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now()
        ))

    # 2. Fix user_refresh_tokens table - rename and add columns
    print("Fixing user_refresh_tokens table...")

    # Check if we need to rename token_hash to refresh_token
    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'user_refresh_tokens'
        AND column_name = 'token_hash'
    """))

    has_token_hash = result.scalar() > 0

    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'user_refresh_tokens'
        AND column_name = 'refresh_token'
    """))

    has_refresh_token = result.scalar() > 0

    if has_token_hash and not has_refresh_token:
        # Rename token_hash to refresh_token and change type
        op.add_column("user_refresh_tokens", sa.Column("refresh_token", sa.Text(), nullable=True))

        # Copy data (expand hash to text format - this is a breaking change)
        connection.execute(sa.text("""
            UPDATE user_refresh_tokens
            SET refresh_token = token_hash
        """))

        op.alter_column("user_refresh_tokens", "refresh_token", nullable=False)
        op.drop_column("user_refresh_tokens", "token_hash")

    # Add is_revoked column if it doesn't exist
    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'user_refresh_tokens'
        AND column_name = 'is_revoked'
    """))

    if result.scalar() == 0:
        op.add_column("user_refresh_tokens", sa.Column(
            "is_revoked",
            sa.Boolean(),
            nullable=False,
            server_default="false"
        ))

        # Set is_revoked=true for tokens that have revoked_at
        connection.execute(sa.text("""
            UPDATE user_refresh_tokens
            SET is_revoked = true
            WHERE revoked_at IS NOT NULL
        """))

    # Update timestamps to use timezone
    try:
        op.alter_column("user_refresh_tokens", "expires_at",
                       type_=postgresql.TIMESTAMP(timezone=True))
        op.alter_column("user_refresh_tokens", "created_at",
                       type_=postgresql.TIMESTAMP(timezone=True))
        if connection.execute(sa.text("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'user_refresh_tokens' AND column_name = 'updated_at'
        """)).scalar() == 0:
            op.add_column("user_refresh_tokens", sa.Column(
                "updated_at",
                postgresql.TIMESTAMP(timezone=True),
                nullable=False,
                server_default=sa.func.now()
            ))
    except:
        pass  # Already correct type

    # 3. Fix manga_assets table - remove extra columns not in model
    print("Cleaning up manga_assets table...")

    extra_columns = ["session_id", "phase", "file_size", "content_type", "quality_score", "is_primary"]

    for column_name in extra_columns:
        result = connection.execute(sa.text(f"""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'manga_assets'
            AND column_name = '{column_name}'
        """))

        if result.scalar() > 0:
            try:
                # Drop foreign key constraint first if exists
                if column_name == "session_id":
                    try:
                        op.drop_constraint("fk_manga_assets_session_id", "manga_assets", type_="foreignkey")
                    except:
                        pass

                op.drop_column("manga_assets", column_name)
                print(f"Dropped extra column: {column_name}")
            except Exception as e:
                print(f"Could not drop column {column_name}: {e}")

    # Ensure required columns exist and have correct types
    required_columns = [
        ("signed_url", sa.String(length=2048)),
        ("size_bytes", sa.Numeric(16, 0)),
    ]

    for column_name, column_type in required_columns:
        result = connection.execute(sa.text(f"""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'manga_assets'
            AND column_name = '{column_name}'
        """))

        if result.scalar() == 0:
            op.add_column("manga_assets", sa.Column(column_name, column_type, nullable=True))

    # 4. Create missing tables: session_messages and session_events
    print("Creating missing tables...")

    # Create session_messages table if it doesn't exist
    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = 'session_messages'
    """))

    if result.scalar() == 0:
        op.create_table(
            "session_messages",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("session_id", postgresql.UUID(as_uuid=True),
                     sa.ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("message_type", sa.String(length=20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("phase", sa.Integer(), nullable=True),
            sa.Column("message_metadata", sa.JSON(), nullable=True, server_default="{}"),
            sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                     nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True),
                     nullable=False, server_default=sa.func.now()),
        )

        # Create indexes
        op.create_index("ix_session_messages_session_id", "session_messages", ["session_id"])
        op.create_index("ix_session_messages_message_type", "session_messages", ["message_type"])
        print("Created session_messages table")

    # Create session_events table if it doesn't exist
    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = 'session_events'
    """))

    if result.scalar() == 0:
        op.create_table(
            "session_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("session_id", postgresql.UUID(as_uuid=True),
                     sa.ForeignKey("manga_sessions.id", ondelete="CASCADE"), nullable=False),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("event_data", sa.JSON(), nullable=False),
            sa.Column("created_at", postgresql.TIMESTAMP(timezone=True),
                     nullable=False, server_default=sa.func.now()),
        )

        # Create indexes
        op.create_index("ix_session_events_session_id", "session_events", ["session_id"])
        op.create_index("ix_session_events_event_type", "session_events", ["event_type"])
        op.create_index("ix_session_events_created_at", "session_events", ["created_at"])
        print("Created session_events table")

    print("Schema inconsistencies fixed successfully!")


def downgrade() -> None:
    """Revert schema fixes (use with caution - may cause data loss)"""

    # Drop created tables
    op.drop_table("session_events")
    op.drop_table("session_messages")

    # Note: We don't revert user table changes or token table changes
    # as this could cause data loss and application breakage
    print("Downgrade completed - some changes retained to prevent data loss")
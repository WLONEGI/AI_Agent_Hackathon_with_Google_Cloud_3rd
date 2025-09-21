"""Ensure request_id column exists with proper handling

Revision ID: 0009_ensure_request_id_exists
Revises: 0008_unify_manga_session_schema
Create Date: 2025-09-21 10:40:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0009_ensure_request_id_exists"
down_revision = "0008_unify_manga_session_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ensure request_id column exists and is properly configured"""

    # Check if request_id column exists and add it if missing
    # This is a safe operation that uses IF NOT EXISTS
    connection = op.get_bind()

    # Check if request_id column exists
    result = connection.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'manga_sessions'
        AND column_name = 'request_id'
    """))

    request_id_exists = result.scalar() > 0

    if not request_id_exists:
        print("Adding request_id column...")
        # Add the request_id column
        op.add_column("manga_sessions", sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=True))

        # Generate request_id for existing records
        connection.execute(sa.text("""
            UPDATE manga_sessions
            SET request_id = gen_random_uuid()
            WHERE request_id IS NULL
        """))

        # Make request_id NOT NULL and UNIQUE
        op.alter_column("manga_sessions", "request_id", nullable=False)
        op.create_unique_constraint("uq_manga_sessions_request_id", "manga_sessions", ["request_id"])

        print("request_id column added successfully!")
    else:
        print("request_id column already exists")

    # Ensure other critical columns exist
    critical_columns = [
        ("session_metadata", sa.JSON(), True),
        ("current_phase", sa.Integer(), True),
        ("total_phases", sa.Integer(), True),
        ("retry_count", sa.Integer(), False, "0"),
    ]

    for column_info in critical_columns:
        column_name = column_info[0]
        column_type = column_info[1]
        nullable = column_info[2]
        default = column_info[3] if len(column_info) > 3 else None

        # Check if column exists
        result = connection.execute(sa.text(f"""
            SELECT COUNT(*)
            FROM information_schema.columns
            WHERE table_name = 'manga_sessions'
            AND column_name = '{column_name}'
        """))

        column_exists = result.scalar() > 0

        if not column_exists:
            print(f"Adding {column_name} column...")
            column_args = [column_name, column_type]
            column_kwargs = {"nullable": nullable}
            if default:
                column_kwargs["server_default"] = default

            op.add_column("manga_sessions", sa.Column(*column_args, **column_kwargs))
            print(f"{column_name} column added successfully!")
        else:
            print(f"{column_name} column already exists")


def downgrade() -> None:
    """Remove the added columns if needed"""

    # Remove unique constraint
    try:
        op.drop_constraint("uq_manga_sessions_request_id", "manga_sessions", type_="unique")
    except:
        pass

    # Only drop columns that we know we added in this migration
    # Be conservative to avoid data loss
    pass
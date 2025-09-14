"""Add JSONB columns for unified PostgreSQL storage

Revision ID: 002_postgresql_unification
Revises: 001_firebase_user_fields
Create Date: 2025-09-14 19:12:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_postgresql_unification'
down_revision = '001_firebase_user_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add unified PostgreSQL storage columns to replace Firestore."""

    # Add JSONB columns for storing Firebase data in PostgreSQL
    op.add_column('users', sa.Column('user_profile', postgresql.JSONB, nullable=True,
                                    comment='Store user profile data previously in Firestore'))
    op.add_column('users', sa.Column('user_preferences', postgresql.JSONB, nullable=True,
                                    comment='Store user preferences and settings'))
    op.add_column('users', sa.Column('user_metadata', postgresql.JSONB, nullable=True,
                                    comment='Store additional user metadata'))
    op.add_column('users', sa.Column('generation_history', postgresql.JSONB, nullable=True,
                                    comment='Store manga generation history'))
    op.add_column('users', sa.Column('subscription_data', postgresql.JSONB, nullable=True,
                                    comment='Store subscription and billing data'))

    # Add indexes for JSONB columns for performance
    op.create_index('idx_users_user_profile_gin', 'users', ['user_profile'],
                   postgresql_using='gin', postgresql_concurrently=True)
    op.create_index('idx_users_user_preferences_gin', 'users', ['user_preferences'],
                   postgresql_using='gin', postgresql_concurrently=True)
    op.create_index('idx_users_user_metadata_gin', 'users', ['user_metadata'],
                   postgresql_using='gin', postgresql_concurrently=True)


def downgrade() -> None:
    """Remove unified PostgreSQL storage columns."""

    # Drop indexes first
    op.drop_index('idx_users_user_metadata_gin', 'users')
    op.drop_index('idx_users_user_preferences_gin', 'users')
    op.drop_index('idx_users_user_profile_gin', 'users')

    # Drop columns
    op.drop_column('users', 'subscription_data')
    op.drop_column('users', 'generation_history')
    op.drop_column('users', 'user_metadata')
    op.drop_column('users', 'user_preferences')
    op.drop_column('users', 'user_profile')
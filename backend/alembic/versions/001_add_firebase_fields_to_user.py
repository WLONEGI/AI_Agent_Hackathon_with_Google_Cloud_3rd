"""Add Firebase fields to User model

Revision ID: 001_firebase_user_fields
Revises: 
Create Date: 2025-08-31 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_firebase_user_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add Firebase integration fields to users table."""
    # Add new columns for Firebase integration
    op.add_column('users', sa.Column('firebase_claims', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('account_type', sa.String(length=50), nullable=False, server_default='free'))
    op.add_column('users', sa.Column('provider', sa.String(length=50), nullable=False, server_default='google'))
    
    # Make hashed_password nullable for OAuth users
    op.alter_column('users', 'hashed_password', nullable=True)


def downgrade() -> None:
    """Remove Firebase integration fields from users table."""
    # Remove added columns
    op.drop_column('users', 'provider')
    op.drop_column('users', 'account_type')
    op.drop_column('users', 'firebase_claims')
    
    # Make hashed_password non-nullable again
    op.alter_column('users', 'hashed_password', nullable=False)
"""SQLAlchemy model for Users."""

from sqlalchemy import (
    Column, String, DateTime, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class UsersModel(Base):
    """SQLAlchemy model for users."""
    
    __tablename__ = "users"
    
    # Primary key
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User identification
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    
    # Account information
    account_type = Column(String(20), nullable=False, default="free")
    
    # Firebase integration
    firebase_claims = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            account_type.in_(['free', 'premium', 'admin']),
            name='check_account_type_valid'
        ),
        Index('idx_users_email', 'email'),
        Index('idx_users_account_type', 'account_type'),
        Index('idx_users_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<User(user_id='{self.user_id}', email='{self.email}', account_type='{self.account_type}')>"
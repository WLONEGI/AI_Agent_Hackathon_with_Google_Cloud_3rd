"""User model and authentication schemas."""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    # Primary key - Firebase UID (string format) not UUID
    id = Column(String(128), primary_key=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    
    # Profile fields
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    
    # Status fields
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    
    # Role and permissions
    role = Column(String(50), default="user")  # user, premium, admin
    
    # Firebase integration fields
    firebase_claims = Column(JSON, nullable=True)
    account_type = Column(String(50), default="free")  # free, premium, admin
    provider = Column(String(50), default="google")  # google, email
    
    # Usage limits
    daily_generation_limit = Column(Integer, default=5)
    daily_generations_used = Column(Integer, default=0)
    last_generation_reset = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # manga_sessions = relationship("MangaSession", back_populates="user", cascade="all, delete-orphan")
    # refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"
    
    @property
    def can_generate(self) -> bool:
        """Check if user can generate manga based on limits."""
        if self.account_type == "admin" or self.role == "admin":
            return True
        if self.account_type == "premium" or self.is_premium:
            return self.daily_generations_used < 50  # Premium limit
        return self.daily_generations_used < self.daily_generation_limit
    
    def reset_daily_limit_if_needed(self) -> None:
        """Reset daily generation limit if needed."""
        now = datetime.utcnow()
        if self.last_generation_reset is None or \
           (now - self.last_generation_reset).days >= 1:
            self.daily_generations_used = 0
            self.last_generation_reset = now


# Temporarily disabled RefreshToken to fix relationship issues
# TODO: Re-enable after authentication works
# class RefreshToken(Base):
#     """Refresh token model for JWT authentication."""
#     
#     __tablename__ = "refresh_tokens"
#     
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
#     user_id = Column(String(128), ForeignKey('users.id'), nullable=False, index=True)
#     token = Column(String(500), unique=True, nullable=False)
#     expires_at = Column(DateTime(timezone=True), nullable=False)
#     created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
#     revoked_at = Column(DateTime(timezone=True), nullable=True)
#     
#     # Relationship
#     # user = relationship("User", back_populates="refresh_tokens")
#     
#     @property
#     def is_valid(self) -> bool:
#         """Check if token is valid."""
#         now = datetime.utcnow()
#         return self.revoked_at is None and self.expires_at > now
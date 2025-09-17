from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(min_length=10)


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10)


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class UserProfile(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    account_type: str
    provider: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]


class AuthTokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"
    user: UserProfile


class AccessTokenResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str = "bearer"


class LogoutResponse(BaseModel):
    message: str = "Successfully logged out"

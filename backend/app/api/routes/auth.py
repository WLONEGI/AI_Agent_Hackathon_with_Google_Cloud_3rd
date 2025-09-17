from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import (
    AccessTokenResponse,
    AuthTokensResponse,
    GoogleLoginRequest,
    LogoutRequest,
    LogoutResponse,
    TokenRefreshRequest,
    UserProfile,
)
from app.db.models import UserAccount
from app.dependencies import get_db_session
from app.dependencies.auth import get_current_user
from app.services.auth_service import AuthService


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/google/login", response_model=AuthTokensResponse, status_code=status.HTTP_200_OK)
async def google_login(payload: GoogleLoginRequest, db: AsyncSession = Depends(get_db_session)) -> AuthTokensResponse:
    service = AuthService(db)
    result = await service.login_with_google(payload.id_token)
    user_data = result.pop("user")
    return AuthTokensResponse(user=UserProfile(**user_data), **result)


@router.post("/refresh", response_model=AccessTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    payload: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AccessTokenResponse:
    service = AuthService(db)
    result = await service.refresh_access_token(payload.refresh_token)
    return AccessTokenResponse(**result)


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db_session),
) -> LogoutResponse:
    service = AuthService(db)
    await service.logout(payload.refresh_token)
    return LogoutResponse()


@router.get("/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
async def read_profile(current_user: UserAccount = Depends(get_current_user)) -> UserProfile:
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        account_type=current_user.account_type,
        provider=(current_user.firebase_claims or {}).get("firebase", {}).get("sign_in_provider", "google"),
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=None,
    )

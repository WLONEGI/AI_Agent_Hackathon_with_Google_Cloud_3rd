from __future__ import annotations

from fastapi import Depends, HTTPException, status, WebSocket, WebSocketException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserAccount
from app.dependencies import get_db_session
from app.services.auth_service import AuthService


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> UserAccount:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authorization_required")

    auth_service = AuthService(db)
    return await auth_service.authenticate_access_token(credentials.credentials)


async def get_current_user_websocket(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db_session),
) -> UserAccount:
    """WebSocket authentication dependency."""
    # Get token from query parameters
    token = websocket.query_params.get("token")

    if not token:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")

    try:
        auth_service = AuthService(db)
        return await auth_service.authenticate_access_token(token)
    except HTTPException:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication token")

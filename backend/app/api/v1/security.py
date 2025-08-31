"""Security middleware and authentication for API v1."""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import jwt
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Authentication specific error."""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Authorization specific error."""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extract and validate current user from JWT token."""
    
    if not credentials:
        raise AuthenticationError("Missing authentication token")
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
            
        # Check token expiration
        exp = payload.get("exp")
        if exp and datetime.utcnow().timestamp() > exp:
            raise AuthenticationError("Token expired")
            
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
    
    # Fetch user from database
    user = await db.get(User, user_id)
    if user is None:
        raise AuthenticationError("User not found")
    
    if not user.is_active:
        raise AuthenticationError("User account disabled")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user with additional checks."""
    
    if not current_user.is_active:
        raise AuthenticationError("Inactive user")
    
    return current_user


def require_permissions(*required_permissions: str):
    """Decorator to require specific permissions."""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise AuthorizationError("User context required")
            
            # Check user permissions
            user_permissions = set(current_user.permissions or [])
            if not all(perm in user_permissions for perm in required_permissions):
                missing = set(required_permissions) - user_permissions
                raise AuthorizationError(f"Missing permissions: {', '.join(missing)}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


class RateLimiter:
    """Rate limiting for API endpoints."""
    
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.call_times: dict = {}
    
    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limit."""
        now = datetime.utcnow().timestamp()
        
        if identifier not in self.call_times:
            self.call_times[identifier] = []
        
        # Clean old entries
        cutoff = now - self.period
        self.call_times[identifier] = [
            call_time for call_time in self.call_times[identifier]
            if call_time > cutoff
        ]
        
        # Check rate limit
        if len(self.call_times[identifier]) >= self.calls:
            return False
        
        # Add current call
        self.call_times[identifier].append(now)
        return True


# Rate limiters for different endpoint types
generation_limiter = RateLimiter(calls=10, period=3600)  # 10 generations per hour
feedback_limiter = RateLimiter(calls=100, period=300)    # 100 feedback per 5 minutes
api_limiter = RateLimiter(calls=1000, period=3600)       # 1000 API calls per hour


async def check_generation_limit(current_user: User = Depends(get_current_active_user)):
    """Check generation rate limit for user."""
    if not await generation_limiter.is_allowed(str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Generation rate limit exceeded"
        )
    return current_user


async def check_api_limit(current_user: User = Depends(get_current_active_user)):
    """Check general API rate limit for user."""
    if not await api_limiter.is_allowed(str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="API rate limit exceeded"
        )
    return current_user


# Permission constants
class Permissions:
    MANGA_CREATE = "manga:create"
    MANGA_READ = "manga:read"
    MANGA_UPDATE = "manga:update" 
    MANGA_DELETE = "manga:delete"
    MANGA_ADMIN = "manga:admin"
    
    HITL_PARTICIPATE = "hitl:participate"
    HITL_MODERATE = "hitl:moderate"
    
    ANALYTICS_VIEW = "analytics:view"
    SYSTEM_ADMIN = "system:admin"


def create_access_token(data: dict, expires_delta_minutes: int = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta_minutes:
        expire = datetime.utcnow() + timedelta(minutes=expires_delta_minutes)
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")


def create_jwt_token(data: dict, expires_delta_minutes: int = None) -> str:
    """Alias for create_access_token for compatibility."""
    return create_access_token(data, expires_delta_minutes)


def verify_jwt_token(token: str) -> dict:
    """Alias for verify_token for compatibility."""
    return verify_token(token)

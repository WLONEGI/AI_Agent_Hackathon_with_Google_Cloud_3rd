"""Firebase Authentication API endpoints for AI Manga Generation Service."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.config import settings
from app.core.database import get_db
from app.core.firebase_postgresql import get_postgresql_firebase_manager, PostgreSQLFirebaseManager as FirebaseManager
from app.models.user import User
from app.api.v1.security import create_access_token, RateLimiter, get_current_active_user as get_current_user, verify_token

logger = structlog.get_logger(__name__)
router = APIRouter()

# Rate limiters
auth_limiter = RateLimiter(calls=5, period=3600)  # 5 attempts per hour
refresh_limiter = RateLimiter(calls=10, period=3600)  # 10 refreshes per hour


class FirebaseLoginRequest(BaseModel):
    """Firebase ID token login request."""
    id_token: str = Field(..., description="Firebase ID token from client")
    device_info: Optional[Dict[str, str]] = Field(None, description="Optional device information")


class AuthResponse(BaseModel):
    """Authentication response model."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token") 
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry time in seconds")
    user: Dict[str, Any] = Field(..., description="User information")


class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str = Field(..., description="Valid refresh token")


@router.post("/auth/google/login", response_model=AuthResponse)
async def firebase_google_login(
    request: FirebaseLoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    firebase_manager: FirebaseManager = Depends(get_postgresql_firebase_manager)
) -> AuthResponse:
    """
    Authenticate user with Firebase ID token (Google OAuth).
    
    This endpoint:
    1. Verifies Firebase ID token
    2. Creates/updates user in local database
    3. Issues JWT tokens for API access
    4. Sets up user session
    """
    client_ip = http_request.client.host
    
    # Rate limiting check
    if not await auth_limiter.is_allowed(client_ip):
        logger.warning("Rate limit exceeded for login", ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    try:
        # Development Mock Authentication
        import os
        if os.getenv('MOCK_GOOGLE_AUTH', 'false').lower() == 'true' and request.id_token == 'mock-dev-token':
            logger.info("Using mock authentication for development")
            decoded_token = {
                'uid': 'a0000000-b000-c000-d000-e00000000001',
                'email': 'dev@example.com',
                'email_verified': True
            }
            firebase_uid = decoded_token['uid']
            email = decoded_token.get('email')
            email_verified = decoded_token.get('email_verified', False)
            firebase_user = {
                'display_name': 'Development User',
                'photo_url': None
            }
        else:
            # Ensure Firebase is initialized
            if not firebase_manager.is_initialized():
                project_id = os.getenv('FIREBASE_PROJECT_ID', 'comic-ai-agent-470309')
                credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')

                success = firebase_manager.initialize(project_id, credentials_path)
                logger.info("Firebase initialization during login", success=success)

            # Step 1: Verify Firebase ID token
            decoded_token = await firebase_manager.verify_id_token(request.id_token)

            firebase_uid = decoded_token['uid']
            email = decoded_token.get('email')
            email_verified = decoded_token.get('email_verified', False)

            # Step 2: Get detailed user info from Firebase
            firebase_user = await firebase_manager.get_user(firebase_uid)
        
        if not email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not verified. Please verify your email with Google."
            )
        
        logger.info("Firebase token verified", uid=firebase_uid, email=email)
        
        # Step 2: Get detailed user info from Firebase
        firebase_user = await firebase_manager.get_user(firebase_uid)
        
        # Step 3: Find or create user in local database
        user = await db.get(User, firebase_uid)

        # If user not found by ID, also check by email (for existing users with different UIDs)
        if not user and email:
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
        
        if not user:
            # Create username from email
            username_base = email.split('@')[0] if email else firebase_uid[:8]
            username = username_base
            
            # Ensure username uniqueness
            counter = 1
            while True:
                existing_user = await db.execute(
                    select(User).where(User.username == username)
                )
                if existing_user.scalar_one_or_none() is None:
                    break
                username = f"{username_base}{counter}"
                counter += 1
            
            # Create new user
            user = User(
                id=firebase_uid,
                email=email,
                username=username,
                display_name=firebase_user.get('display_name') or email.split('@')[0],
                is_active=True,
                account_type='free',
                firebase_claims=decoded_token,
                provider='google',
                hashed_password=None  # OAuth users don't have passwords
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            # Create user document in Firestore
            await firebase_manager.create_user_document({
                'uid': firebase_uid,
                'email': email,
                'display_name': user.display_name,
                'user_type': 'free',
                'photo_url': firebase_user.get('photo_url')
            })
            
            # Set custom claims
            await firebase_manager.set_custom_claims(firebase_uid, {
                'user_type': 'free',
                'tier': 'basic',
                'quota': {'daily_limit': 3, 'monthly_limit': 90}
            })
            
            logger.info("New user created", user_id=firebase_uid, email=email, username=username)
        else:
            # Update existing user
            user.firebase_claims = decoded_token
            user.last_login_at = None  # Will be set by the database
            await db.commit()
            await db.refresh(user)
            
            logger.info("Existing user updated", user_id=firebase_uid)
        
        # Update last login in Firestore
        await firebase_manager.update_user_last_login(firebase_uid)
        
        # Step 4: Generate JWT tokens
        jwt_payload = {
            'sub': user.id,
            'email': user.email,
            'user_type': user.account_type,
            'firebase_uid': firebase_uid,
            'email_verified': email_verified
        }
        
        access_token = create_access_token(jwt_payload, expires_delta_minutes=60)
        refresh_token = create_access_token(jwt_payload, expires_delta_minutes=10080)  # 7 days
        
        # Step 5: Prepare response
        user_info = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'display_name': user.display_name,
            'account_type': user.account_type,
            'provider': user.provider,
            'is_active': user.is_active,
            'photo_url': firebase_user.get('photo_url'),
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': firebase_user.get('last_sign_in')
        }
        
        logger.info("Login successful", user_id=firebase_uid, account_type=user.account_type)
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
            user=user_info
        )
        
    except ValueError as e:
        # Firebase token verification error
        logger.warning("Invalid Firebase token", error=str(e), ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error("Login failed", error=str(e), ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed. Please try again."
        )


@router.post("/auth/refresh", response_model=AuthResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    firebase_manager: FirebaseManager = Depends(get_postgresql_firebase_manager)
) -> AuthResponse:
    """
    Refresh access token using refresh token.
    """
    client_ip = http_request.client.host
    
    # Rate limiting check
    if not await refresh_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many refresh attempts. Please try again later."
        )
    
    try:
        # Verify refresh token (same verification as access token)
        from app.api.v1.security import verify_token
        payload = verify_token(request.refresh_token)
        
        user_id = payload.get('sub')
        if not user_id:
            raise ValueError("Invalid token payload")
        
        # Get user from database
        user = await db.get(User, user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Generate new tokens
        jwt_payload = {
            'sub': user.id,
            'email': user.email,
            'user_type': user.account_type,
            'firebase_uid': user.id,
            'email_verified': True
        }
        
        access_token = create_access_token(jwt_payload, expires_delta_minutes=60)
        new_refresh_token = create_access_token(jwt_payload, expires_delta_minutes=10080)
        
        # Get latest Firebase user info
        firebase_user = await firebase_manager.get_user(user.id)
        user_info = {
            'id': user.id,
            'email': user.email,
            'display_name': user.display_name,
            'account_type': user.account_type,
            'is_active': user.is_active,
            'photo_url': firebase_user.get('photo_url'),
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'last_login': firebase_user.get('last_sign_in')
        }
        
        logger.info("Token refresh successful", user_id=user_id)
        
        return AuthResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=3600,
            user=user_info
        )
        
    except Exception as e:
        logger.warning("Token refresh failed", error=str(e), ip=client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.post("/auth/logout")
async def logout(
    http_request: Request,
    firebase_manager: FirebaseManager = Depends(get_postgresql_firebase_manager)
):
    """
    Logout user (client should delete tokens).
    """
    # In stateless JWT system, logout is primarily client-side
    # But we can log the event for security monitoring
    
    client_ip = http_request.client.host
    logger.info("User logout", ip=client_ip)
    
    return JSONResponse(
        content={
            "message": "Logged out successfully",
            "instructions": "Please delete your tokens on the client side"
        },
        status_code=status.HTTP_200_OK
    )


@router.get("/auth/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    firebase_manager: FirebaseManager = Depends(get_postgresql_firebase_manager)
) -> Dict[str, Any]:
    """
    Get current authenticated user information.
    """
    try:
        # Get latest Firebase user info
        firebase_user = await firebase_manager.get_user(current_user.id)
        
        return {
            'id': current_user.id,
            'email': current_user.email,
            'display_name': current_user.display_name,
            'account_type': current_user.account_type,
            'is_active': current_user.is_active,
            'photo_url': firebase_user.get('photo_url'),
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'last_login': firebase_user.get('last_sign_in'),
            'firebase_claims': current_user.firebase_claims,
            'permissions': _get_user_permissions(current_user.account_type)
        }
        
    except Exception as e:
        logger.error("Failed to get user info", user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


def _get_user_permissions(account_type: str) -> Dict[str, Any]:
    """Get user permissions based on account type."""
    permissions = {
        'free': {
            'manga_generation': {'daily_limit': 3, 'quality': 'standard'},
            'features': ['basic_generation', 'view_own', 'download_own']
        },
        'premium': {
            'manga_generation': {'daily_limit': 100, 'quality': 'high'},
            'features': ['unlimited_generation', 'view_own', 'download_own', 'edit_own', 'share_public']
        },
        'admin': {
            'manga_generation': {'daily_limit': -1, 'quality': 'ultra'},
            'features': ['*']
        }
    }
    
    return permissions.get(account_type, permissions['free'])


@router.post("/auth/test/mock")
async def test_mock_authentication(
    request: FirebaseLoginRequest,
    firebase_manager: FirebaseManager = Depends(get_postgresql_firebase_manager)
):
    """
    Test mock authentication for development.
    Simplified version that doesn't touch database.
    """
    try:
        # Force Firebase initialization if not already done
        if not firebase_manager.is_initialized():
            import os
            project_id = os.getenv('FIREBASE_PROJECT_ID', 'comic-ai-agent-470309')
            credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
            
            success = firebase_manager.initialize(project_id, credentials_path)
            logger.info("Firebase initialization forced", success=success, project_id=project_id)
        
        # Step 1: Verify Firebase ID token
        decoded_token = await firebase_manager.verify_id_token(request.id_token)
        
        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email')
        
        logger.info("Mock token test successful", uid=firebase_uid, email=email)
        
        # Step 2: Get detailed user info from Firebase
        firebase_user = await firebase_manager.get_user(firebase_uid)
        
        # Return simple response without database operations
        return {
            "status": "success",
            "message": "Mock authentication working",
            "firebase_token": decoded_token,
            "firebase_user": firebase_user,
            "firebase_initialized": firebase_manager.is_initialized(),
            "firebase_mock_mode": firebase_manager.is_mock_mode()
        }
        
    except Exception as e:
        logger.error("Mock test failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock test failed: {str(e)}"
        )



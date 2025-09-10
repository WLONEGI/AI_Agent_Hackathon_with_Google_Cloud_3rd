"""Firebase configuration and initialization for AI Manga Generation Service."""

import os
import json
import base64
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, auth, firestore
from google.oauth2 import service_account
import structlog

# Import settings for environment detection (avoid circular import)
def _is_development_environment() -> bool:
    """Check if running in development environment."""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    return env in ('development', 'dev', 'local')

logger = structlog.get_logger(__name__)


class FirebaseManager:
    """Firebase authentication and service manager."""
    
    def __init__(self):
        self._app: Optional[firebase_admin.App] = None
        self._firestore_client: Optional[firestore.Client] = None
        self._initialized = False
        self._mock_mode = False
        
    def initialize(self, project_id: str, credentials_path: Optional[str] = None) -> bool:
        """
        Initialize Firebase Admin SDK with fallback to mock mode.
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account key file (optional)
            
        Returns:
            bool: True if initialization successful
        """
        try:
            if self._initialized:
                logger.info("Firebase already initialized")
                return True
                
            # Check if credentials file exists
            if credentials_path and not os.path.exists(credentials_path):
                logger.warning("Firebase credentials file not found", path=credentials_path)
                return self._enable_mock_mode()
                
            # Try multiple credential sources
            cred = None
            
            # 1. Service account key file
            if credentials_path and os.path.exists(credentials_path):
                try:
                    cred = credentials.Certificate(credentials_path)
                    logger.info("Using service account key file", path=credentials_path)
                except Exception as e:
                    logger.warning("Failed to load credentials file", path=credentials_path, error=str(e))
                    return self._enable_mock_mode()
                
            # 2. Environment variable with JSON key
            elif os.getenv('FIREBASE_CREDENTIALS_JSON'):
                try:
                    key_data = json.loads(os.getenv('FIREBASE_CREDENTIALS_JSON'))
                    cred = credentials.Certificate(key_data)
                    logger.info("Using credentials from environment variable")
                except Exception as e:
                    logger.warning("Failed to parse credentials from environment", error=str(e))
                    return self._enable_mock_mode()
                
            # 3. Google Cloud Application Default Credentials
            else:
                try:
                    cred = credentials.ApplicationDefault()
                    logger.info("Using Application Default Credentials")
                except Exception as e:
                    logger.warning("Failed to use Application Default Credentials", error=str(e))
                    return self._enable_mock_mode()
            
            # Initialize Firebase App
            self._app = firebase_admin.initialize_app(cred, {
                'projectId': project_id,
                'databaseURL': f'https://{project_id}-default-rtdb.firebaseio.com',
            })
            
            # Initialize Firestore client
            self._firestore_client = firestore.client()
            
            self._initialized = True
            self._mock_mode = False
            logger.info("Firebase initialization successful", project_id=project_id)
            return True
            
        except Exception as e:
            logger.error("Firebase initialization failed, enabling mock mode", error=str(e))
            return self._enable_mock_mode()
    
    def _enable_mock_mode(self) -> bool:
        """Enable mock authentication mode for development."""
        self._mock_mode = True
        self._initialized = True
        logger.warning("Firebase mock mode enabled - suitable for development only")
        return True
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token and return decoded claims.
        Supports both real Firebase tokens and development mock tokens.
        
        Args:
            id_token: Firebase ID token or mock JWT token
            
        Returns:
            Dict containing decoded token claims
            
        Raises:
            ValueError: If token is invalid
        """
        if not self._initialized:
            raise RuntimeError("Firebase not initialized")
        
        # Check if this is a mock token (only in development environment)
        is_dev_env = _is_development_environment()
        if is_dev_env and self._is_mock_token(id_token):
            logger.info("Processing mock token for development environment")
            return self._mock_verify_token(id_token)
        elif not is_dev_env and self._is_mock_token(id_token):
            logger.error("Mock token rejected in production environment")
            raise ValueError("Mock tokens not allowed in production")
        
        # Mock mode - accept any token in mock mode
        if self._mock_mode:
            logger.info("Mock mode - accepting token")
            return self._mock_verify_token(id_token)
        
        try:
            decoded_token = auth.verify_id_token(id_token)
            logger.info("Token verified successfully", user_id=decoded_token.get('uid'))
            return decoded_token
            
        except auth.InvalidIdTokenError as e:
            logger.warning("Invalid ID token", error=str(e))
            raise ValueError("Invalid ID token")
            
        except auth.ExpiredIdTokenError as e:
            logger.warning("Expired ID token", error=str(e))
            raise ValueError("Token expired")
            
        except Exception as e:
            logger.error("Token verification failed", error=str(e))
            raise ValueError("Token verification failed")
    
    def _is_mock_token(self, id_token: str) -> bool:
        """
        Check if the token is a mock token for development.
        
        Mock tokens are identified by:
        1. JWT structure with alg: 'none' in header
        2. iss: 'mock-google' in payload
        """
        try:
            # Split JWT into parts
            parts = id_token.split('.')
            if len(parts) != 3:
                return False
            
            # Decode header (add padding if needed)
            header_padded = parts[0] + '=' * (4 - len(parts[0]) % 4)
            header = json.loads(base64.urlsafe_b64decode(header_padded).decode('utf-8'))
            
            # Decode payload (add padding if needed)
            payload_padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_padded).decode('utf-8'))
            
            # Check mock token indicators
            is_mock_alg = header.get('alg') == 'none'
            is_mock_iss = payload.get('iss') == 'mock-google'
            
            return is_mock_alg and is_mock_iss
            
        except Exception as e:
            logger.debug("Error checking if token is mock", error=str(e))
            return False
    
    def _mock_verify_token(self, id_token: str) -> Dict[str, Any]:
        """
        Mock token verification for development.
        Supports both fixed mock token and JWT mock tokens.
        """
        # Handle legacy fixed mock token
        if id_token == "mock_firebase_google_token_for_development":
            return {
                'uid': 'mock-user-id',
                'email': 'mock@example.com',
                'email_verified': True,
                'name': 'Mock User',
                'picture': None,
                'iss': 'https://securetoken.google.com/comic-ai-agent-470309',
                'aud': 'comic-ai-agent-470309',
                'auth_time': 1700000000,
                'user_id': 'mock-user-id',
                'sub': 'mock-user-id',
                'iat': 1700000000,
                'exp': 1700003600,
                'firebase': {
                    'identities': {
                        'google.com': ['mock-google-id'],
                        'email': ['mock@example.com']
                    },
                    'sign_in_provider': 'google.com'
                }
            }
        
        # Handle JWT mock tokens (no signature verification)
        try:
            parts = id_token.split('.')
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")
            
            # Decode payload (add padding if needed)
            payload_padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_padded).decode('utf-8'))
            
            # Validate mock token structure
            if payload.get('iss') != 'mock-google':
                raise ValueError("Not a valid mock token")
            
            # Return Firebase-compatible token structure
            mock_uid = payload.get('sub', 'mock-user-id')
            mock_email = payload.get('email', 'mock@example.com')
            
            logger.info("Mock token verified", uid=mock_uid, email=mock_email)
            
            return {
                'uid': mock_uid,
                'email': mock_email,
                'email_verified': True,
                'name': payload.get('name', 'Mock User'),
                'picture': payload.get('picture'),
                'iss': 'https://securetoken.google.com/comic-ai-agent-470309',
                'aud': 'comic-ai-agent-470309',
                'auth_time': payload.get('iat', 1700000000),
                'user_id': mock_uid,
                'sub': mock_uid,
                'iat': payload.get('iat', 1700000000),
                'exp': payload.get('exp', 1700003600),
                'firebase': {
                    'identities': {
                        'google.com': [payload.get('sub', 'mock-google-id')],
                        'email': [mock_email]
                    },
                    'sign_in_provider': 'google.com'
                }
            }
            
        except Exception as e:
            logger.warning("Failed to verify mock token", error=str(e))
            raise ValueError("Invalid mock token")
    
    async def get_user(self, uid: str) -> Dict[str, Any]:
        """
        Get user information from Firebase Auth.
        
        Args:
            uid: User ID
            
        Returns:
            Dict containing user information
        """
        if not self._initialized:
            raise RuntimeError("Firebase not initialized")
        
        # Check if this is a mock user (development environment)
        is_dev_env = _is_development_environment()
        if is_dev_env and uid.startswith('mock-'):
            logger.info("Getting mock user info for development environment", uid=uid)
            return self._mock_get_user(uid)
        
        # Mock mode - return mock user data
        if self._mock_mode:
            return self._mock_get_user(uid)
            
        try:
            user_record = auth.get_user(uid)
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name,
                'photo_url': user_record.photo_url,
                'disabled': user_record.disabled,
                'created_at': user_record.user_metadata.creation_timestamp,
                'last_sign_in': user_record.user_metadata.last_sign_in_timestamp,
                'custom_claims': user_record.custom_claims or {}
            }
            
        except auth.UserNotFoundError:
            raise ValueError(f"User {uid} not found")
            
        except Exception as e:
            logger.error("Failed to get user", uid=uid, error=str(e))
            raise ValueError("Failed to get user information")
    
    def _mock_get_user(self, uid: str) -> Dict[str, Any]:
        """Mock user data for development."""
        # Support both original mock-user-id and any mock-* ID
        if uid == 'mock-user-id' or uid.startswith('mock-'):
            # Extract number from mock-user-123 format for variety
            user_num = uid.split('-')[-1] if '-' in uid else '1'
            email = f'mock{user_num}@example.com' if user_num.isdigit() else 'mock@example.com'
            
            return {
                'uid': uid,
                'email': email,
                'email_verified': True,
                'display_name': f'Mock User {user_num}' if user_num.isdigit() else 'Mock User',
                'photo_url': None,
                'disabled': False,
                'created_at': 1700000000,
                'last_sign_in': 1700000000,
                'custom_claims': {'user_type': 'free'}
            }
        else:
            raise ValueError(f"Mock user {uid} not found")
    
    async def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> bool:
        """
        Set custom claims for a user.
        
        Args:
            uid: User ID
            claims: Custom claims dictionary
            
        Returns:
            bool: True if successful
        """
        if not self._initialized:
            raise RuntimeError("Firebase not initialized")
        
        # Mock mode - just log the operation
        if self._mock_mode:
            logger.info("Mock: Custom claims set", uid=uid, claims=claims)
            return True
            
        try:
            auth.set_custom_user_claims(uid, claims)
            logger.info("Custom claims set successfully", uid=uid, claims=claims)
            return True
            
        except Exception as e:
            logger.error("Failed to set custom claims", uid=uid, error=str(e))
            return False
    
    async def create_user_document(self, user_data: Dict[str, Any]) -> bool:
        """
        Create user document in Firestore.
        
        Args:
            user_data: User data dictionary
            
        Returns:
            bool: True if successful
        """
        if not self._initialized:
            raise RuntimeError("Firebase not initialized")
        
        # Mock mode - just log the operation
        if self._mock_mode:
            logger.info("Mock: User document created", uid=user_data.get('uid'))
            return True
            
        if not self._firestore_client:
            logger.warning("Firestore client not available")
            return False
            
        try:
            doc_ref = self._firestore_client.collection('users').document(user_data['uid'])
            doc_ref.set({
                'uid': user_data['uid'],
                'email': user_data['email'],
                'display_name': user_data.get('display_name'),
                'created_at': firestore.SERVER_TIMESTAMP,
                'last_updated': firestore.SERVER_TIMESTAMP,
                'user_type': user_data.get('user_type', 'free'),
                'api_quota': user_data.get('api_quota', {'daily_limit': 3, 'monthly_limit': 90}),
                'profile': {
                    'photo_url': user_data.get('photo_url'),
                    'preferences': {}
                }
            })
            
            logger.info("User document created", uid=user_data['uid'])
            return True
            
        except Exception as e:
            logger.error("Failed to create user document", error=str(e))
            return False
    
    async def update_user_last_login(self, uid: str) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            uid: User ID
            
        Returns:
            bool: True if successful
        """
        if not self._initialized:
            return False
        
        # Mock mode - just log the operation
        if self._mock_mode:
            logger.info("Mock: Last login updated", uid=uid)
            return True
            
        if not self._firestore_client:
            return False
            
        try:
            doc_ref = self._firestore_client.collection('users').document(uid)
            doc_ref.update({
                'last_login': firestore.SERVER_TIMESTAMP,
                'last_updated': firestore.SERVER_TIMESTAMP
            })
            return True
            
        except Exception as e:
            logger.error("Failed to update last login", uid=uid, error=str(e))
            return False
    
    def is_initialized(self) -> bool:
        """Check if Firebase is properly initialized."""
        return self._initialized
    
    def is_mock_mode(self) -> bool:
        """Check if running in mock mode."""
        return self._mock_mode
    
    @property
    def app(self) -> Optional[firebase_admin.App]:
        """Get Firebase app instance."""
        return self._app
    
    @property
    def firestore(self) -> Optional[firestore.Client]:
        """Get Firestore client instance."""
        return self._firestore_client


# Global Firebase manager instance
firebase_manager = FirebaseManager()


async def get_firebase_manager() -> FirebaseManager:
    """Get the global Firebase manager instance."""
    return firebase_manager


def initialize_firebase(project_id: str, credentials_path: Optional[str] = None) -> bool:
    """
    Initialize Firebase with project configuration.
    
    Args:
        project_id: GCP project ID
        credentials_path: Optional path to service account key
        
    Returns:
        bool: True if initialization successful
    """
    return firebase_manager.initialize(project_id, credentials_path)
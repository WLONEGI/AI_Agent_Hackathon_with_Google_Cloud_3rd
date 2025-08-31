"""Firebase configuration and initialization for AI Manga Generation Service."""

import os
import json
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, auth, firestore
from google.oauth2 import service_account
import structlog

logger = structlog.get_logger(__name__)


class FirebaseManager:
    """Firebase authentication and service manager."""
    
    def __init__(self):
        self._app: Optional[firebase_admin.App] = None
        self._firestore_client: Optional[firestore.Client] = None
        self._initialized = False
        
    def initialize(self, project_id: str, credentials_path: Optional[str] = None) -> bool:
        """
        Initialize Firebase Admin SDK.
        
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
                
            # Try multiple credential sources
            cred = None
            
            # 1. Service account key file
            if credentials_path and os.path.exists(credentials_path):
                cred = credentials.Certificate(credentials_path)
                logger.info("Using service account key file", path=credentials_path)
                
            # 2. Environment variable with JSON key
            elif os.getenv('FIREBASE_CREDENTIALS_JSON'):
                key_data = json.loads(os.getenv('FIREBASE_CREDENTIALS_JSON'))
                cred = credentials.Certificate(key_data)
                logger.info("Using credentials from environment variable")
                
            # 3. Google Cloud Application Default Credentials
            else:
                cred = credentials.ApplicationDefault()
                logger.info("Using Application Default Credentials")
            
            # Initialize Firebase App
            self._app = firebase_admin.initialize_app(cred, {
                'projectId': project_id,
                'databaseURL': f'https://{project_id}-default-rtdb.firebaseio.com',
            })
            
            # Initialize Firestore client
            self._firestore_client = firestore.client()
            
            self._initialized = True
            logger.info("Firebase initialization successful", project_id=project_id)
            return True
            
        except Exception as e:
            logger.error("Firebase initialization failed", error=str(e))
            return False
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token and return decoded claims.
        
        Args:
            id_token: Firebase ID token
            
        Returns:
            Dict containing decoded token claims
            
        Raises:
            ValueError: If token is invalid
        """
        if not self._initialized:
            raise RuntimeError("Firebase not initialized")
            
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
        if not self._initialized or not self._firestore_client:
            raise RuntimeError("Firebase not initialized")
            
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
        if not self._initialized or not self._firestore_client:
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
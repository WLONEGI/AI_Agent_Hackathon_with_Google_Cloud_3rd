"""Firebase configuration settings."""

from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field


class FirebaseSettings(BaseSettings):
    """Firebase configuration settings."""
    
    # Firebase Authentication
    firebase_project_id: str = Field(..., env="FIREBASE_PROJECT_ID")
    firebase_credentials_path: Optional[str] = Field(None, env="FIREBASE_CREDENTIALS_PATH")
    firebase_credentials_json: Optional[str] = Field(None, env="FIREBASE_CREDENTIALS_JSON")
    
    # Firebase Database
    firebase_database_url: Optional[str] = Field(None, env="FIREBASE_DATABASE_URL")
    
    # Firebase Storage
    firebase_storage_bucket: Optional[str] = Field(None, env="FIREBASE_STORAGE_BUCKET")
    
    # Firebase Auth Configuration
    firebase_auth_domain: Optional[str] = Field(None, env="FIREBASE_AUTH_DOMAIN")
    firebase_api_key: Optional[str] = Field(None, env="FIREBASE_API_KEY")
    
    # Token Configuration
    firebase_token_expiry_hours: int = Field(24, env="FIREBASE_TOKEN_EXPIRY_HOURS")
    firebase_refresh_token_expiry_days: int = Field(30, env="FIREBASE_REFRESH_TOKEN_EXPIRY_DAYS")
    
    # Security Configuration
    firebase_verify_email: bool = Field(True, env="FIREBASE_VERIFY_EMAIL")
    firebase_enforce_email_verification: bool = Field(False, env="FIREBASE_ENFORCE_EMAIL_VERIFICATION")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def get_firebase_config(self) -> dict:
        """Get Firebase configuration dictionary."""
        config = {
            "project_id": self.firebase_project_id,
            "database_url": self.firebase_database_url or f"https://{self.firebase_project_id}-default-rtdb.firebaseio.com/",
        }
        
        if self.firebase_api_key:
            config["api_key"] = self.firebase_api_key
        
        if self.firebase_auth_domain:
            config["auth_domain"] = self.firebase_auth_domain
        
        if self.firebase_storage_bucket:
            config["storage_bucket"] = self.firebase_storage_bucket
        
        return config
    
    def get_credentials_config(self) -> dict:
        """Get credentials configuration."""
        return {
            "credentials_path": self.firebase_credentials_path,
            "credentials_json": self.firebase_credentials_json,
            "project_id": self.firebase_project_id
        }
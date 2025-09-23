from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyUrl, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = Field(default="spell-backend")
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8080)

    database_url: str = Field(..., description="SQLAlchemy connection string")


    gcs_bucket_preview: str = Field(...)
    signed_url_ttl_seconds: int = Field(default=3600, ge=60, le=86400)

    firebase_project_id: str = Field(...)
    firebase_client_email: str = Field(...)
    firebase_private_key: str = Field(..., description="Service account private key with newlines escaped")

    websocket_base_url: Optional[AnyUrl] = Field(default=None)

    auth_secret_key: str = Field(default="change-me", min_length=12)
    access_token_expires_minutes: int = Field(default=60, ge=5, le=720)
    refresh_token_expires_days: int = Field(default=30, ge=1, le=90)

    vertex_project_id: str = Field(default="", description="GCP project ID for Vertex AI")
    vertex_location: str = Field(default="asia-northeast1")
    vertex_text_model: str = Field(default="gemini-2.5")
    vertex_image_model: str = Field(default="imagen-4.0-ultra")
    vertex_credentials_json: str = Field(
        ...,
        description="Raw or base64-encoded JSON service account credentials for Vertex AI",
    )

    # HITL (Human-in-the-loop) Configuration
    hitl_enabled: bool = Field(default=True, description="Enable HITL feedback system")
    hitl_feedback_timeout_minutes: int = Field(default=30, ge=1, le=120, description="Feedback timeout in minutes")
    hitl_max_retry_attempts: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts for failed feedback integration")
    hitl_default_quality_threshold: float = Field(default=0.72, ge=0.0, le=1.0, description="Default quality threshold for HITL phases")
    
    # HITL Phase-specific Configuration
    hitl_enabled_phases: str = Field(default="1,2", description="Comma-separated list of phases where HITL is enabled (e.g., '1,2,3')")
    hitl_max_iterations: int = Field(default=3, ge=1, le=10, description="Maximum feedback iterations per phase")
    hitl_auto_approve_threshold: float = Field(default=0.9, ge=0.0, le=1.0, description="Quality threshold for automatic approval")
    hitl_require_manual_approval: bool = Field(default=False, description="Always require manual approval regardless of quality score")
    
    # HITL Environment-specific overrides
    hitl_development_mode: bool = Field(default=True, description="Enable development mode with extended timeouts and verbose logging")
    hitl_skip_on_error: bool = Field(default=True, description="Skip HITL on errors and continue with standard pipeline")

    @validator("firebase_private_key")
    def _normalize_private_key(cls, value: str) -> str:
        return value.replace("\\n", "\n") if value else value

    @validator("vertex_credentials_json")
    def _validate_vertex_credentials(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("VERTEX_CREDENTIALS_JSON must not be empty")
        return stripped
    
    @validator("hitl_enabled_phases")
    def _validate_hitl_phases(cls, value: str) -> str:
        """Validate that hitl_enabled_phases contains valid phase numbers"""
        if not value.strip():
            return ""
        
        try:
            phases = [int(phase.strip()) for phase in value.split(",") if phase.strip()]
            # Validate phase numbers are in valid range (1-7 for manga generation pipeline)
            for phase in phases:
                if phase < 1 or phase > 7:
                    raise ValueError(f"Phase {phase} is not in valid range (1-7)")
            return value
        except ValueError as e:
            raise ValueError(f"Invalid hitl_enabled_phases format: {value}. Expected comma-separated integers (e.g., '1,2,3'). Error: {e}")
    
    def get_hitl_enabled_phases(self) -> List[int]:
        """Get list of phase numbers where HITL is enabled"""
        if not self.hitl_enabled or not self.hitl_enabled_phases.strip():
            return []
        
        try:
            return [int(phase.strip()) for phase in self.hitl_enabled_phases.split(",") if phase.strip()]
        except ValueError:
            return []  # Return empty list if parsing fails
    
    def is_hitl_enabled_for_phase(self, phase: int) -> bool:
        """Check if HITL is enabled for a specific phase"""
        if not self.hitl_enabled:
            return False
        
        enabled_phases = self.get_hitl_enabled_phases()
        return phase in enabled_phases


@lru_cache
def get_settings() -> Settings:
    return Settings()

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import AnyUrl, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    app_name: str = Field(default="spell-backend")
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8080)

    database_url: str = Field(..., description="SQLAlchemy connection string")

    cloud_tasks_queue: str = Field(...)
    cloud_tasks_project: str = Field(...)
    cloud_tasks_location: str = Field(...)
    cloud_tasks_service_url: AnyUrl = Field(..., description="Target Cloud Run service URL")

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
    vertex_text_model: str = Field(default="gemini-1.5-flash")
    vertex_image_model: str = Field(default="imagen-3.0-generate-image")

    @validator("firebase_private_key")
    def _normalize_private_key(cls, value: str) -> str:
        return value.replace("\\n", "\n") if value else value


@lru_cache
def get_settings() -> Settings:
    return Settings()

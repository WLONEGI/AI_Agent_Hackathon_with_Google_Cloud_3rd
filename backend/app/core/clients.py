from __future__ import annotations

from functools import lru_cache

from google.cloud import storage

from .settings import get_settings



@lru_cache
def get_storage_client() -> storage.Client:
    settings = get_settings()
    return storage.Client(project=settings.firebase_project_id)

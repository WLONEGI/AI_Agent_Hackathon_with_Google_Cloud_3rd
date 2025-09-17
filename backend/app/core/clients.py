from __future__ import annotations

from functools import lru_cache

from google.cloud import storage, tasks_v2

from .settings import get_settings


@lru_cache
def get_tasks_client() -> tasks_v2.CloudTasksClient:
    return tasks_v2.CloudTasksClient()


@lru_cache
def get_storage_client() -> storage.Client:
    settings = get_settings()
    return storage.Client(project=settings.firebase_project_id)

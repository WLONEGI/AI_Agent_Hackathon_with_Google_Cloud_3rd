import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

import unittest

try:  # pragma: no cover - optional dependency guard
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.api.schemas.manga import GenerateRequest
    from app.db.base import Base
    from app.db.models import (
        GeneratedImage,
        MangaAsset,
        MangaProject,
        MangaProjectStatus,
        MangaSession,
        MangaSessionStatus,
        PreviewCacheMetadata,
        PreviewVersion,
    )
    from app.services.generation_service import GenerationService
    from app.services.pipeline_service import PipelineOrchestrator
    _SQLALCHEMY_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - skip when dependency missing
    _SQLALCHEMY_AVAILABLE = False


class _FakeSettings:
    app_name = "spell-backend"
    cloud_tasks_project = "test-project"
    cloud_tasks_location = "asia-northeast1"
    cloud_tasks_queue = "spell-queue"
    cloud_tasks_service_url = "https://spell-backend.example.com"
    gcs_bucket_preview = "spell-preview"
    signed_url_ttl_seconds = 3600
    websocket_base_url = "wss://backend.example.com"
    firebase_project_id = "firebase-test"
    firebase_client_email = "svc@firebase-test"
    firebase_private_key = "-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----\n"
    auth_secret_key = "test-secret-key"
    access_token_expires_minutes = 60
    refresh_token_expires_days = 30


class _FakeBlob:
    def __init__(self, name: str, calls: List[str]):
        self.name = name
        self._calls = calls

    def generate_signed_url(self, expiration: datetime, method: str, version: str) -> str:
        self._calls.append(self.name)
        return f"https://signed.example.com/{self.name}"


class _FakeBucket:
    def __init__(self, calls: List[str]):
        self._calls = calls

    def blob(self, name: str) -> _FakeBlob:
        return _FakeBlob(name, self._calls)


class _FakeStorageClient:
    def __init__(self) -> None:
        self.calls: List[str] = []

    def bucket(self, name: str) -> _FakeBucket:
        return _FakeBucket(self.calls)


class _FakeTasksClient:
    def __init__(self) -> None:
        self.requests: List[Dict[str, Any]] = []

    @staticmethod
    def queue_path(project: str, location: str, queue: str) -> str:
        return f"projects/{project}/locations/{location}/queues/{queue}"

    def create_task(self, request: Dict[str, Any]) -> None:
        self.requests.append(request)


class _FakeVertexService:
    async def generate_text(self, prompt: str, *, temperature: float = 0.4) -> str:
        return f"(fake-response) {prompt[:60]}"

    async def generate_image(self, prompt: str) -> list[dict[str, Any]]:
        return [
            {
                "image_base64": None,
                "data_url": None,
                "description": f"placeholder for {prompt[:40]}",
            }
        ]


if _SQLALCHEMY_AVAILABLE:

    class PipelineIntegrationTest(IsolatedAsyncioTestCase):
        async def asyncSetUp(self) -> None:
            self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

            self.fake_tasks = _FakeTasksClient()
            self.fake_storage = _FakeStorageClient()

            self.settings_patch = patch("app.core.settings.get_settings", return_value=_FakeSettings())
            self.tasks_patch = patch("app.core.clients.get_tasks_client", return_value=self.fake_tasks)
            self.storage_patch = patch("app.core.clients.get_storage_client", return_value=self.fake_storage)
            self.vertex_patch = patch("app.services.pipeline_service.get_vertex_service", return_value=_FakeVertexService())

            self.settings_patch.start()
            self.tasks_patch.start()
            self.storage_patch.start()
            self.vertex_patch.start()

        async def asyncTearDown(self) -> None:
            self.settings_patch.stop()
            self.tasks_patch.stop()
            self.storage_patch.stop()
            self.vertex_patch.stop()
            await self.engine.dispose()

        async def test_generation_pipeline_creates_artifacts(self) -> None:
            request_payload = GenerateRequest(
                title="Test Manga",
                text="""This is a sample prompt for the manga generation system that exceeds the minimum length.""",
            )

            async with self.session_factory() as session:  # type: AsyncSession
                generation_service = GenerationService(session)
                response = await generation_service.enqueue_generation(request_payload)
                await session.commit()

                orchestrator = PipelineOrchestrator(session)
                await orchestrator.run(response.request_id)
                await session.commit()

                session_result = await session.execute(
                    select(MangaSession).where(MangaSession.request_id == response.request_id)
                )
                session_obj = session_result.scalar_one()
                self.assertEqual(session_obj.status, MangaSessionStatus.COMPLETED.value)
                self.assertIsNotNone(session_obj.project_id)

                project_result = await session.execute(
                    select(MangaProject).where(MangaProject.id == session_obj.project_id)
                )
                project = project_result.scalar_one()
                self.assertEqual(project.status, MangaProjectStatus.COMPLETED)
                self.assertGreaterEqual(project.total_pages or 0, 8)

                preview_count = await session.execute(
                    select(PreviewVersion).where(PreviewVersion.session_id == session_obj.id)
                )
                self.assertEqual(len(preview_count.scalars().all()), 7, "7フェーズ分のプレビューが生成されること")

                cache_entries = await session.execute(
                    select(PreviewCacheMetadata)
                    .join(PreviewVersion, PreviewCacheMetadata.version_id == PreviewVersion.id)
                    .where(PreviewVersion.session_id == session_obj.id)
                )
                self.assertEqual(len(cache_entries.scalars().all()), 7)

                generated_images = await session.execute(
                    select(GeneratedImage).where(GeneratedImage.session_id == session_obj.id)
                )
                self.assertTrue(generated_images.scalars().all(), "画像メタデータが生成されること")

                assets = await session.execute(select(MangaAsset).where(MangaAsset.project_id == project.id))
                asset_list = assets.scalars().all()
                self.assertTrue(asset_list, "プロジェクト資産が登録されること")

                self.assertTrue(self.fake_storage.calls, "Cloud Storageの署名付きURL生成が呼び出されていること")


else:

    class PipelineIntegrationTest(unittest.TestCase):  # type: ignore[misc]
        def test_sqlalchemy_dependency(self) -> None:
            self.skipTest("SQLAlchemy not installed; pipeline integration test skipped")


if __name__ == "__main__" and _SQLALCHEMY_AVAILABLE:  # pragma: no cover
    asyncio.run(PipelineIntegrationTest().test_generation_pipeline_creates_artifacts())

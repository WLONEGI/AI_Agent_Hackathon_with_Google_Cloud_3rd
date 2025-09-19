from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any, Optional

from app.core.settings import get_settings

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import vertexai
    from vertexai.generative_models import GenerativeModel
    try:  # pragma: no cover - image generation may be unavailable
        from vertexai.generative_models import ImageGenerationModel
    except ImportError:  # pragma: no cover
        ImageGenerationModel = None  # type: ignore
except ImportError:  # pragma: no cover
    vertexai = None
    GenerativeModel = None  # type: ignore
    ImageGenerationModel = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from google.api_core import exceptions as google_exceptions
except ImportError:  # pragma: no cover
    google_exceptions = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from google.oauth2 import service_account
except ImportError:  # pragma: no cover
    service_account = None  # type: ignore


class VertexAIServiceError(RuntimeError):
    """Base class for Vertex AI integration errors."""


class VertexAICredentialsError(VertexAIServiceError):
    """Raised when credentials are missing or invalid."""


class VertexAIUnavailableError(VertexAIServiceError):
    """Raised when the Vertex AI service is unavailable."""


class VertexAIRateLimitError(VertexAIServiceError):
    """Raised when Vertex AI signals resource exhaustion or rate limiting."""


class VertexAIService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._enabled = False
        self._text_model: Optional[GenerativeModel] = None
        self._image_model: Optional[ImageGenerationModel] = None
        if vertexai is None:
            logger.warning("vertexai library is not installed; falling back to stub generation")
            return
        if not self._settings.vertex_project_id:
            logger.error("VERTEX_PROJECT_ID is not configured; Vertex AI integration disabled")
            return
        try:
            credentials = self._build_credentials()
        except VertexAICredentialsError as exc:
            logger.error("Vertex AI credentials could not be loaded: %s", exc)
            return
        try:
            vertexai.init(
                project=self._settings.vertex_project_id,
                location=self._settings.vertex_location,
                credentials=credentials,
            )
            self._text_model = GenerativeModel(self._settings.vertex_text_model)
            if ImageGenerationModel is not None:
                self._image_model = ImageGenerationModel.from_pretrained(self._settings.vertex_image_model)
            else:
                logger.info("ImageGenerationModel not available; image generation will use stub responses")
            self._enabled = True
        except Exception as exc:  # pragma: no cover - initialization
            logger.warning("Vertex AI initialization failed: %s", exc)
            self._enabled = False

    def _build_credentials(self):
        if service_account is None:
            raise VertexAICredentialsError("google-auth library is not installed")

        credential = self._credentials_from_json(self._settings.vertex_credentials_json)
        if credential is None:
            raise VertexAICredentialsError("VERTEX_CREDENTIALS_JSON is invalid or unreadable")
        return credential

    def _credentials_from_json(self, raw: str):
        candidates = [raw]
        try:
            candidates.append(base64.b64decode(raw).decode("utf-8"))
        except Exception:  # pragma: no cover - base64 decode failure
            pass

        for candidate in candidates:
            try:
                info = json.loads(candidate)
                return service_account.Credentials.from_service_account_info(info)
            except json.JSONDecodeError:
                continue
            except Exception as exc:  # pragma: no cover - credential failure
                logger.warning("Failed to load Vertex credentials from JSON: %s", exc)
                return None

        logger.warning("VERTEX_CREDENTIALS_JSON is not valid JSON")
        return None

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def generate_text(self, prompt: str, *, temperature: float = 0.4) -> str:
        if not prompt.strip():
            return ""
        if not self._enabled or self._text_model is None:
            return self._stub_text(prompt)

        def _invoke() -> str:
            if self._text_model is None:
                raise VertexAIUnavailableError("Vertex AI text model is not initialised")
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": 2048,
                "top_p": 0.95,
                "top_k": 40,
                "response_mime_type": "application/json",
            }

            try:
                response = self._text_model.generate_content(
                    [prompt],
                    generation_config=generation_config,
                )
            except TypeError:  # pragma: no cover - older SDKs without response_mime_type
                generation_config.pop("response_mime_type", None)
                response = self._text_model.generate_content(
                    [prompt],
                    generation_config=generation_config,
                )
            except Exception as exc:  # pragma: no cover - runtime failure
                raise self._translate_exception(exc) from exc

            text = getattr(response, "text", None)
            if text:
                return text

            candidates = getattr(response, "candidates", None)
            if candidates:
                first = candidates[0]
                parts = getattr(first, "content", getattr(first, "parts", None))
                if parts:
                    joined = "\n".join(
                        getattr(part, "text", "")
                        for part in getattr(parts, "parts", parts)
                        if getattr(part, "text", "")
                    )
                    if joined:
                        return joined

            raise VertexAIServiceError("Vertex AI returned an empty response")

        return await asyncio.to_thread(_invoke)

    async def generate_image(self, prompt: str) -> list[dict[str, Any]]:
        if not prompt.strip():
            return []
        if not self._enabled or self._image_model is None:
            return [self._stub_image(prompt)]

        def _invoke() -> list[dict[str, Any]]:
            if self._image_model is None:
                raise VertexAIUnavailableError("Vertex AI image model is not initialised")

            try:
                response = self._image_model.generate_images(
                    prompt=prompt,
                    number_of_images=1,
                )
            except Exception as exc:  # pragma: no cover - runtime failure
                raise self._translate_exception(exc) from exc

            results: list[dict[str, Any]] = []
            for image in getattr(response, "images", []):
                image_bytes = getattr(image, "image_bytes", None)
                if not image_bytes:
                    continue
                b64 = base64.b64encode(image_bytes).decode("ascii")
                results.append(
                    {
                        "image_base64": b64,
                        "data_url": f"data:image/png;base64,{b64}",
                    }
                )

            if results:
                return results

            raise VertexAIServiceError("Vertex AI returned no images")

        return await asyncio.to_thread(_invoke)

    def _stub_text(self, prompt: str) -> str:
        summary = prompt.strip().split("\n")[0][:120]
        return f"(stub) {summary}..."

    def _stub_image(self, prompt: str) -> dict[str, Any]:
        return {
            "image_base64": None,
            "data_url": None,
            "description": f"Placeholder image for: {prompt[:100]}",
        }

    def _translate_exception(self, exc: Exception) -> VertexAIServiceError:
        if google_exceptions is not None:
            if isinstance(exc, google_exceptions.ResourceExhausted):
                return VertexAIRateLimitError("Vertex AI rate limit exceeded")
            if isinstance(exc, google_exceptions.DeadlineExceeded):
                return VertexAIUnavailableError("Vertex AI request timed out")
            if isinstance(exc, google_exceptions.GoogleAPICallError):
                return VertexAIServiceError(str(exc))

        # When dependency-specific exceptions are not available, wrap generically
        return VertexAIServiceError(str(exc))


_vertex_service: Optional[VertexAIService] = None


def get_vertex_service() -> VertexAIService:
    global _vertex_service
    if _vertex_service is None:
        _vertex_service = VertexAIService()
    return _vertex_service

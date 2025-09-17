from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any, Dict, Optional

from app.core.settings import get_settings

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import vertexai
    from vertexai.generative_models import GenerativeModel, ImageGenerationModel, Part
except ImportError:  # pragma: no cover
    vertexai = None
    GenerativeModel = None  # type: ignore
    ImageGenerationModel = None  # type: ignore
    Part = None  # type: ignore


class VertexAIService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._enabled = False
        self._text_model: Optional[GenerativeModel] = None
        self._image_model: Optional[ImageGenerationModel] = None
        if vertexai is None or not self._settings.vertex_project_id:
            logger.warning("vertexai library is not installed; falling back to stub generation")
            return
        try:
            vertexai.init(project=self._settings.vertex_project_id, location=self._settings.vertex_location)
            self._text_model = GenerativeModel(self._settings.vertex_text_model)
            self._image_model = ImageGenerationModel.from_pretrained(self._settings.vertex_image_model)
            self._enabled = True
        except Exception as exc:  # pragma: no cover - initialization
            logger.warning("Vertex AI initialization failed: %s", exc)
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def generate_text(self, prompt: str, *, temperature: float = 0.4) -> str:
        if not prompt.strip():
            return ""
        if not self._enabled or self._text_model is None:
            return self._stub_text(prompt)

        def _invoke() -> str:
            response = self._text_model.generate_content(
                [prompt],
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 512,
                    "top_p": 0.95,
                    "top_k": 40,
                },
            )
            if hasattr(response, "text") and response.text:
                return response.text
            if hasattr(response, "candidates") and response.candidates:
                return "\n".join(part.text for part in response.candidates[0].content.parts if getattr(part, "text", ""))
            return self._stub_text(prompt)

        try:
            return await asyncio.to_thread(_invoke)
        except Exception as exc:  # pragma: no cover - runtime failure
            logger.error("Vertex text generation failed: %s", exc)
            return self._stub_text(prompt)

    async def generate_image(self, prompt: str) -> list[dict[str, Any]]:
        if not prompt.strip():
            return []
        if not self._enabled or self._image_model is None:
            return [self._stub_image(prompt)]

        def _invoke() -> list[dict[str, Any]]:
            response = self._image_model.generate_images(
                prompt=prompt,
                number_of_images=1,
            )
            results: list[dict[str, Any]] = []
            for image in response.images:
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
            if not results:
                results.append(self._stub_image(prompt))
            return results

        try:
            return await asyncio.to_thread(_invoke)
        except Exception as exc:  # pragma: no cover - runtime failure
            logger.error("Vertex image generation failed: %s", exc)
            return [self._stub_image(prompt)]

    def _stub_text(self, prompt: str) -> str:
        summary = prompt.strip().split("\n")[0][:120]
        return f"(stub) {summary}..."

    def _stub_image(self, prompt: str) -> dict[str, Any]:
        return {
            "image_base64": None,
            "data_url": None,
            "description": f"Placeholder image for: {prompt[:100]}",
        }


_vertex_service: Optional[VertexAIService] = None


def get_vertex_service() -> VertexAIService:
    global _vertex_service
    if _vertex_service is None:
        _vertex_service = VertexAIService()
    return _vertex_service

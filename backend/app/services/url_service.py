"""URL construction service for CDN and storage management."""

from typing import Optional
from app.core.config import settings


class URLService:
    """Service for constructing optimized URLs for images and content."""
    
    def __init__(self):
        self.cdn_base_url = settings.cdn_url.rstrip('/')
        self.storage_base_url = "https://storage.googleapis.com"
    
    def get_preview_url(self, filename: str) -> str:
        """Get CDN-optimized URL for preview content."""
        return f"{self.cdn_base_url}/preview/{filename}"
    
    def get_image_url(self, filename: str, signed: bool = False) -> str:
        """Get CDN-optimized URL for generated images."""
        if signed:
            # For signed URLs, use direct storage (CDN preserves query params)
            return f"{self.cdn_base_url}/images/{filename}"
        else:
            # For public images, use CDN
            return f"{self.cdn_base_url}/images/{filename}"
    
    def get_thumbnail_url(self, filename: str) -> str:
        """Get CDN-optimized URL for thumbnails."""
        return f"{self.cdn_base_url}/preview/{filename}"
    
    def get_final_product_url(self, filename: str, signed: bool = True) -> str:
        """Get URL for final products (typically signed)."""
        if signed:
            return f"{self.storage_base_url}/manga-final-products/{filename}?signed=true"
        else:
            return f"{self.cdn_base_url}/images/{filename}"
    
    def construct_manga_files_urls(self, manga_id: str) -> dict:
        """Construct all URLs for a manga work."""
        return {
            "pdf_url": f"{self.storage_base_url}/manga-files/{manga_id}.pdf?signed=true",
            "webp_urls": [
                self.get_image_url(f"{manga_id}_page_{i}.webp")
                for i in range(1, 21)
            ],
            "thumbnail_url": self.get_thumbnail_url(f"{manga_id}_thumb.webp")
        }
    
    def construct_preview_urls(self, request_id: str, phase_number: int) -> dict:
        """Construct preview URLs for specific phase."""
        return {
            "thumbnail": self.get_preview_url(f"{request_id}_phase_{phase_number}_thumb.webp"),
            "structure_diagram": self.get_preview_url(f"{request_id}_phase_{phase_number}_diagram.png")
        }
    
    def construct_feedback_urls(self, feedback_id: str) -> dict:
        """Construct URLs for feedback-related content."""
        return {
            "result_preview": self.get_preview_url(f"{feedback_id}_mood_preview.webp")
        }


# Global URL service instance
url_service = URLService()
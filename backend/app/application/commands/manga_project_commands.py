"""Manga project related commands for CQRS pattern."""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .base_command import Command, RequireUserMixin, RequireIdMixin, CommandValidationError


@dataclass(kw_only=True)
class CreateMangaProjectCommand(Command[str], RequireUserMixin):
    """Command to create a new manga project."""
    
    title: str
    metadata: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    visibility: str = "private"  # private, public, unlisted
    expires_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate create manga project command."""
        self.validate_user_required()
        
        if not self.title or not self.title.strip():
            raise CommandValidationError("Title is required")
        
        if len(self.title) > 255:
            raise CommandValidationError("Title must be 255 characters or less")
        
        if self.visibility not in ["private", "public", "unlisted"]:
            raise CommandValidationError("Visibility must be 'private', 'public', or 'unlisted'")
        
        if self.expires_at is not None and self.expires_at <= datetime.utcnow():
            raise CommandValidationError("Expiration date must be in the future")


@dataclass(kw_only=True)
class UpdateMangaProjectCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to update manga project information."""
    
    project_id: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    visibility: Optional[str] = None
    total_pages: Optional[int] = None
    
    def validate(self) -> None:
        """Validate update manga project command."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if self.title is not None:
            if not self.title.strip():
                raise CommandValidationError("Title cannot be empty")
            if len(self.title) > 255:
                raise CommandValidationError("Title must be 255 characters or less")
        
        if self.visibility is not None:
            if self.visibility not in ["private", "public", "unlisted"]:
                raise CommandValidationError("Visibility must be 'private', 'public', or 'unlisted'")
        
        if self.total_pages is not None:
            if self.total_pages < 0:
                raise CommandValidationError("Total pages cannot be negative")


@dataclass(kw_only=True)
class DeleteMangaProjectCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to delete a manga project."""
    
    project_id: str
    reason: Optional[str] = None
    
    def validate(self) -> None:
        """Validate delete manga project command."""
        self.validate_user_required()
        self.validate_id_required("project_id")


@dataclass(kw_only=True)
class ArchiveMangaProjectCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to archive a manga project."""
    
    project_id: str
    reason: Optional[str] = None
    
    def validate(self) -> None:
        """Validate archive manga project command."""
        self.validate_user_required()
        self.validate_id_required("project_id")


@dataclass(kw_only=True)
class PublishMangaProjectCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to publish a manga project."""
    
    project_id: str
    visibility: str = "public"  # public, unlisted
    publish_settings: Optional[Dict[str, Any]] = None
    
    def validate(self) -> None:
        """Validate publish manga project command."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if self.visibility not in ["public", "unlisted"]:
            raise CommandValidationError("Publish visibility must be 'public' or 'unlisted'")


@dataclass(kw_only=True)
class UpdateMangaProjectStatusCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to update manga project status."""
    
    project_id: str
    status: str  # completed, processing, failed
    error_message: Optional[str] = None
    
    def validate(self) -> None:
        """Validate update status command."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if self.status not in ["completed", "processing", "error"]:
            raise CommandValidationError("Status must be 'completed', 'processing', or 'failed'")
        
        if self.status == "error" and not self.error_message:
            raise CommandValidationError("Error message is required when status is 'failed'")


@dataclass(kw_only=True)
class AddMangaFileCommand(Command[str], RequireUserMixin, RequireIdMixin):
    """Command to add a file to manga project."""
    
    project_id: str
    file_type: str  # pdf, webp, thumbnail
    file_path: str
    file_size: int
    mime_type: str
    page_number: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def validate(self) -> None:
        """Validate add manga file command."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if self.file_type not in ["pdf", "webp", "thumbnail"]:
            raise CommandValidationError("File type must be 'pdf', 'webp', or 'thumbnail'")
        
        if not self.file_path or not self.file_path.strip():
            raise CommandValidationError("File path is required")
        
        if len(self.file_path) > 500:
            raise CommandValidationError("File path must be 500 characters or less")
        
        if self.file_size < 0:
            raise CommandValidationError("File size cannot be negative")
        
        if not self.mime_type or not self.mime_type.strip():
            raise CommandValidationError("MIME type is required")
        
        if self.page_number is not None and self.page_number < 1:
            raise CommandValidationError("Page number must be positive")


@dataclass(kw_only=True)
class RemoveMangaFileCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to remove a file from manga project."""
    
    project_id: str
    file_id: str
    reason: Optional[str] = None
    
    def validate(self) -> None:
        """Validate remove manga file command."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        self.validate_id_required("file_id")


@dataclass(kw_only=True)
class AddProjectTagCommand(Command[str], RequireUserMixin, RequireIdMixin):
    """Command to add a tag to manga project."""
    
    project_id: str
    tag_name: str
    tag_type: str = "user"  # user, system, genre
    
    def validate(self) -> None:
        """Validate add project tag command."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if not self.tag_name or not self.tag_name.strip():
            raise CommandValidationError("Tag name is required")
        
        if len(self.tag_name) > 50:
            raise CommandValidationError("Tag name must be 50 characters or less")
        
        if self.tag_type not in ["user", "system", "genre"]:
            raise CommandValidationError("Tag type must be 'user', 'system', or 'genre'")


@dataclass(kw_only=True)
class RemoveProjectTagCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to remove a tag from manga project."""
    
    project_id: str
    tag_id: str
    
    def validate(self) -> None:
        """Validate remove project tag command."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        self.validate_id_required("tag_id")

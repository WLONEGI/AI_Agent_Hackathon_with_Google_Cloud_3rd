"""Manga project related queries for CQRS pattern."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .base_query import Query, RequireUserMixin, RequireIdMixin, QueryValidationError
from ..dto.manga_project_dto import MangaProjectDTO, MangaProjectStatsDTO, MangaProjectSummaryDTO


@dataclass(kw_only=True)
class GetMangaProjectQuery(Query[MangaProjectDTO], RequireUserMixin, RequireIdMixin):
    """Query to get a single manga project by ID."""
    
    project_id: str
    include_files: bool = False
    include_tags: bool = False
    include_stats: bool = False
    
    def validate(self) -> None:
        """Validate get manga project query."""
        self.validate_user_required()
        self.validate_id_required("project_id")


@dataclass(kw_only=True)
class ListMangaProjectsQuery(Query[List[MangaProjectDTO]], RequireUserMixin):
    """Query to list manga projects with filtering."""
    
    owner_user_id: Optional[str] = None  # If None, shows requesting user's projects
    status: Optional[str] = None  # completed, processing, failed
    visibility: Optional[str] = None  # private, public, unlisted
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    expires_before: Optional[datetime] = None
    include_expired: bool = False
    
    def validate(self) -> None:
        """Validate list manga projects query."""
        self.validate_user_required()
        
        if self.status is not None:
            if self.status not in ["completed", "processing", "error"]:
                raise QueryValidationError("Status must be 'completed', 'processing', or 'failed'")
        
        if self.visibility is not None:
            if self.visibility not in ["private", "public", "unlisted"]:
                raise QueryValidationError("Visibility must be 'private', 'public', or 'unlisted'")
        
        if self.created_after and self.created_before:
            if self.created_after >= self.created_before:
                raise QueryValidationError("Created after date must be before created before date")


@dataclass(kw_only=True)
class SearchMangaProjectsQuery(Query[List[MangaProjectDTO]], RequireUserMixin):
    """Query to search manga projects by various criteria."""
    
    search_term: str
    search_fields: List[str] = None  # title, metadata
    status: Optional[str] = None
    visibility: Optional[str] = None
    owner_user_id: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        """Set default search fields."""
        if self.search_fields is None:
            self.search_fields = ["title"]
    
    def validate(self) -> None:
        """Validate search manga projects query."""
        self.validate_user_required()
        
        if not self.search_term or not self.search_term.strip():
            raise QueryValidationError("Search term is required")
        
        if len(self.search_term) < 2:
            raise QueryValidationError("Search term must be at least 2 characters")
        
        valid_fields = ["title", "metadata"]
        for field in self.search_fields:
            if field not in valid_fields:
                raise QueryValidationError(f"Invalid search field: {field}")
        
        if self.status is not None:
            if self.status not in ["completed", "processing", "error"]:
                raise QueryValidationError("Status must be 'completed', 'processing', or 'failed'")
        
        if self.visibility is not None:
            if self.visibility not in ["private", "public", "unlisted"]:
                raise QueryValidationError("Visibility must be 'private', 'public', or 'unlisted'")


@dataclass(kw_only=True)
class GetMangaProjectsByUserQuery(Query[List[MangaProjectDTO]], RequireUserMixin, RequireIdMixin):
    """Query to get manga projects for a specific user."""
    
    owner_user_id: str
    status: Optional[str] = None
    visibility: Optional[str] = None
    include_expired: bool = False
    include_files: bool = False
    include_stats: bool = False
    
    def validate(self) -> None:
        """Validate get projects by user query."""
        self.validate_user_required()
        self.validate_id_required("owner_user_id")
        
        if self.status is not None:
            if self.status not in ["completed", "processing", "error"]:
                raise QueryValidationError("Status must be 'completed', 'processing', or 'failed'")
        
        if self.visibility is not None:
            if self.visibility not in ["private", "public", "unlisted"]:
                raise QueryValidationError("Visibility must be 'private', 'public', or 'unlisted'")


@dataclass(kw_only=True)
class GetMangaProjectStatsQuery(Query[MangaProjectStatsDTO], RequireUserMixin):
    """Query to get manga project statistics."""
    
    user_id: Optional[str] = None  # If None, gets overall stats (admin only)
    period_days: int = 30
    include_file_stats: bool = True
    include_generation_stats: bool = True
    
    def validate(self) -> None:
        """Validate get project stats query."""
        self.validate_user_required()
        
        if self.period_days < 1:
            raise QueryValidationError("Period days must be at least 1")
        
        if self.period_days > 365:
            raise QueryValidationError("Period days cannot exceed 365")


@dataclass(kw_only=True)
class GetMangaProjectFilesQuery(Query[List[dict]], RequireUserMixin, RequireIdMixin):
    """Query to get files for a manga project."""
    
    project_id: str
    file_type: Optional[str] = None  # pdf, webp, thumbnail
    page_number: Optional[int] = None
    
    def validate(self) -> None:
        """Validate get project files query."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if self.file_type is not None:
            if self.file_type not in ["pdf", "webp", "thumbnail"]:
                raise QueryValidationError("File type must be 'pdf', 'webp', or 'thumbnail'")
        
        if self.page_number is not None and self.page_number < 1:
            raise QueryValidationError("Page number must be positive")


@dataclass(kw_only=True)
class GetMangaProjectTagsQuery(Query[List[dict]], RequireUserMixin, RequireIdMixin):
    """Query to get tags for a manga project."""
    
    project_id: str
    tag_type: Optional[str] = None  # user, system, genre
    
    def validate(self) -> None:
        """Validate get project tags query."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if self.tag_type is not None:
            if self.tag_type not in ["user", "system", "genre"]:
                raise QueryValidationError("Tag type must be 'user', 'system', or 'genre'")


@dataclass(kw_only=True)
class GetPublicMangaProjectsQuery(Query[List[MangaProjectSummaryDTO]]):
    """Query to get public manga projects for browsing."""
    
    status: str = "completed"
    featured_only: bool = False
    created_after: Optional[datetime] = None
    tags: Optional[List[str]] = None
    
    def validate(self) -> None:
        """Validate get public projects query."""
        if self.status not in ["completed", "processing"]:
            raise QueryValidationError("Status must be 'completed' or 'processing'")


@dataclass(kw_only=True)
class GetTrendingMangaProjectsQuery(Query[List[MangaProjectSummaryDTO]]):
    """Query to get trending manga projects."""
    
    period_days: int = 7
    min_interactions: int = 1
    
    def validate(self) -> None:
        """Validate get trending projects query."""
        if self.period_days < 1:
            raise QueryValidationError("Period days must be at least 1")
        
        if self.period_days > 30:
            raise QueryValidationError("Period days cannot exceed 30")
        
        if self.min_interactions < 1:
            raise QueryValidationError("Minimum interactions must be at least 1")


@dataclass(kw_only=True)
class GetMangaProjectHistoryQuery(Query[List[dict]], RequireUserMixin, RequireIdMixin):
    """Query to get manga project history/audit trail."""
    
    project_id: str
    action_types: Optional[List[str]] = None  # create, update, delete, publish, etc.
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate get project history query."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if self.from_date and self.to_date:
            if self.from_date >= self.to_date:
                raise QueryValidationError("From date must be before to date")
        
        if self.action_types:
            valid_types = [
                "create", "update", "delete", "publish", "archive",
                "file_add", "file_remove", "tag_add", "tag_remove"
            ]
            for action_type in self.action_types:
                if action_type not in valid_types:
                    raise QueryValidationError(f"Invalid action type: {action_type}")


@dataclass(kw_only=True)
class GetExpiredMangaProjectsQuery(Query[List[MangaProjectDTO]], RequireUserMixin):
    """Query to get expired manga projects (admin only)."""
    
    expired_before: Optional[datetime] = None
    user_id: Optional[str] = None
    grace_period_hours: int = 24
    
    def validate(self) -> None:
        """Validate get expired projects query."""
        self.validate_user_required()
        
        if self.grace_period_hours < 0:
            raise QueryValidationError("Grace period hours cannot be negative")
        
        if self.grace_period_hours > 168:  # 7 days
            raise QueryValidationError("Grace period hours cannot exceed 168 (7 days)")


@dataclass(kw_only=True)
class GetMangaProjectAnalyticsQuery(Query[dict], RequireUserMixin, RequireIdMixin):
    """Query to get analytics for a manga project."""
    
    project_id: str
    metric_types: Optional[List[str]] = None
    period_days: int = 30
    
    def validate(self) -> None:
        """Validate get project analytics query."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if self.period_days < 1:
            raise QueryValidationError("Period days must be at least 1")
        
        if self.period_days > 365:
            raise QueryValidationError("Period days cannot exceed 365")
        
        if self.metric_types:
            valid_types = [
                "views", "downloads", "shares", "ratings",
                "generation_time", "file_size", "quality_score"
            ]
            for metric_type in self.metric_types:
                if metric_type not in valid_types:
                    raise QueryValidationError(f"Invalid metric type: {metric_type}")


@dataclass(kw_only=True)
class ValidateProjectAccessQuery(Query[bool], RequireUserMixin, RequireIdMixin):
    """Query to validate user access to a manga project."""
    
    project_id: str
    access_type: str  # read, write, delete, publish
    
    def validate(self) -> None:
        """Validate project access query."""
        self.validate_user_required()
        self.validate_id_required("project_id")
        
        if self.access_type not in ["read", "write", "delete", "publish"]:
            raise QueryValidationError("Access type must be 'read', 'write', 'delete', or 'publish'")
"""Manga project related DTOs for data transfer."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from .base_dto import BaseDTO, StatsDTO, validate_required_fields, validate_field_length


@dataclass
class MangaProjectDTO(BaseDTO):
    """DTO for manga project data transfer."""
    
    project_id: str
    user_id: str
    title: str
    status: str  # completed, processing, failed
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    total_pages: Optional[int] = None
    visibility: str = "private"
    expires_at: Optional[datetime] = None
    
    # Related data (populated when requested)
    files: Optional[List['MangaFileDTO']] = None
    tags: Optional[List['ProjectTagDTO']] = None
    generation_requests: Optional[List['GenerationRequestSummaryDTO']] = None
    stats: Optional['MangaProjectStatsDTO'] = None
    
    def validate(self) -> None:
        """Validate manga project DTO."""
        validate_required_fields(self, ['project_id', 'user_id', 'title', 'status'])
        validate_field_length(self, {'title': (1, 255)})
        
        if self.status not in ["completed", "processing", "error"]:
            raise ValueError("Status must be 'completed', 'processing', or 'failed'")
        
        if self.visibility not in ["private", "public", "unlisted"]:
            raise ValueError("Visibility must be 'private', 'public', or 'unlisted'")
        
        if self.total_pages is not None and self.total_pages < 0:
            raise ValueError("Total pages cannot be negative")


@dataclass
class MangaProjectCreateDTO(BaseDTO):
    """DTO for creating a new manga project."""
    
    title: str
    metadata: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    visibility: str = "private"
    expires_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate manga project create DTO."""
        validate_required_fields(self, ['title'])
        validate_field_length(self, {'title': (1, 255)})
        
        if self.visibility not in ["private", "public", "unlisted"]:
            raise ValueError("Visibility must be 'private', 'public', or 'unlisted'")
        
        if self.expires_at is not None and self.expires_at <= datetime.utcnow():
            raise ValueError("Expiration date must be in the future")


@dataclass
class MangaProjectUpdateDTO(BaseDTO):
    """DTO for updating manga project information."""
    
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    visibility: Optional[str] = None
    total_pages: Optional[int] = None
    status: Optional[str] = None
    
    def validate(self) -> None:
        """Validate manga project update DTO."""
        if self.title is not None:
            validate_field_length(self, {'title': (1, 255)})
        
        if self.visibility is not None:
            if self.visibility not in ["private", "public", "unlisted"]:
                raise ValueError("Visibility must be 'private', 'public', or 'unlisted'")
        
        if self.total_pages is not None and self.total_pages < 0:
            raise ValueError("Total pages cannot be negative")
        
        if self.status is not None:
            if self.status not in ["completed", "processing", "error"]:
                raise ValueError("Status must be 'completed', 'processing', or 'failed'")


@dataclass
class MangaProjectStatsDTO(StatsDTO):
    """DTO for manga project statistics."""
    
    total_projects: int = 0
    completed_projects: int = 0
    processing_projects: int = 0
    failed_projects: int = 0
    
    # File statistics
    total_files: int = 0
    total_file_size_bytes: int = 0
    pdf_files: int = 0
    webp_files: int = 0
    thumbnail_files: int = 0
    
    # Generation statistics
    total_generation_requests: int = 0
    successful_generations: int = 0
    average_generation_time_seconds: float = 0.0
    average_quality_score: float = 0.0
    
    # Usage patterns
    most_common_settings: Optional[Dict[str, Any]] = None
    most_active_users: Optional[List[Dict[str, Any]]] = None
    peak_usage_hours: Optional[List[int]] = None
    
    # Trends (compared to previous period)
    projects_trend_percentage: float = 0.0
    completion_rate_trend: float = 0.0
    
    def calculate_derived_stats(self) -> None:
        """Calculate derived statistics."""
        # Completion rate
        if self.total_projects > 0:
            self.completion_rate = self.completed_projects / self.total_projects * 100
        
        # Generation success rate
        if self.total_generation_requests > 0:
            self.generation_success_rate = (
                self.successful_generations / self.total_generation_requests * 100
            )


@dataclass
class MangaProjectSummaryDTO(BaseDTO):
    """DTO for manga project summary (minimal data for lists)."""
    
    project_id: str
    title: str
    status: str
    visibility: str
    created_at: datetime
    updated_at: datetime
    total_pages: Optional[int] = None
    
    # Thumbnail/preview info
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None
    
    # Owner info
    owner_display_name: Optional[str] = None
    
    def validate(self) -> None:
        """Validate manga project summary DTO."""
        validate_required_fields(self, ['project_id', 'title', 'status', 'visibility'])


@dataclass
class MangaFileDTO(BaseDTO):
    """DTO for manga file information."""
    
    file_id: str
    project_id: str
    file_type: str  # pdf, webp, thumbnail
    file_path: str
    file_size: int
    mime_type: str
    created_at: datetime
    page_number: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Derived fields
    file_url: Optional[str] = None
    download_url: Optional[str] = None
    
    def validate(self) -> None:
        """Validate manga file DTO."""
        validate_required_fields(self, [
            'file_id', 'project_id', 'file_type', 'file_path', 
            'file_size', 'mime_type'
        ])
        
        if self.file_type not in ["pdf", "webp", "thumbnail"]:
            raise ValueError("File type must be 'pdf', 'webp', or 'thumbnail'")
        
        if self.file_size < 0:
            raise ValueError("File size cannot be negative")
        
        if self.page_number is not None and self.page_number < 1:
            raise ValueError("Page number must be positive")


@dataclass
class ProjectTagDTO(BaseDTO):
    """DTO for project tag information."""
    
    tag_id: str
    project_id: str
    tag_name: str
    created_at: datetime
    tag_type: str = "user"  # user, system, genre
    
    def validate(self) -> None:
        """Validate project tag DTO."""
        validate_required_fields(self, ['tag_id', 'project_id', 'tag_name'])
        validate_field_length(self, {'tag_name': (1, 50)})
        
        if self.tag_type not in ["user", "system", "genre"]:
            raise ValueError("Tag type must be 'user', 'system', or 'genre'")


@dataclass
class MangaProjectAnalyticsDTO(BaseDTO):
    """DTO for manga project analytics."""
    
    project_id: str
    period_start: datetime
    period_end: datetime
    
    # View metrics
    total_views: int = 0
    unique_viewers: int = 0
    average_view_duration_seconds: float = 0.0
    
    # Download metrics
    total_downloads: int = 0
    unique_downloaders: int = 0
    
    # Engagement metrics
    total_shares: int = 0
    total_ratings: int = 0
    average_rating: float = 0.0
    
    # Performance metrics
    page_load_time_ms: float = 0.0
    bounce_rate_percentage: float = 0.0
    
    # Geographic data
    top_countries: List[Dict[str, Any]] = field(default_factory=list)
    
    # Traffic sources
    traffic_sources: Dict[str, int] = field(default_factory=dict)
    
    def validate(self) -> None:
        """Validate project analytics DTO."""
        validate_required_fields(self, ['project_id', 'period_start', 'period_end'])
        
        if self.period_start >= self.period_end:
            raise ValueError("Period start must be before period end")
        
        if self.average_rating < 0 or self.average_rating > 5:
            raise ValueError("Average rating must be between 0 and 5")


@dataclass
class GenerationRequestSummaryDTO(BaseDTO):
    """DTO for generation request summary (used in project details)."""
    
    request_id: str
    status: str
    priority: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    current_module: int = 0
    progress_percentage: float = 0.0
    
    def validate(self) -> None:
        """Validate generation request summary DTO."""
        validate_required_fields(self, ['request_id', 'status', 'priority'])
        
        valid_statuses = ["queued", "processing", "completed", "error"]
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        if self.priority not in ["normal", "high"]:
            raise ValueError("Priority must be 'normal' or 'high'")
        
        if not (0.0 <= self.progress_percentage <= 100.0):
            raise ValueError("Progress percentage must be between 0.0 and 100.0")


@dataclass
class ProjectHistoryEntryDTO(BaseDTO):
    """DTO for project history/audit entries."""
    
    entry_id: str
    project_id: str
    user_id: str
    action_type: str
    action_data: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str] = None
    
    def validate(self) -> None:
        """Validate project history entry DTO."""
        validate_required_fields(self, [
            'entry_id', 'project_id', 'user_id', 
            'action_type', 'action_data'
        ])
        
        valid_actions = [
            "create", "update", "delete", "publish", "archive",
            "file_add", "file_remove", "tag_add", "tag_remove"
        ]
        
        if self.action_type not in valid_actions:
            raise ValueError(f"Action type must be one of: {', '.join(valid_actions)}")


@dataclass
class ProjectValidationDTO(BaseDTO):
    """DTO for project validation results."""
    
    project_id: str
    is_valid: bool
    can_read: bool = False
    can_write: bool = False
    can_delete: bool = False
    can_publish: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate project validation DTO."""
        validate_required_fields(self, ['project_id', 'is_valid'])
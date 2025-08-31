"""Common domain entities."""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4


@dataclass
class DomainEntity(ABC):
    """Base class for all domain entities.
    
    Contains common functionality for all domain entities including
    identity management and basic validation.
    """
    
    def __post_init__(self):
        """Post-initialization validation."""
        self.validate()
    
    def validate(self) -> None:
        """Validate entity state.
        
        Should be implemented by subclasses to validate business rules.
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, UUID):
                result[key] = str(value)
            elif isinstance(value, DomainEntity):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [
                    item.to_dict() if isinstance(item, DomainEntity) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result


@dataclass
class UserEntity(DomainEntity):
    """Domain entity representing a user.
    
    Contains all user-related business logic and validation rules.
    """
    
    user_id: UUID = field(default_factory=uuid4)
    email: str = ""
    display_name: str = ""
    account_type: str = "free"
    firebase_claims: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Optional fields for extended functionality
    is_active: bool = True
    is_verified: bool = False
    last_login_at: Optional[datetime] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    # Business rule properties
    @property
    def is_premium(self) -> bool:
        """Check if user has premium account."""
        return self.account_type in ["premium", "admin"]
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.account_type == "admin"
    
    @property
    def can_create_unlimited_projects(self) -> bool:
        """Check if user can create unlimited projects."""
        return self.is_premium
    
    @property
    def max_concurrent_generations(self) -> int:
        """Get maximum concurrent generations allowed."""
        return {
            "free": 1,
            "premium": 3,
            "admin": 10
        }.get(self.account_type, 1)
    
    @property
    def daily_generation_limit(self) -> int:
        """Get daily generation limit."""
        return {
            "free": 10,
            "premium": 100,
            "admin": 1000
        }.get(self.account_type, 10)
    
    def validate(self) -> None:
        """Validate user entity business rules."""
        if not self.email or not self.email.strip():
            raise ValueError("Email is required")
        
        if "@" not in self.email:
            raise ValueError("Invalid email format")
        
        if not self.display_name or not self.display_name.strip():
            raise ValueError("Display name is required")
        
        if len(self.display_name) > 100:
            raise ValueError("Display name too long (max 100 characters)")
        
        if self.account_type not in ["free", "premium", "admin"]:
            raise ValueError("Invalid account type")
        
        if self.avatar_url and len(self.avatar_url) > 500:
            raise ValueError("Avatar URL too long (max 500 characters)")
        
        if self.bio and len(self.bio) > 1000:
            raise ValueError("Bio too long (max 1000 characters)")
    
    def update_display_name(self, new_name: str) -> None:
        """Update user's display name with validation."""
        if not new_name or not new_name.strip():
            raise ValueError("Display name cannot be empty")
        
        if len(new_name) > 100:
            raise ValueError("Display name too long")
        
        self.display_name = new_name.strip()
        self.updated_at = datetime.utcnow()
    
    def upgrade_to_premium(self) -> None:
        """Upgrade user to premium account."""
        if self.account_type == "free":
            self.account_type = "premium"
            self.updated_at = datetime.utcnow()
    
    def downgrade_to_free(self) -> None:
        """Downgrade user to free account."""
        if self.account_type == "premium":
            self.account_type = "free"
            self.updated_at = datetime.utcnow()
    
    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def verify_email(self) -> None:
        """Mark user email as verified."""
        self.is_verified = True
        self.updated_at = datetime.utcnow()


@dataclass
class MangaProjectEntity(DomainEntity):
    """Domain entity representing a manga project."""
    
    project_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    title: str = ""
    status: str = "draft"
    metadata: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    total_pages: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    @property
    def is_active(self) -> bool:
        """Check if project is in active status."""
        return self.status in ["draft", "processing"]
    
    @property
    def is_completed(self) -> bool:
        """Check if project is completed."""
        return self.status == "completed"
    
    @property
    def is_expired(self) -> bool:
        """Check if project has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def validate(self) -> None:
        """Validate project entity."""
        if not self.title or not self.title.strip():
            raise ValueError("Project title is required")
        
        if len(self.title) > 255:
            raise ValueError("Project title too long")
        
        valid_statuses = ["draft", "processing", "completed", "failed", "archived"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}")
        
        if self.total_pages is not None and self.total_pages <= 0:
            raise ValueError("Total pages must be positive")
    
    def update_status(self, new_status: str) -> None:
        """Update project status with validation."""
        valid_statuses = ["draft", "processing", "completed", "failed", "archived"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")
        
        self.status = new_status
        self.updated_at = datetime.utcnow()
    
    def update_title(self, new_title: str) -> None:
        """Update project title with validation."""
        if not new_title or not new_title.strip():
            raise ValueError("Title cannot be empty")
        
        if len(new_title) > 255:
            raise ValueError("Title too long")
        
        self.title = new_title.strip()
        self.updated_at = datetime.utcnow()


@dataclass
class GenerationRequestEntity(DomainEntity):
    """Domain entity representing a generation request."""
    
    request_id: UUID = field(default_factory=uuid4)
    project_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    input_text: str = ""
    request_settings: Dict[str, Any] = field(default_factory=dict)
    status: str = "queued"
    current_module: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_processing(self) -> bool:
        """Check if request is currently processing."""
        return self.status == "processing"
    
    @property
    def is_completed(self) -> bool:
        """Check if request is completed."""
        return self.status == "completed"
    
    @property
    def is_failed(self) -> bool:
        """Check if request has failed."""
        return self.status == "failed"
    
    @property
    def can_retry(self) -> bool:
        """Check if request can be retried."""
        return self.is_failed and self.retry_count < 3
    
    def validate(self) -> None:
        """Validate generation request entity."""
        if not self.input_text or not self.input_text.strip():
            raise ValueError("Input text is required")
        
        valid_statuses = ["queued", "processing", "completed", "failed", "cancelled"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}")
        
        if not (0 <= self.current_module <= 7):
            raise ValueError("Current module must be between 0 and 7")
        
        if self.retry_count < 0:
            raise ValueError("Retry count cannot be negative")
    
    def start_processing(self) -> None:
        """Mark request as started processing."""
        self.status = "processing"
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_processing(self) -> None:
        """Mark request as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def fail_processing(self, error_message: str = None) -> None:
        """Mark request as failed."""
        self.status = "failed"
        self.updated_at = datetime.utcnow()
    
    def retry_processing(self) -> None:
        """Retry failed processing."""
        if not self.can_retry:
            raise ValueError("Cannot retry this request")
        
        self.status = "queued"
        self.retry_count += 1
        self.current_module = 0
        self.started_at = None
        self.completed_at = None
        self.updated_at = datetime.utcnow()


@dataclass  
class ProcessingModuleEntity(DomainEntity):
    """Domain entity representing a processing module."""
    
    module_id: UUID = field(default_factory=uuid4)
    module_name: str = ""
    module_type: str = ""
    version: str = "1.0.0"
    is_enabled: bool = True
    configuration: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_active(self) -> bool:
        """Check if module is active and enabled."""
        return self.is_enabled
    
    def validate(self) -> None:
        """Validate processing module entity."""
        if not self.module_name or not self.module_name.strip():
            raise ValueError("Module name is required")
        
        if not self.module_type or not self.module_type.strip():
            raise ValueError("Module type is required")
        
        valid_types = [
            "text_analysis", "character_extraction", "panel_generation", 
            "speech_bubble", "background_generation", "style_transfer",
            "quality_control", "output_formatting"
        ]
        if self.module_type not in valid_types:
            raise ValueError(f"Invalid module type: {self.module_type}")
    
    def enable(self) -> None:
        """Enable the module."""
        self.is_enabled = True
        self.updated_at = datetime.utcnow()
    
    def disable(self) -> None:
        """Disable the module."""
        self.is_enabled = False
        self.updated_at = datetime.utcnow()
    
    def update_configuration(self, new_config: Dict[str, Any]) -> None:
        """Update module configuration."""
        self.configuration.update(new_config)
        self.updated_at = datetime.utcnow()
"""User-related DTOs for data transfer."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from .base_dto import BaseDTO, StatsDTO, validate_required_fields, validate_field_length


@dataclass
class UserDTO(BaseDTO):
    """DTO for user data transfer."""
    
    user_id: str
    email: str
    display_name: str
    account_type: str
    firebase_claims: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    # Optional fields
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    last_login_at: Optional[datetime] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    # Statistics (populated when requested)
    stats: Optional['UserStatsDTO'] = None
    preferences: Optional['UserPreferencesDTO'] = None
    
    def validate(self) -> None:
        """Validate user DTO."""
        validate_required_fields(self, ['user_id', 'email', 'display_name', 'account_type'])
        validate_field_length(self, {
            'email': (5, 255),
            'display_name': (1, 100)
        })
        
        if self.account_type not in ["free", "premium", "admin"]:
            raise ValueError("Account type must be 'free', 'premium', or 'admin'")
        
        if "@" not in self.email:
            raise ValueError("Invalid email format")


@dataclass
class UserCreateDTO(BaseDTO):
    """DTO for creating a new user."""
    
    email: str
    display_name: str
    account_type: str = "free"
    firebase_claims: Optional[Dict[str, Any]] = None
    
    def validate(self) -> None:
        """Validate user create DTO."""
        validate_required_fields(self, ['email', 'display_name'])
        validate_field_length(self, {
            'email': (5, 255),
            'display_name': (1, 100)
        })
        
        if self.account_type not in ["free", "premium", "admin"]:
            raise ValueError("Account type must be 'free', 'premium', or 'admin'")
        
        if "@" not in self.email:
            raise ValueError("Invalid email format")


@dataclass
class UserUpdateDTO(BaseDTO):
    """DTO for updating user information."""
    
    display_name: Optional[str] = None
    account_type: Optional[str] = None
    firebase_claims: Optional[Dict[str, Any]] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    def validate(self) -> None:
        """Validate user update DTO."""
        if self.display_name is not None:
            validate_field_length(self, {'display_name': (1, 100)})
        
        if self.account_type is not None:
            if self.account_type not in ["free", "premium", "admin"]:
                raise ValueError("Account type must be 'free', 'premium', or 'admin'")
        
        if self.avatar_url is not None:
            validate_field_length(self, {'avatar_url': (10, 500)})
        
        if self.bio is not None:
            validate_field_length(self, {'bio': (0, 1000)})


@dataclass
class UserStatsDTO(StatsDTO):
    """DTO for user statistics."""
    
    total_projects: int = 0
    completed_projects: int = 0
    failed_projects: int = 0
    total_generations: int = 0
    successful_generations: int = 0
    total_processing_time_seconds: float = 0.0
    average_processing_time_seconds: float = 0.0
    success_rate: float = 0.0
    
    # Quota and usage stats
    daily_quota_used: int = 0
    daily_quota_limit: int = 0
    monthly_quota_used: int = 0
    monthly_quota_limit: int = 0
    
    # Quality metrics
    average_quality_score: float = 0.0
    total_feedback_sessions: int = 0
    average_feedback_per_generation: float = 0.0
    
    # Recent activity
    last_generation_at: Optional[datetime] = None
    last_project_created_at: Optional[datetime] = None
    
    # Storage usage
    total_storage_used_bytes: int = 0
    total_files_created: int = 0
    
    def calculate_derived_stats(self) -> None:
        """Calculate derived statistics."""
        # Success rate
        if self.total_generations > 0:
            self.success_rate = self.successful_generations / self.total_generations
        
        # Average processing time
        if self.successful_generations > 0:
            self.average_processing_time_seconds = (
                self.total_processing_time_seconds / self.successful_generations
            )
        
        # Average feedback per generation
        if self.total_generations > 0:
            self.average_feedback_per_generation = (
                self.total_feedback_sessions / self.total_generations
            )


@dataclass
class UserPreferencesDTO(BaseDTO):
    """DTO for user preferences."""
    
    user_id: str
    device_capability: float = 0.5  # 0.0 to 1.0
    network_speed: int = 5000  # Kbps
    preferred_quality: int = 3  # 1 to 5
    auto_adapt: bool = True
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    # UI preferences
    theme: str = "auto"  # light, dark, auto
    language: str = "ja"  # ja, en
    notifications_enabled: bool = True
    email_notifications: bool = True
    
    # Generation preferences
    auto_start_generation: bool = False
    feedback_timeout_minutes: int = 30
    save_intermediate_results: bool = True
    
    def validate(self) -> None:
        """Validate user preferences DTO."""
        validate_required_fields(self, ['user_id'])
        
        if not (0.0 <= self.device_capability <= 1.0):
            raise ValueError("Device capability must be between 0.0 and 1.0")
        
        if not (1 <= self.preferred_quality <= 5):
            raise ValueError("Preferred quality must be between 1 and 5")
        
        if self.network_speed < 0:
            raise ValueError("Network speed cannot be negative")
        
        if self.theme not in ["light", "dark", "auto"]:
            raise ValueError("Theme must be 'light', 'dark', or 'auto'")
        
        if self.language not in ["ja", "en"]:
            raise ValueError("Language must be 'ja' or 'en'")
        
        if not (1 <= self.feedback_timeout_minutes <= 120):
            raise ValueError("Feedback timeout must be between 1 and 120 minutes")


@dataclass
class UserQuotaDTO(BaseDTO):
    """DTO for user quota information."""
    
    user_id: str
    quota_type: str  # daily, monthly
    limit_value: int
    used_value: int = 0
    reset_at: datetime
    created_at: datetime
    updated_at: datetime
    
    # Calculated fields
    remaining_value: int = field(init=False)
    usage_percentage: float = field(init=False)
    is_exceeded: bool = field(init=False)
    
    def __post_init__(self):
        """Calculate derived fields."""
        self.remaining_value = max(0, self.limit_value - self.used_value)
        self.usage_percentage = (
            (self.used_value / self.limit_value * 100) if self.limit_value > 0 else 0.0
        )
        self.is_exceeded = self.used_value >= self.limit_value
    
    def validate(self) -> None:
        """Validate user quota DTO."""
        validate_required_fields(self, ['user_id', 'quota_type', 'limit_value', 'reset_at'])
        
        if self.quota_type not in ["daily", "monthly"]:
            raise ValueError("Quota type must be 'daily' or 'monthly'")
        
        if self.limit_value < 0:
            raise ValueError("Limit value cannot be negative")
        
        if self.used_value < 0:
            raise ValueError("Used value cannot be negative")


@dataclass
class UserActivityDTO(BaseDTO):
    """DTO for user activity records."""
    
    user_id: str
    activity_type: str
    activity_data: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def validate(self) -> None:
        """Validate user activity DTO."""
        validate_required_fields(self, ['user_id', 'activity_type', 'activity_data'])
        
        valid_types = [
            "login", "logout", "generation", "project_create",
            "project_update", "project_delete", "settings_update"
        ]
        
        if self.activity_type not in valid_types:
            raise ValueError(f"Activity type must be one of: {', '.join(valid_types)}")


@dataclass
class UserSummaryDTO(BaseDTO):
    """DTO for user summary information (minimal data)."""
    
    user_id: str
    display_name: str
    account_type: str
    created_at: datetime
    
    # Summary stats
    total_projects: int = 0
    total_generations: int = 0
    success_rate: float = 0.0
    
    def validate(self) -> None:
        """Validate user summary DTO."""
        validate_required_fields(self, ['user_id', 'display_name', 'account_type'])


@dataclass
class UserValidationDTO(BaseDTO):
    """DTO for user validation results."""
    
    user_id: str
    is_valid: bool
    permissions: List[str] = field(default_factory=list)
    restrictions: List[str] = field(default_factory=list)
    quota_status: Optional[UserQuotaDTO] = None
    
    def validate(self) -> None:
        """Validate user validation DTO."""
        validate_required_fields(self, ['user_id', 'is_valid'])
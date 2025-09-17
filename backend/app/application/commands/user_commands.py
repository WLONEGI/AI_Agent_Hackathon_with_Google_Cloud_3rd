"""User-related commands for CQRS pattern."""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from .base_command import Command, RequireUserMixin, RequireIdMixin, CommandValidationError


@dataclass(kw_only=True)
class CreateUserCommand(Command[str]):
    """Command to create a new user."""
    
    email: str
    display_name: str
    account_type: str = "free"  # free, premium, admin
    firebase_claims: Optional[Dict[str, Any]] = None
    
    def validate(self) -> None:
        """Validate create user command."""
        if not self.email or not self.email.strip():
            raise CommandValidationError("Email is required")
        
        if "@" not in self.email:
            raise CommandValidationError("Valid email address is required")
        
        if not self.display_name or not self.display_name.strip():
            raise CommandValidationError("Display name is required")
        
        if len(self.display_name) > 100:
            raise CommandValidationError("Display name must be 100 characters or less")
        
        if self.account_type not in ["free", "premium", "admin"]:
            raise CommandValidationError("Account type must be 'free', 'premium', or 'admin'")


@dataclass(kw_only=True)
class UpdateUserCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to update user information."""
    
    user_id: str
    display_name: Optional[str] = None
    account_type: Optional[str] = None
    firebase_claims: Optional[Dict[str, Any]] = None
    
    def validate(self) -> None:
        """Validate update user command."""
        self.validate_id_required("user_id")
        
        if self.display_name is not None:
            if not self.display_name.strip():
                raise CommandValidationError("Display name cannot be empty")
            if len(self.display_name) > 100:
                raise CommandValidationError("Display name must be 100 characters or less")
        
        if self.account_type is not None:
            if self.account_type not in ["free", "premium", "admin"]:
                raise CommandValidationError("Account type must be 'free', 'premium', or 'admin'")


@dataclass(kw_only=True)
class DeleteUserCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to delete a user."""
    
    user_id: str
    reason: Optional[str] = None
    
    def validate(self) -> None:
        """Validate delete user command."""
        self.validate_id_required("user_id")


@dataclass(kw_only=True)
class VerifyUserEmailCommand(Command[bool], RequireIdMixin):
    """Command to verify user email address."""
    
    user_id: str
    verification_code: str
    
    def validate(self) -> None:
        """Validate verify email command."""
        self.validate_id_required("user_id")
        
        if not self.verification_code or not self.verification_code.strip():
            raise CommandValidationError("Verification code is required")


@dataclass(kw_only=True)
class UpdateUserPreferencesCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to update user preferences."""
    
    user_id: str
    device_capability: Optional[float] = None
    network_speed: Optional[int] = None
    preferred_quality: Optional[int] = None
    auto_adapt: Optional[bool] = None
    
    def validate(self) -> None:
        """Validate update preferences command."""
        self.validate_id_required("user_id")
        
        if self.device_capability is not None:
            if not (0.0 <= self.device_capability <= 1.0):
                raise CommandValidationError("Device capability must be between 0.0 and 1.0")
        
        if self.network_speed is not None:
            if self.network_speed < 0:
                raise CommandValidationError("Network speed cannot be negative")
        
        if self.preferred_quality is not None:
            if not (1 <= self.preferred_quality <= 5):
                raise CommandValidationError("Preferred quality must be between 1 and 5")


@dataclass(kw_only=True)
class UpdateUserQuotaCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to update user quota."""
    
    user_id: str
    quota_type: str  # daily, monthly
    limit_value: int
    used_value: Optional[int] = None
    reset_at: Optional[datetime] = None
    
    def validate(self) -> None:
        """Validate update quota command."""
        self.validate_id_required("user_id")
        
        if self.quota_type not in ["daily", "monthly"]:
            raise CommandValidationError("Quota type must be 'daily' or 'monthly'")
        
        if self.limit_value < 0:
            raise CommandValidationError("Limit value cannot be negative")
        
        if self.used_value is not None and self.used_value < 0:
            raise CommandValidationError("Used value cannot be negative")


@dataclass(kw_only=True)
class ResetUserPasswordCommand(Command[bool], RequireIdMixin):
    """Command to reset user password."""
    
    user_id: str
    reset_token: str
    new_password: str
    
    def validate(self) -> None:
        """Validate reset password command."""
        self.validate_id_required("user_id")
        
        if not self.reset_token or not self.reset_token.strip():
            raise CommandValidationError("Reset token is required")
        
        if not self.new_password or len(self.new_password) < 8:
            raise CommandValidationError("New password must be at least 8 characters")


@dataclass(kw_only=True)
class DeactivateUserCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to deactivate a user account."""
    
    user_id: str
    reason: Optional[str] = None
    temporary: bool = False
    
    def validate(self) -> None:
        """Validate deactivate user command."""
        self.validate_id_required("user_id")


@dataclass(kw_only=True)
class ReactivateUserCommand(Command[bool], RequireUserMixin, RequireIdMixin):
    """Command to reactivate a user account."""
    
    user_id: str
    
    def validate(self) -> None:
        """Validate reactivate user command."""
        self.validate_id_required("user_id")

"""Command definitions for CQRS pattern."""

from .base_command import AbstractCommand, Command
from .user_commands import (
    CreateUserCommand,
    UpdateUserCommand,
    DeleteUserCommand,
    VerifyUserEmailCommand,
    UpdateUserPreferencesCommand
)
from .manga_project_commands import (
    CreateMangaProjectCommand,
    UpdateMangaProjectCommand,
    DeleteMangaProjectCommand,
    ArchiveMangaProjectCommand,
    PublishMangaProjectCommand
)
from .generation_request_commands import (
    CreateGenerationRequestCommand,
    UpdateGenerationRequestStatusCommand,
    RetryGenerationRequestCommand,
    CancelGenerationRequestCommand,
    ProcessFeedbackCommand
)
from .processing_module_commands import (
    StartProcessingModuleCommand,
    CompleteProcessingModuleCommand,
    FailProcessingModuleCommand,
    RetryProcessingModuleCommand
)

__all__ = [
    # Base
    "AbstractCommand",
    "Command",
    
    # User Commands
    "CreateUserCommand",
    "UpdateUserCommand", 
    "DeleteUserCommand",
    "VerifyUserEmailCommand",
    "UpdateUserPreferencesCommand",
    
    # Manga Project Commands
    "CreateMangaProjectCommand",
    "UpdateMangaProjectCommand",
    "DeleteMangaProjectCommand",
    "ArchiveMangaProjectCommand",
    "PublishMangaProjectCommand",
    
    # Generation Request Commands
    "CreateGenerationRequestCommand",
    "UpdateGenerationRequestStatusCommand",
    "RetryGenerationRequestCommand",
    "CancelGenerationRequestCommand",
    "ProcessFeedbackCommand",
    
    # Processing Module Commands
    "StartProcessingModuleCommand",
    "CompleteProcessingModuleCommand",
    "FailProcessingModuleCommand",
    "RetryProcessingModuleCommand",
]
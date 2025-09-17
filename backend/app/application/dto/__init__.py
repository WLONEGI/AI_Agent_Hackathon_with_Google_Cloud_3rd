"""Data Transfer Objects for application layer."""

from .base_dto import BaseDTO, PaginatedResponseDTO
from .user_dto import (
    UserDTO,
    UserCreateDTO,
    UserUpdateDTO,
    UserStatsDTO,
    UserPreferencesDTO
)
from .manga_project_dto import (
    MangaProjectDTO,
    MangaProjectCreateDTO,
    MangaProjectUpdateDTO,
    MangaProjectStatsDTO,
    MangaProjectSummaryDTO
)
from .generation_request_dto import (
    GenerationRequestDTO,
    GenerationRequestCreateDTO,
    GenerationRequestUpdateDTO,
    GenerationRequestStatsDTO,
    GenerationRequestProgressDTO
)
from .processing_module_dto import (
    ProcessingModuleDTO,
    ProcessingModuleCreateDTO,
    ProcessingModuleUpdateDTO,
    ProcessingModuleStatsDTO,
    ProcessingModuleResultDTO
)

from .preview_dto import (
    PreviewVersionCreateDTO,
    PreviewVersionUpdateDTO,
    PreviewInteractionCreateDTO,
    PreviewQualitySettingsCreateDTO,
    PreviewQualitySettingsUpdateDTO
)

__all__ = [
    # Base
    "BaseDTO",
    "PaginatedResponseDTO",
    
    # User DTOs
    "UserDTO",
    "UserCreateDTO",
    "UserUpdateDTO",
    "UserStatsDTO",
    "UserPreferencesDTO",
    
    # Manga Project DTOs
    "MangaProjectDTO",
    "MangaProjectCreateDTO",
    "MangaProjectUpdateDTO",
    "MangaProjectStatsDTO", 
    "MangaProjectSummaryDTO",
    
    # Generation Request DTOs
    "GenerationRequestDTO",
    "GenerationRequestCreateDTO",
    "GenerationRequestUpdateDTO",
    "GenerationRequestStatsDTO",
    "GenerationRequestProgressDTO",
    
    # Processing Module DTOs
    "ProcessingModuleDTO",
    "ProcessingModuleCreateDTO", 
    "ProcessingModuleUpdateDTO",
    "ProcessingModuleStatsDTO",
    "ProcessingModuleResultDTO",
    "PreviewVersionCreateDTO",
    "PreviewVersionUpdateDTO",
    "PreviewInteractionCreateDTO",
    "PreviewQualitySettingsCreateDTO",
    "PreviewQualitySettingsUpdateDTO",
]
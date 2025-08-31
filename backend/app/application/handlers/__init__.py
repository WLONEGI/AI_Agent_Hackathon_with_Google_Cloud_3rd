"""Handler definitions for CQRS pattern."""

from .base_handler import (
    AbstractCommandHandler,
    AbstractQueryHandler,
    BaseHandler,
    HandlerRegistry
)
from .user_handlers import (
    CreateUserCommandHandler,
    UpdateUserCommandHandler,
    DeleteUserCommandHandler,
    GetUserQueryHandler,
    ListUsersQueryHandler
)
from .manga_project_handlers import (
    CreateMangaProjectCommandHandler,
    UpdateMangaProjectCommandHandler,
    DeleteMangaProjectCommandHandler,
    GetMangaProjectQueryHandler,
    ListMangaProjectsQueryHandler
)
from .generation_request_handlers import (
    CreateGenerationRequestCommandHandler,
    UpdateGenerationRequestStatusCommandHandler,
    GetGenerationRequestQueryHandler,
    ListGenerationRequestsQueryHandler
)
from .processing_module_handlers import (
    StartProcessingModuleCommandHandler,
    CompleteProcessingModuleCommandHandler,
    GetProcessingModuleQueryHandler,
    ListProcessingModulesQueryHandler
)

__all__ = [
    # Base
    "AbstractCommandHandler",
    "AbstractQueryHandler",
    "BaseHandler",
    "HandlerRegistry",
    
    # User Handlers
    "CreateUserCommandHandler",
    "UpdateUserCommandHandler",
    "DeleteUserCommandHandler", 
    "GetUserQueryHandler",
    "ListUsersQueryHandler",
    
    # Manga Project Handlers
    "CreateMangaProjectCommandHandler",
    "UpdateMangaProjectCommandHandler",
    "DeleteMangaProjectCommandHandler",
    "GetMangaProjectQueryHandler",
    "ListMangaProjectsQueryHandler",
    
    # Generation Request Handlers
    "CreateGenerationRequestCommandHandler",
    "UpdateGenerationRequestStatusCommandHandler",
    "GetGenerationRequestQueryHandler",
    "ListGenerationRequestsQueryHandler",
    
    # Processing Module Handlers
    "StartProcessingModuleCommandHandler",
    "CompleteProcessingModuleCommandHandler", 
    "GetProcessingModuleQueryHandler",
    "ListProcessingModulesQueryHandler",
]
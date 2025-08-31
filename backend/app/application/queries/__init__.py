"""Query definitions for CQRS pattern."""

from .base_query import AbstractQuery, Query, QueryResult
from .user_queries import (
    GetUserQuery,
    GetUserByEmailQuery,
    ListUsersQuery,
    GetUserStatsQuery,
    SearchUsersQuery
)
from .manga_project_queries import (
    GetMangaProjectQuery,
    ListMangaProjectsQuery,
    SearchMangaProjectsQuery,
    GetMangaProjectStatsQuery,
    GetMangaProjectsByUserQuery
)
from .generation_request_queries import (
    GetGenerationRequestQuery,
    ListGenerationRequestsQuery,
    GetGenerationRequestsByUserQuery,
    GetGenerationRequestsByProjectQuery,
    GetGenerationRequestStatsQuery
)
from .processing_module_queries import (
    GetProcessingModuleQuery,
    ListProcessingModulesQuery,
    GetProcessingModulesByRequestQuery,
    GetProcessingModuleStatsQuery
)

__all__ = [
    # Base
    "AbstractQuery",
    "Query", 
    "QueryResult",
    
    # User Queries
    "GetUserQuery",
    "GetUserByEmailQuery",
    "ListUsersQuery",
    "GetUserStatsQuery",
    "SearchUsersQuery",
    
    # Manga Project Queries  
    "GetMangaProjectQuery",
    "ListMangaProjectsQuery",
    "SearchMangaProjectsQuery",
    "GetMangaProjectStatsQuery",
    "GetMangaProjectsByUserQuery",
    
    # Generation Request Queries
    "GetGenerationRequestQuery",
    "ListGenerationRequestsQuery",
    "GetGenerationRequestsByUserQuery",
    "GetGenerationRequestsByProjectQuery", 
    "GetGenerationRequestStatsQuery",
    
    # Processing Module Queries
    "GetProcessingModuleQuery",
    "ListProcessingModulesQuery",
    "GetProcessingModulesByRequestQuery",
    "GetProcessingModuleStatsQuery",
]
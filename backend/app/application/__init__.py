"""Application layer for CQRS pattern implementation.

This module implements the Command Query Responsibility Segregation (CQRS) pattern
with the following structure:

Commands (Write Operations):
- Commands represent state-changing operations
- Validated through command handlers
- Return CommandResult[T] for success/error handling

Queries (Read Operations):  
- Queries represent data retrieval operations
- Support filtering, pagination, and search
- Return QueryResult[T] with execution timing

Handlers:
- CommandHandlers coordinate with domain services for write operations
- QueryHandlers retrieve and format data for read operations
- Both inherit from base handler classes with common functionality

DTOs (Data Transfer Objects):
- Transfer data between application layers
- Include validation logic and serialization support
- Separate DTOs for create, update, and response operations

Integration Example:
    from app.application.handlers.base_handler import handler_registry
    from app.application.commands.user_commands import CreateUserCommand
    from app.application.queries.user_queries import GetUserQuery
    
    # Execute command
    command = CreateUserCommand(
        email="user@example.com",
        display_name="Test User",
        user_id="current_user_id"
    )
    result = await handler_registry.execute_command(command)
    
    # Execute query
    query = GetUserQuery(user_id=result.data, user_id="current_user_id")
    user_result = await handler_registry.execute_query(query)

Usage in API Layer:
    # In FastAPI endpoint
    @app.post("/users/", response_model=IdResponseDTO)
    async def create_user(user_data: UserCreateRequest):
        command = CreateUserCommand(**user_data.dict())
        result = await handler_registry.execute_command(command)
        
        if result.is_error():
            raise HTTPException(status_code=400, detail=result.error)
        
        return IdResponseDTO(id=result.data)
"""

# Explicit imports to avoid namespace pollution
from .commands import (
    base_command,
    user_commands,
    manga_project_commands,
    generation_request_commands,
    processing_module_commands,
    preview_commands
)
from .queries import (
    base_query,
    user_queries,
    manga_project_queries,
    generation_request_queries,
    processing_module_queries,
    preview_queries
)
from .handlers import (
    base_handler,
    user_handlers,
    manga_project_handlers,
    generation_request_handlers,
    processing_module_handlers,
    preview_command_handlers,
    preview_query_handlers
)
from .dto import (
    base_dto,
    user_dto,
    manga_project_dto,
    generation_request_dto,
    processing_module_dto
)

__all__ = [
    "commands",
    "queries", 
    "handlers",
    "dto"
]
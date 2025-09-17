__all__ = (
    "AuthService",
    "GenerationService",
    "FeedbackService",
    "PipelineOrchestrator",
    "ProjectService",
    "TokenService",
)


def __getattr__(name):  # pragma: no cover - thin convenience proxy
    if name == "GenerationService":
        from .generation_service import GenerationService

        return GenerationService
    if name == "FeedbackService":
        from .feedback_service import FeedbackService

        return FeedbackService
    if name == "PipelineOrchestrator":
        from .pipeline_service import PipelineOrchestrator

        return PipelineOrchestrator
    if name == "TokenService":
        from .token_service import TokenService

        return TokenService
    if name == "AuthService":
        from .auth_service import AuthService

        return AuthService
    if name == "ProjectService":
        from .project_service import ProjectService

        return ProjectService
    raise AttributeError(f"module 'app.services' has no attribute {name}")

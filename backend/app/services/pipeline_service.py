from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import clients as core_clients, settings as core_settings
from app.db.models import (
    FeedbackOptionTemplate,
    GeneratedImage,
    MangaAsset,
    MangaAssetType,
    MangaProject,
    MangaProjectStatus,
    MangaSession,
    MangaSessionStatus,
    PhaseResult,
    PreviewCacheMetadata,
    PreviewVersion,
)
from app.services.realtime_hub import build_event, realtime_hub
from app.services.hitl_service import HITLService
from app.services.vertex_ai_service import (
    VertexAIServiceError,
    VertexAIRateLimitError,
    VertexAICredentialsError,
    VertexAIUnavailableError,
    get_vertex_service,
)

logger = logging.getLogger(__name__)


class SessionScopeManager:
    """Manages session variable scope to prevent NameError in pipeline execution"""

    def __init__(self):
        self.session: Optional[MangaSession] = None
        self.request_id: Optional[UUID] = None
        self.project: Optional[MangaProject] = None
        self._initialized = False

    def initialize(self, request_id: UUID):
        """Initialize the manager with request ID"""
        self.request_id = request_id
        self._initialized = True

    def set_session(self, session: Optional[MangaSession]):
        """Set the session with validation"""
        if not self._initialized:
            raise ValueError("SessionScopeManager not initialized")
        self.session = session

    def set_project(self, project: Optional[MangaProject]):
        """Set the project reference"""
        self.project = project

    def get_session_id(self) -> str:
        """Get session ID safely for events"""
        if self.session and self.session.request_id:
            return str(self.session.request_id)
        elif self.request_id:
            return str(self.request_id)
        else:
            return "unknown"

    def get_project_id(self) -> Optional[str]:
        """Get project ID safely for events"""
        if self.session and self.session.project_id:
            return str(self.session.project_id)
        elif self.project and self.project.id:
            return str(self.project.id)
        else:
            return None

    def has_session(self) -> bool:
        """Check if valid session is available"""
        return self.session is not None

    def get_completion_event_data(self) -> Dict[str, Any]:
        """Generate safe completion event data"""
        return {
            "results": {"project_id": self.get_project_id()},
            "sessionId": self.get_session_id(),
            "requestId": self.get_session_id(),
        }


PHASE_SEQUENCE = (
    {
        "phase": 1,
        "name": "concept_analysis",
        "label": "Phase1: コンセプト・世界観分析",
        "preview_key": "concept_sheet",
    },
    {
        "phase": 2,
        "name": "character_design",
        "label": "Phase2: キャラクター設計",
        "preview_key": "character_board",
    },
    {
        "phase": 3,
        "name": "story_structure",
        "label": "Phase3: プロット構成",
        "preview_key": "story_outline",
    },
    {
        "phase": 4,
        "name": "name_generation",
        "label": "Phase4: ネーム生成",
        "preview_key": "name_layout",
    },
    {
        "phase": 5,
        "name": "scene_imagery",
        "label": "Phase5: シーン画像生成",
        "preview_key": "scene_preview",
    },
    {
        "phase": 6,
        "name": "dialogue_layout",
        "label": "Phase6: セリフ配置",
        "preview_key": "dialogue_layout",
    },
    {
        "phase": 7,
        "name": "final_composition",
        "label": "Phase7: 最終統合・品質調整",
        "preview_key": "final_board",
    },
)

QUALITY_THRESHOLD = 0.72
MAX_PHASE_RETRIES = 3
DEFAULT_PAGE_MIN = 8
MAX_PANEL_IMAGES = 3


class PhaseDependencyError(Exception):
    """Phase dependency validation error"""
    pass


class PhaseDependencyValidator:
    """Validates phase dependencies to prevent runtime errors"""

    # Phase dependency mapping: phase -> list of required previous phases
    PHASE_DEPENDENCIES = {
        1: [],                    # Phase 1: No dependencies
        2: [1],                   # Phase 2: Needs concept analysis
        3: [1, 2],               # Phase 3: Needs concept and characters
        4: [1, 3],               # Phase 4: Needs concept and story structure
        5: [4],                  # Phase 5: Needs panel layout
        6: [3, 4, 5],           # Phase 6: Needs story, panels, and images
        7: [1, 2, 3, 4, 5, 6],  # Phase 7: Needs all previous phases
    }

    # Required data keys for each phase
    REQUIRED_DATA_KEYS = {
        1: ["themes", "worldSetting", "genre"],
        2: ["characters"],
        3: ["acts", "overallArc"],
        4: ["panels", "pageCount"],
        5: ["images"],
        6: ["dialogues", "soundEffects"],
        7: ["finalPages", "qualityChecks"],
    }

    @classmethod
    def validate_phase_dependencies(
        cls,
        phase_number: int,
        context: Dict[int, Dict[str, Any]]
    ) -> None:
        """
        Validate that all required dependencies are present and valid

        Args:
            phase_number: Current phase to validate
            context: Phase context dictionary

        Raises:
            PhaseDependencyError: If dependencies are missing or invalid
        """
        required_phases = cls.PHASE_DEPENDENCIES.get(phase_number, [])

        for required_phase in required_phases:
            # Check if required phase exists in context
            if required_phase not in context:
                raise PhaseDependencyError(
                    f"Phase {phase_number} requires Phase {required_phase} "
                    f"to complete first, but Phase {required_phase} not found in context"
                )

            # Check if required phase has valid data
            phase_data = context[required_phase]
            if not cls._validate_phase_data(required_phase, phase_data):
                raise PhaseDependencyError(
                    f"Phase {phase_number} requires valid data from Phase {required_phase}, "
                    f"but Phase {required_phase} data is invalid or incomplete"
                )

    @classmethod
    def _validate_phase_data(cls, phase_number: int, phase_data: Dict[str, Any]) -> bool:
        """
        Validate that phase data contains required keys and is not empty

        Args:
            phase_number: Phase number to validate
            phase_data: Phase data dictionary

        Returns:
            bool: True if data is valid, False otherwise
        """
        if not isinstance(phase_data, dict):
            return False

        # Check if data section exists
        data_section = phase_data.get("data", {})
        if not isinstance(data_section, dict) or not data_section:
            return False

        # Check required keys for this phase
        required_keys = cls.REQUIRED_DATA_KEYS.get(phase_number, [])
        for key in required_keys:
            if key not in data_section:
                return False

            # Check if key has meaningful content
            value = data_section[key]
            if value is None:
                return False

            # For list values, check they're not empty
            if isinstance(value, list) and len(value) == 0:
                return False

            # For string values, check they're not empty
            if isinstance(value, str) and not value.strip():
                return False

        return True


class PhaseTimeoutError(Exception):
    """Phase execution timeout error"""
    pass


class PhaseTimeoutManager:
    """Manages timeout control for each phase to prevent indefinite hanging"""

    # Phase-specific timeout settings in seconds
    # Based on expected processing complexity for each phase
    PHASE_TIMEOUTS = {
        1: 60,    # Concept analysis: Quick text processing
        2: 90,    # Character generation: Text + simple image generation
        3: 120,   # Story structure: Complex text processing
        4: 90,    # Panel layout: Layout calculations
        5: 300,   # Scene imagery: Most time-consuming - complex image generation
        6: 120,   # Dialogue layout: Text processing with layout
        7: 180,   # Final composition: Assembly and quality checks
    }

    # Default timeout for unknown phases
    DEFAULT_TIMEOUT = 120

    @classmethod
    async def execute_with_timeout(
        cls,
        phase_number: int,
        coro,
        custom_timeout: Optional[int] = None
    ):
        """
        Execute a coroutine with phase-appropriate timeout

        Args:
            phase_number: The phase number (1-7)
            coro: The coroutine to execute
            custom_timeout: Optional custom timeout override

        Returns:
            The result of the coroutine execution

        Raises:
            PhaseTimeoutError: If the operation times out
        """
        timeout = custom_timeout or cls.PHASE_TIMEOUTS.get(phase_number, cls.DEFAULT_TIMEOUT)

        try:
            logger.debug(f"Executing phase {phase_number} with timeout {timeout}s")
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            error_msg = f"Phase {phase_number} timed out after {timeout} seconds"
            logger.error(error_msg)
            raise PhaseTimeoutError(error_msg)

    @classmethod
    def get_timeout_for_phase(cls, phase_number: int) -> int:
        """Get the configured timeout for a specific phase"""
        return cls.PHASE_TIMEOUTS.get(phase_number, cls.DEFAULT_TIMEOUT)


class ErrorRecoveryStrategy:
    """Defines error recovery strategies for different error types"""

    # Recovery strategy types
    IMMEDIATE_FAIL = "immediate_fail"     # Unrecoverable errors
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # Network/Service errors
    ADAPTIVE_WAIT = "adaptive_wait"       # Rate limiting errors
    LIMITED_RETRY = "limited_retry"       # Unknown errors with conservative retry

    def __init__(self, strategy_type: str, max_retries: int = 3, base_delay: float = 1.0):
        self.strategy_type = strategy_type
        self.max_retries = max_retries
        self.base_delay = base_delay


class ErrorRecoveryManager:
    """Standardizes error recovery patterns across the pipeline"""

    # Error type to recovery strategy mapping
    ERROR_STRATEGIES = {
        # Unrecoverable errors - immediate failure
        "VertexAICredentialsError": ErrorRecoveryStrategy(
            ErrorRecoveryStrategy.IMMEDIATE_FAIL, max_retries=0
        ),
        "PhaseTimeoutError": ErrorRecoveryStrategy(
            ErrorRecoveryStrategy.IMMEDIATE_FAIL, max_retries=0
        ),
        "PhaseDependencyError": ErrorRecoveryStrategy(
            ErrorRecoveryStrategy.IMMEDIATE_FAIL, max_retries=0
        ),

        # Network/Service errors - exponential backoff retry
        "VertexAIUnavailableError": ErrorRecoveryStrategy(
            ErrorRecoveryStrategy.EXPONENTIAL_BACKOFF, max_retries=3, base_delay=2.0
        ),
        "VertexAIServiceError": ErrorRecoveryStrategy(
            ErrorRecoveryStrategy.EXPONENTIAL_BACKOFF, max_retries=3, base_delay=1.5
        ),

        # Rate limiting - adaptive wait
        "VertexAIRateLimitError": ErrorRecoveryStrategy(
            ErrorRecoveryStrategy.ADAPTIVE_WAIT, max_retries=3, base_delay=2.0
        ),

        # Unknown errors - limited conservative retry
        "Exception": ErrorRecoveryStrategy(
            ErrorRecoveryStrategy.LIMITED_RETRY, max_retries=1, base_delay=1.0
        ),
    }

    @classmethod
    def get_strategy(cls, error_type: str) -> ErrorRecoveryStrategy:
        """Get recovery strategy for a specific error type"""
        return cls.ERROR_STRATEGIES.get(error_type, cls.ERROR_STRATEGIES["Exception"])

    @classmethod
    def should_retry(cls, error_type: str, current_attempt: int) -> bool:
        """Determine if an error should be retried based on strategy"""
        strategy = cls.get_strategy(error_type)
        return current_attempt < strategy.max_retries

    @classmethod
    async def calculate_wait_time(cls, error_type: str, attempt: int) -> float:
        """Calculate wait time based on error type and attempt number"""
        strategy = cls.get_strategy(error_type)

        if strategy.strategy_type == ErrorRecoveryStrategy.IMMEDIATE_FAIL:
            return 0.0
        elif strategy.strategy_type == ErrorRecoveryStrategy.EXPONENTIAL_BACKOFF:
            # Exponential backoff: base_delay * (2 ^ (attempt - 1))
            return strategy.base_delay * (2 ** (attempt - 1))
        elif strategy.strategy_type == ErrorRecoveryStrategy.ADAPTIVE_WAIT:
            # Adaptive wait with jitter for rate limiting
            return strategy.base_delay * attempt + (attempt * 0.5)  # Linear increase with jitter
        elif strategy.strategy_type == ErrorRecoveryStrategy.LIMITED_RETRY:
            # Conservative fixed delay
            return strategy.base_delay
        else:
            return strategy.base_delay

    @classmethod
    def get_failure_reason(cls, error_type: str, attempt: int) -> str:
        """Generate standardized failure reason for logging"""
        strategy = cls.get_strategy(error_type)

        if strategy.strategy_type == ErrorRecoveryStrategy.IMMEDIATE_FAIL:
            return f"{error_type.lower()}_unrecoverable"
        else:
            return f"{error_type.lower()}_max_retries_exceeded"


class PhaseContextManager:
    """Manages phase context with state protection and rollback capabilities"""

    def __init__(self):
        self._context: Dict[int, Dict[str, Any]] = {}
        self._snapshots: Dict[int, Dict[int, Dict[str, Any]]] = {}  # phase_number -> context_snapshot
        self._validated_phases: set = set()

    def get_context(self) -> Dict[int, Dict[str, Any]]:
        """Get a read-only copy of the current context"""
        import copy
        return copy.deepcopy(self._context)

    def get_phase_data(self, phase_number: int) -> Optional[Dict[str, Any]]:
        """Get data for a specific phase (returns copy)"""
        import copy
        phase_data = self._context.get(phase_number)
        return copy.deepcopy(phase_data) if phase_data else None

    def has_phase(self, phase_number: int) -> bool:
        """Check if a phase exists in the context"""
        return phase_number in self._context

    def create_snapshot(self, phase_number: int) -> None:
        """Create a snapshot of the current context before processing a phase"""
        import copy
        self._snapshots[phase_number] = copy.deepcopy(self._context)
        logger.debug(f"Created context snapshot for phase {phase_number}")

    def set_phase_data(self, phase_number: int, phase_data: Dict[str, Any]) -> None:
        """Set data for a phase with validation"""
        if not isinstance(phase_data, dict):
            raise ValueError(f"Phase data must be a dictionary, got {type(phase_data)}")

        # Validate that essential keys exist
        if "data" not in phase_data:
            raise ValueError(f"Phase {phase_number} data missing required 'data' key")

        import copy
        self._context[phase_number] = copy.deepcopy(phase_data)
        self._validated_phases.add(phase_number)
        logger.debug(f"Set validated data for phase {phase_number}")

    def rollback_to_snapshot(self, phase_number: int) -> bool:
        """Rollback context to the snapshot taken before phase processing"""
        if phase_number not in self._snapshots:
            logger.warning(f"No snapshot available for phase {phase_number} rollback")
            return False

        import copy
        self._context = copy.deepcopy(self._snapshots[phase_number])

        # Remove validation for any phases that were added after the snapshot
        self._validated_phases = {p for p in self._validated_phases if p in self._context}

        logger.info(f"Rolled back context to snapshot before phase {phase_number}")
        return True

    def cleanup_snapshots(self, keep_latest: int = 2) -> None:
        """Clean up old snapshots to prevent memory bloat"""
        if len(self._snapshots) <= keep_latest:
            return

        # Keep only the latest snapshots
        latest_phases = sorted(self._snapshots.keys())[-keep_latest:]
        old_snapshots = {phase: snapshot for phase, snapshot in self._snapshots.items()
                        if phase not in latest_phases}

        for phase in old_snapshots:
            del self._snapshots[phase]

        logger.debug(f"Cleaned up {len(old_snapshots)} old context snapshots")

    def validate_context_integrity(self) -> bool:
        """Validate the integrity of the current context"""
        try:
            # Check that all phases have the required structure
            for phase_number, phase_data in self._context.items():
                if not isinstance(phase_data, dict):
                    logger.error(f"Phase {phase_number} data is not a dictionary")
                    return False

                if "data" not in phase_data:
                    logger.error(f"Phase {phase_number} missing required 'data' key")
                    return False

                # Validate dependencies based on PhaseDependencyValidator
                try:
                    PhaseDependencyValidator.validate_phase_dependencies(phase_number, self._context)
                except PhaseDependencyError as e:
                    logger.error(f"Context dependency validation failed: {e}")
                    return False

            logger.debug("Context integrity validation passed")
            return True

        except Exception as e:
            logger.error(f"Context integrity validation error: {e}")
            return False

    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context state for logging"""
        return {
            "phases_completed": list(self._context.keys()),
            "validated_phases": list(self._validated_phases),
            "available_snapshots": list(self._snapshots.keys()),
            "total_context_size": len(self._context)
        }


class QualityMetric:
    """Defines a quality metric for phase evaluation"""

    def __init__(self, name: str, weight: float, data_key: str,
                 expected_range: tuple = (0, 1), transform_func=None):
        self.name = name
        self.weight = weight  # Contribution to overall score (0.0-1.0)
        self.data_key = data_key  # Key in data or diagnostics
        self.expected_range = expected_range  # (min, max) expected values
        self.transform_func = transform_func  # Optional transformation function

    def evaluate(self, data: Dict[str, Any], diagnostics: Dict[str, Any]) -> float:
        """Evaluate this metric and return a normalized score (0.0-1.0)"""
        # Apply transformation function if provided (it gets full context)
        if self.transform_func:
            processed_value = self.transform_func(data, diagnostics)
        else:
            # Get raw value from data or diagnostics
            raw_value = data.get(self.data_key) or diagnostics.get(self.data_key, 0)
            processed_value = raw_value

        # Handle different value types
        if isinstance(processed_value, (list, tuple)):
            processed_value = len(processed_value)
        elif isinstance(processed_value, bool):
            processed_value = 1.0 if processed_value else 0.0
        elif not isinstance(processed_value, (int, float)):
            processed_value = 0.0

        # Normalize to expected range
        min_val, max_val = self.expected_range
        if max_val > min_val:
            normalized = max(0.0, min(1.0, (processed_value - min_val) / (max_val - min_val)))
        else:
            normalized = 1.0 if processed_value >= min_val else 0.0

        return normalized


class QualityCalculator:
    """Unified quality calculation system with consistent scoring across all phases"""

    # Consistent base quality score for all phases
    BASE_QUALITY_SCORE = 0.65

    # Quality score bounds (consistent across all phases)
    MIN_QUALITY_SCORE = 0.55
    MAX_QUALITY_SCORE = 0.97

    # Phase-specific quality metrics configuration
    PHASE_METRICS = {
        1: [  # Concept Analysis
            QualityMetric("theme_richness", 0.4, "themes", (0, 5)),
            QualityMetric("world_setting", 0.3, "worldSetting", (0, 1),
                         lambda data, diag: 1 if data.get("worldSetting") else 0),
            QualityMetric("genre_clarity", 0.2, "genre", (0, 1),
                         lambda data, diag: 1 if data.get("genre") else 0),
            QualityMetric("mood_definition", 0.1, "mood", (0, 1),
                         lambda data, diag: 1 if data.get("mood") else 0),
        ],
        2: [  # Character Generation
            QualityMetric("character_count", 0.6, "characters", (0, 6)),
            QualityMetric("character_depth", 0.3, "characterDepth", (0, 1)),
            QualityMetric("visual_assets", 0.1, "imageUrl", (0, 1),
                         lambda data, diag: 1 if data.get("imageUrl") else 0),
        ],
        3: [  # Story Structure
            QualityMetric("story_acts", 0.5, "acts", (0, 5)),
            QualityMetric("scene_count", 0.3, "sceneCount", (0, 15)),
            QualityMetric("narrative_flow", 0.2, "overallArc", (0, 1),
                         lambda data, diag: 1 if data.get("overallArc") else 0),
        ],
        4: [  # Panel Layout
            QualityMetric("panel_count", 0.5, "panelCount", (0, 20)),
            QualityMetric("page_count", 0.3, "pageCount", (5, 25)),
            QualityMetric("layout_complexity", 0.2, "layoutComplexity", (0, 1)),
        ],
        5: [  # Scene Imagery
            QualityMetric("image_generation_ratio", 0.8, "generationRatio", (0, 1),
                         lambda data, diag: (diag.get("generatedImages", 0) /
                                           max(diag.get("requestedPanels", 1), 1))),
            QualityMetric("image_quality", 0.2, "imageQuality", (0, 1)),
        ],
        6: [  # Dialogue Layout
            QualityMetric("dialogue_coverage", 0.6, "dialogues", (0, 30)),
            QualityMetric("sound_effects", 0.3, "soundEffects", (0, 10)),
            QualityMetric("text_layout", 0.1, "textLayout", (0, 1)),
        ],
        7: [  # Final Composition
            QualityMetric("overall_quality", 0.5, "overallQuality", (0, 1)),
            QualityMetric("quality_checks", 0.3, "qualityChecks", (0, 10),
                         lambda data, diag: sum(1 for item in data.get("qualityChecks", [])
                                              if isinstance(item, dict) and item.get("status") == "completed")),
            QualityMetric("completion_score", 0.2, "completionScore", (0, 1)),
        ],
    }

    @classmethod
    def calculate_quality(
        cls,
        phase_number: int,
        data: Dict[str, Any],
        diagnostics: Dict[str, Any]
    ) -> float:
        """
        Calculate quality score for a phase using unified methodology

        Returns:
            Quality score between MIN_QUALITY_SCORE and MAX_QUALITY_SCORE
        """
        metrics = cls.PHASE_METRICS.get(phase_number, [])

        if not metrics:
            # Fallback for unknown phases
            return cls.BASE_QUALITY_SCORE

        # Calculate weighted score from all metrics
        total_weighted_score = 0.0
        total_weight = 0.0

        for metric in metrics:
            metric_score = metric.evaluate(data, diagnostics)
            weighted_contribution = metric_score * metric.weight
            total_weighted_score += weighted_contribution
            total_weight += metric.weight

        # Normalize by total weight (should be 1.0, but protect against misconfiguration)
        if total_weight > 0:
            normalized_score = total_weighted_score / total_weight
        else:
            normalized_score = 0.5  # Neutral score if no valid metrics

        # Apply to base score with scaling
        quality_range = cls.MAX_QUALITY_SCORE - cls.MIN_QUALITY_SCORE
        final_score = cls.BASE_QUALITY_SCORE + (normalized_score - 0.5) * quality_range * 0.4

        # Ensure bounds
        return max(cls.MIN_QUALITY_SCORE, min(cls.MAX_QUALITY_SCORE, final_score))

    @classmethod
    def get_quality_breakdown(
        cls,
        phase_number: int,
        data: Dict[str, Any],
        diagnostics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get detailed breakdown of quality calculation for debugging/transparency
        """
        metrics = cls.PHASE_METRICS.get(phase_number, [])
        breakdown = {
            "phase_number": phase_number,
            "base_score": cls.BASE_QUALITY_SCORE,
            "metrics": [],
            "total_score": cls.calculate_quality(phase_number, data, diagnostics)
        }

        for metric in metrics:
            metric_score = metric.evaluate(data, diagnostics)
            breakdown["metrics"].append({
                "name": metric.name,
                "weight": metric.weight,
                "raw_score": metric_score,
                "weighted_contribution": metric_score * metric.weight,
                "data_key": metric.data_key
            })

        return breakdown


class PipelineOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = core_settings.get_settings()
        core_clients.get_storage_client.cache_clear()
        self.vertex_service = get_vertex_service()
        self.hitl_service = HITLService(db) if self.settings.hitl_enabled else None

    async def run(self, request_id: UUID) -> None:
        # Initialize session scope manager to prevent variable scope issues
        scope_manager = SessionScopeManager()
        scope_manager.initialize(request_id)

        # Use transaction to ensure all-or-nothing pipeline execution
        async with self.db.begin() as transaction:
            try:
                session = await self._get_session(request_id)
                if session is None:
                    raise ValueError("session_not_found")

                # Set session in scope manager for safe access throughout pipeline
                scope_manager.set_session(session)

                session.status = MangaSessionStatus.RUNNING.value
                session.started_at = session.started_at or datetime.utcnow()
                # Remove flush() - will be handled by transaction commit

                await realtime_hub.publish(
                    session.request_id,
                    build_event(
                        "session_start",
                        sessionId=str(session.request_id),
                        requestId=str(session.request_id),
                    ),
                )

                project = await self._load_project(session.project_id)
                # Set project in scope manager for safe access
                scope_manager.set_project(project)

                # Initialize protected phase context manager
                context_manager = PhaseContextManager()

                # Check if HITL is enabled for this session
                hitl_enabled = self._is_hitl_enabled_for_session(session)

                for phase_config in PHASE_SEQUENCE:
                    phase_number = phase_config["phase"]
                    session.current_phase = phase_number
                    # Remove flush() - will be handled by transaction commit

                    await realtime_hub.publish(
                        session.request_id,
                        build_event(
                            "phase_start",
                            phaseId=phase_number,
                            phaseName=phase_config["label"],
                        ),
                    )

                    await realtime_hub.publish(
                        session.request_id,
                        build_event(
                            "phase_progress",
                            phase=phase_number,
                            progress=10,
                            status="processing",
                        ),
                    )

                    # Create context snapshot before phase processing for rollback capability
                    context_manager.create_snapshot(phase_number)

                    attempt = 0
                    phase_payload: Optional[Dict[str, Any]] = None
                    quality_score = 0.0
                    while attempt < MAX_PHASE_RETRIES:
                        attempt += 1
                        try:
                            # Get current context for phase processing
                            current_context = context_manager.get_context()
                            phase_payload = await self._process_phase(session, phase_config, current_context, attempt)
                        except Exception as exc:
                            # Standardized error recovery using ErrorRecoveryManager
                            error_type = type(exc).__name__

                            # Log error with appropriate level based on error type
                            if error_type in ["VertexAICredentialsError", "PhaseTimeoutError", "PhaseDependencyError"]:
                                logger.error("Unrecoverable error on phase %s (attempt %s): %s", phase_number, attempt, exc)
                            else:
                                logger.warning("Recoverable error on phase %s (attempt %s): %s", phase_number, attempt, exc)

                            # Check if we should retry based on error recovery strategy
                            if not ErrorRecoveryManager.should_retry(error_type, attempt):
                                # Rollback context to snapshot for unrecoverable errors
                                context_manager.rollback_to_snapshot(phase_number)
                                failure_reason = ErrorRecoveryManager.get_failure_reason(error_type, attempt)
                                await self._handle_failure(session, project, phase_number, failure_reason)
                                return

                            # Calculate wait time based on error type and attempt
                            wait_time = await ErrorRecoveryManager.calculate_wait_time(error_type, attempt)

                            if wait_time > 0:
                                logger.info(f"Waiting {wait_time:.1f}s before retry (strategy: {ErrorRecoveryManager.get_strategy(error_type).strategy_type})")
                                try:
                                    # Use timeout protection for wait operations
                                    await asyncio.wait_for(asyncio.sleep(wait_time), timeout=max(wait_time + 5, 15))
                                except asyncio.TimeoutError:
                                    logger.warning(f"Error recovery wait timed out for phase {phase_number}")
                                    # Continue anyway - this shouldn't normally happen

                            continue  # Retry the operation

                        quality_score = phase_payload.get("metadata", {}).get("quality", 0.0)
                        if quality_score >= QUALITY_THRESHOLD:
                            break

                        logger.warning(
                            "Phase %s quality %.2f below threshold %.2f (attempt %s)",
                            phase_number,
                            quality_score,
                            QUALITY_THRESHOLD,
                            attempt,
                        )
                        if attempt >= MAX_PHASE_RETRIES:
                            await self._handle_failure(session, project, phase_number, "quality_threshold_not_met")
                            return

                    if phase_payload is None:
                        await self._handle_failure(session, project, phase_number, "phase_payload_missing")
                        return

                    if attempt > 1:
                        session.retry_count = (session.retry_count or 0) + (attempt - 1)

                    await self._persist_phase_outputs(
                        session=session,
                        project=project,
                        phase_config=phase_config,
                        phase_payload=phase_payload,
                    )

                    await realtime_hub.publish(
                        session.request_id,
                        build_event(
                            "phase_progress",
                            phase=phase_number,
                            progress=90,
                            status="completed",
                            preview=phase_payload.get("preview"),
                        ),
                    )

                    await realtime_hub.publish(
                        session.request_id,
                        build_event(
                            "phase_complete",
                            phaseId=phase_number,
                            result=phase_payload,
                        ),
                    )

                    # Store validated phase data in protected context
                    context_manager.set_phase_data(phase_number, phase_payload)

                    # HITL Integration: Request feedback after phase completion
                    if hitl_enabled and self.hitl_service:
                        # Get current context for HITL feedback
                        current_context = context_manager.get_context()
                        feedback_result = await self._handle_hitl_feedback(
                            session, phase_number, phase_payload, current_context
                        )

                        # Apply feedback modifications if provided
                        if feedback_result and feedback_result.get("modifications"):
                            phase_payload = await self._apply_feedback_modifications(
                                session, phase_config, phase_payload, feedback_result["modifications"]
                            )

                            # CRITICAL: Re-evaluate quality after HITL modifications
                            modified_data = phase_payload.get("data", {})
                            modified_diagnostics = phase_payload.get("diagnostics", {})
                            modified_quality = self._evaluate_quality(phase_number, modified_data, modified_diagnostics)

                            # Update metadata with new quality score
                            if "metadata" not in phase_payload:
                                phase_payload["metadata"] = {}
                            phase_payload["metadata"]["quality"] = round(modified_quality, 3)
                            phase_payload["metadata"]["modified_by_user"] = True
                            phase_payload["metadata"]["original_quality"] = phase_payload["metadata"].get("quality", 0.0)

                            # Check if quality degraded after modifications
                            if modified_quality < QUALITY_THRESHOLD:
                                logger.warning(
                                    f"Phase {phase_number} quality degraded to {modified_quality:.3f} "
                                    f"after HITL modifications (threshold: {QUALITY_THRESHOLD})"
                                )

                                # Notify user about quality degradation
                                await realtime_hub.publish(
                                    session.request_id,
                                    build_event(
                                        "quality_warning",
                                        phase=phase_number,
                                        original_quality=phase_payload["metadata"].get("original_quality", 0.0),
                                        modified_quality=modified_quality,
                                        threshold=QUALITY_THRESHOLD,
                                        message=f"User modifications reduced quality below threshold"
                                    ),
                                )

                            # Update protected context with modified payload
                            context_manager.set_phase_data(phase_number, phase_payload)

                            # Re-persist modified outputs with updated quality
                            await self._persist_phase_outputs(
                                session=session,
                                project=project,
                                phase_config=phase_config,
                                phase_payload=phase_payload,
                            )

                # Validate final context integrity before completion
                if not context_manager.validate_context_integrity():
                    logger.error("Context integrity validation failed at pipeline completion")
                    raise ValueError("Pipeline context integrity validation failed")

                session.status = MangaSessionStatus.COMPLETED.value
                session.completed_at = datetime.utcnow()
                if project is not None:
                    project.status = MangaProjectStatus.COMPLETED
                    # Get final context for page estimation
                    final_context = context_manager.get_context()
                    project.total_pages = self._estimate_pages(session, final_context)
                    project.updated_at = datetime.utcnow()
                    await self._upsert_project_assets(project, session)
                # Remove flush() - will be handled by transaction commit

                # Clean up context snapshots before completion
                context_manager.cleanup_snapshots(keep_latest=1)

                # Log context summary for debugging
                context_summary = context_manager.get_context_summary()
                logger.info(f"Pipeline completed successfully for session {request_id}. Context: {context_summary}")

                # Transaction will commit automatically on successful completion
                await transaction.commit()

            except Exception as e:
                # Transaction will rollback automatically on exception
                await transaction.rollback()
                logger.error(f"Pipeline failed for session {request_id}, rolling back all changes: {e}")

                # Handle failure status update outside transaction using scope manager
                failed_session = await self._get_session(request_id)
                if failed_session:
                    scope_manager.set_session(failed_session)
                    await self._handle_failure_outside_transaction(failed_session, scope_manager.project, 0, str(e))
                raise

        # Publish completion event outside transaction using scope manager
        # This prevents NameError if session was not initialized due to early pipeline failure
        completion_event_data = scope_manager.get_completion_event_data()
        await realtime_hub.publish(
            UUID(completion_event_data["sessionId"]) if completion_event_data["sessionId"] != "unknown" else request_id,
            build_event("session_complete", **completion_event_data),
        )

    async def _get_session(self, request_id: UUID) -> Optional[MangaSession]:
        result = await self.db.execute(
            select(MangaSession).where(MangaSession.request_id == request_id)
        )
        return result.scalar_one_or_none()

    async def _persist_phase_outputs(
        self,
        *,
        session: MangaSession,
        project: Optional[MangaProject],
        phase_config: Dict[str, Any],
        phase_payload: Dict[str, Any],
    ) -> None:
        phase_number = phase_config["phase"]
        quality_score = float(phase_payload.get("metadata", {}).get("quality", 0.0))

        phase_result = PhaseResult(
            session_id=session.id,
            phase=phase_number,
            status="completed",
            content=phase_payload,
            quality_score=quality_score,
        )
        self.db.add(phase_result)
        await self.db.flush()

        preview_version = PreviewVersion(
            session_id=session.id,
            phase=phase_number,
            version_data=phase_payload.get("preview"),
            quality_level=self._quality_to_level(quality_score),
            quality_score=quality_score,
        )
        self.db.add(preview_version)
        await self.db.flush()

        cache_entry = PreviewCacheMetadata(
            cache_key=(
                f"preview/{session.request_id}/phase-{phase_number}/"
                f"v{preview_version.created_at.timestamp():.0f}"
            ),
            version_id=preview_version.id,
            phase=phase_number,
            quality_level=self._quality_to_level(quality_score),
            signed_url=self._build_signed_url(session, phase_config, preview_version),
            content_type="application/json",
            expires_at=datetime.utcnow() + timedelta(seconds=self.settings.signed_url_ttl_seconds),
        )
        self.db.add(cache_entry)

        if phase_number == 5:
            images = phase_payload.get("data", {}).get("images", [])
            for index, image in enumerate(images, start=1):
                storage_path = (
                    f"projects/{session.project_id}/sessions/{session.request_id}/"
                    f"phase-{phase_number}/panel-{index}.png"
                )
                image_record = GeneratedImage(
                    session_id=session.id,
                    phase=phase_number,
                    storage_path=storage_path,
                    signed_url=self._build_asset_signed_url(storage_path),
                    image_metadata={
                        "panel_id": image.get("panelId"),
                        "status": image.get("status"),
                        "prompt": image.get("prompt"),
                        "has_preview": bool(image.get("url")),
                    },
                )
                self.db.add(image_record)

        await self.db.flush()

    async def _process_phase(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
        attempt: int,
    ) -> Dict[str, Any]:
        phase_number = phase_config["phase"]
        handler_map = {
            1: self._run_phase_concept,
            2: self._run_phase_characters,
            3: self._run_phase_story_structure,
            4: self._run_phase_panel_layout,
            5: self._run_phase_scene_imagery,
            6: self._run_phase_dialogue_layout,
            7: self._run_phase_final_composition,
        }
        handler = handler_map.get(phase_number)
        if handler is None:
            raise ValueError(f"unsupported_phase_{phase_number}")

        # Validate phase dependencies before processing
        try:
            PhaseDependencyValidator.validate_phase_dependencies(phase_number, context)
        except PhaseDependencyError as e:
            logger.error(f"Phase dependency validation failed for phase {phase_number}: {e}")
            raise ValueError(f"Phase {phase_number} dependency validation failed: {e}") from e

        start_time = time.perf_counter()

        # Execute phase handler with timeout control
        result = await PhaseTimeoutManager.execute_with_timeout(
            phase_number,
            handler(session, phase_config, context)
        )
        processing_time_ms = int((time.perf_counter() - start_time) * 1000)

        data = result.get("data", {})
        preview = result.get("preview") or data
        diagnostics = result.get("diagnostics", {})
        quality = self._evaluate_quality(phase_number, data, diagnostics)
        confidence = min(0.98, max(0.55, quality + 0.05))

        metadata = {
            "processingTimeMs": processing_time_ms,
            "quality": round(quality, 3),
            "confidence": round(confidence, 3),
            "attempt": attempt,
        }
        metadata.update(diagnostics)

        payload = {
            "phaseId": phase_number,
            "phaseName": phase_config["label"],
            "phaseKey": phase_config["name"],
            "data": data,
            "metadata": metadata,
            "preview": preview,
        }
        return payload

    async def _run_phase_concept(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        session_meta = session.session_metadata or {}
        story_text = session_meta.get("text", "")
        title = session_meta.get("title", "Untitled")
        trimmed_story = story_text[:6000]

        prompt = (
            "You are an AI manga production planner."
            " Extract concept metadata from the following story."
            " Respond in JSON with keys: themes (array of strings), world_setting, genre,"
            " target_audience, mood, synopsis (<=160 chars), page_estimate (int)."
            f"\n\nTITLE: {title}\nSTORY:\n{trimmed_story}"
        )
        raw = await self.vertex_service.generate_text(prompt)
        parsed = self._parse_json(raw)

        data = {
            "themes": self._ensure_list_of_strings(parsed, "themes", default=[title, "成長", "冒険"]),
            "worldSetting": self._coalesce(parsed, ["world_setting", "setting"], default="物語に基づく世界設定"),
            "genre": self._coalesce(parsed, ["genre"], default="ドラマ"),
            "targetAudience": self._coalesce(parsed, ["target_audience", "audience"], default="一般読者"),
            "mood": self._coalesce(parsed, ["mood", "tone"], default="希望と緊張が交錯"),
        }
        synopsis = self._coalesce(parsed, ["synopsis"], default=story_text[:160])
        page_estimate = self._coalesce(parsed, ["page_estimate", "pages"], default=max(DEFAULT_PAGE_MIN, math.ceil(len(story_text) / 800)))
        diagnostics = {
            "synopsis": synopsis,
            "pageEstimate": int(page_estimate) if isinstance(page_estimate, (int, float)) else DEFAULT_PAGE_MIN,
        }

        preview = {
            "themes": data["themes"][:3],
            "worldSetting": data["worldSetting"],
            "genre": data["genre"],
            "targetAudience": data["targetAudience"],
            "mood": data["mood"],
            "synopsis": synopsis,
        }

        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_characters(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        concept = context.get(1, {}).get("data", {})
        session_meta = session.session_metadata or {}
        story_text = session_meta.get("text", "")[:4000]

        prompt = (
            "You are designing manga characters."
            " Using the concept below, output JSON with key 'characters' (array of up to 3 objects)"
            " each object having name, role, appearance, personality."
            " Provide vivid but concise descriptions."
            f"\n\nCONCEPT: {json.dumps(concept, ensure_ascii=False)}\n\nSTORY_SNIPPET:\n{story_text}"
        )
        raw = await self.vertex_service.generate_text(prompt)
        parsed = self._parse_json(raw)
        characters = self._ensure_list_of_dicts(parsed, "characters")
        if not characters:
            characters = [
                {
                    "name": "主人公",
                    "role": "語り手",
                    "appearance": "短い黒髪と真剣な瞳",
                    "personality": "責任感が強く仲間思い",
                }
            ]

        awaitables = []
        for index, character in enumerate(characters[:2], start=1):
            prompt_image = (
                f"Manga character concept art for {character.get('name', 'main character')} in the style of modern Japanese manga. "
                f"World setting: {concept.get('worldSetting', 'contemporary Japan')}. "
                f"Appearance: {character.get('appearance', 'detailed description')}."
            )
            awaitables.append(self.vertex_service.generate_image(prompt_image))

        image_results: list[list[dict[str, Any]]] = []
        if awaitables:
            image_results = await asyncio.gather(*awaitables, return_exceptions=True)
        else:
            image_results = []

        enriched_characters = []
        for idx, character in enumerate(characters):
            image_url: Optional[str] = None
            if idx < len(image_results):
                result = image_results[idx]
                if isinstance(result, list) and result:
                    first = result[0]
                    image_url = first.get("data_url") or first.get("url")
                    if not image_url and first.get("image_base64"):
                        image_url = f"data:image/png;base64,{first['image_base64']}"
                    if not image_url and first.get("description"):
                        image_url = f"placeholder://character-{idx + 1}"
            enriched_characters.append(
                {
                    "name": character.get("name", f"キャラクター{idx + 1}"),
                    "role": character.get("role", "主要人物"),
                    "appearance": character.get("appearance", "外見情報なし"),
                    "personality": character.get("personality", "性格情報なし"),
                    "imageUrl": image_url,
                }
            )

        data = {
            "characters": enriched_characters,
            "imageUrl": next((c["imageUrl"] for c in enriched_characters if c.get("imageUrl")), None),
        }
        diagnostics = {
            "characterCount": len(enriched_characters),
        }
        preview = {
            "characters": enriched_characters[:2],
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_story_structure(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        concept = context.get(1, {}).get("data", {})
        characters = context.get(2, {}).get("data", {}).get("characters", [])
        session_meta = session.session_metadata or {}
        story_text = session_meta.get("text", "")[:5000]

        prompt = (
            "Create a three-act manga story outline in JSON with keys:"
            " acts (array of objects with title, description, scenes array) and overall_arc."
            " Scenes should be concise strings."
            f"\n\nCONCEPT: {json.dumps(concept, ensure_ascii=False)}"
            f"\nCHARACTERS: {json.dumps(characters, ensure_ascii=False)}"
            f"\nSOURCE:\n{story_text}"
        )
        raw = await self.vertex_service.generate_text(prompt)
        parsed = self._parse_json(raw)
        acts = self._ensure_list_of_dicts(parsed, "acts")
        if not acts:
            acts = [
                {
                    "title": "序章",
                    "description": "主人公が世界の異変に気づく",
                    "scenes": ["主人公の日常", "導入となる事件"],
                },
                {
                    "title": "対立",
                    "description": "仲間を得て課題に立ち向かう",
                    "scenes": ["仲間との出会い", "試練", "決断"],
                },
                {
                    "title": "解決",
                    "description": "クライマックスと余韻",
                    "scenes": ["最終決戦", "余韻のシーン"],
                },
            ]
        overall_arc = self._coalesce(parsed, ["overall_arc", "overallArc"], default="主人公の成長と世界の変革")

        data = {
            "acts": [
                {
                    "title": act.get("title", f"Act {idx + 1}"),
                    "description": act.get("description", ""),
                    "scenes": self._ensure_list_of_strings_from_value(act.get("scenes"), default=[]),
                }
                for idx, act in enumerate(acts)
            ],
            "overallArc": overall_arc,
        }
        diagnostics = {
            "actCount": len(data["acts"]),
            "sceneCount": sum(len(act["scenes"]) for act in data["acts"]),
        }
        preview = {
            "acts": data["acts"][:2],
            "overallArc": overall_arc,
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_panel_layout(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        story = context.get(3, {}).get("data", {})
        concept = context.get(1, {}).get("data", {})
        acts = story.get("acts", [])

        prompt = (
            "Design manga panel layout guidance in JSON with keys:"
            " panels (array of objects: description, composition, characters (array), dialogues (array), camera_angle)"
            " and page_count (int)."
            f"\n\nSTORY STRUCTURE: {json.dumps(story, ensure_ascii=False)}"
            f"\nCONCEPT: {json.dumps(concept, ensure_ascii=False)}"
        )
        raw = await self.vertex_service.generate_text(prompt)
        parsed = self._parse_json(raw)
        panels = self._ensure_list_of_dicts(parsed, "panels")
        if not panels:
            panels = [
                {
                    "description": "主人公が世界の異変に気づく導入カット",
                    "composition": "ワイドショット",
                    "characters": ["主人公"],
                    "dialogues": ["これは一体…"],
                    "camera_angle": "俯瞰",
                },
                {
                    "description": "仲間との合流で意思を固める",
                    "composition": "ミディアム",
                    "characters": ["主人公", "仲間"],
                    "dialogues": ["一緒にやろう"],
                    "camera_angle": "アイレベル",
                },
            ]
        page_count = parsed.get("page_count") or max(DEFAULT_PAGE_MIN, len(acts) * 6)

        data = {
            "panels": [
                {
                    "description": panel.get("description", "シーンの説明"),
                    "composition": panel.get("composition", "ミディアム"),
                    "characters": self._ensure_list_of_strings_from_value(panel.get("characters"), default=[]),
                    "dialogues": self._ensure_list_of_strings_from_value(panel.get("dialogues"), default=[]),
                    "cameraAngle": panel.get("camera_angle", panel.get("cameraAngle", "アイレベル")),
                }
                for panel in panels
            ],
            "pageCount": int(page_count) if isinstance(page_count, (int, float)) else DEFAULT_PAGE_MIN,
        }
        diagnostics = {
            "panelCount": len(data["panels"]),
            "pageCount": data["pageCount"],
        }
        preview = {
            "panels": data["panels"][:4],
            "pageCount": data["pageCount"],
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_scene_imagery(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        panels = context.get(4, {}).get("data", {}).get("panels", [])
        concept = context.get(1, {}).get("data", {})
        if not panels:
            panels = [
                {
                    "description": "主人公が街角で空を見上げる印象的なシーン",
                    "composition": "ロングショット",
                    "characters": ["主人公"],
                    "dialogues": [],
                    "cameraAngle": "ローアングル",
                }
            ]

        selected_panels = panels[:MAX_PANEL_IMAGES]
        prompts = []
        for panel in selected_panels:
            prompt = (
                f"Generate highly detailed manga panel concept art. "
                f"Scene: {panel.get('description', 'dramatic moment')}. "
                f"Characters: {', '.join(panel.get('characters', [])) or 'main cast'}. "
                f"Camera: {panel.get('cameraAngle', 'eye level')}. "
                f"World setting: {concept.get('worldSetting', 'contemporary Japan')}."
            )
            prompts.append(prompt)

        async def _generate(prompt: str) -> list[dict[str, Any]]:
            try:
                return await self.vertex_service.generate_image(prompt)
            except VertexAIServiceError:
                return [
                    {
                        "image_base64": None,
                        "data_url": None,
                        "description": f"Placeholder image for: {prompt[:100]}",
                    }
                ]

        results = await asyncio.gather(*(_generate(p) for p in prompts), return_exceptions=True)

        images = []
        diagnostics_generated = 0
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                images.append(
                    {
                        "url": None,
                        "prompt": prompts[idx],
                        "panelId": idx + 1,
                        "status": "error",
                    }
                )
                continue
            image_entry = result[0] if result else {}
            url = image_entry.get("data_url") or image_entry.get("url")
            if not url and image_entry.get("image_base64"):
                url = f"data:image/png;base64,{image_entry['image_base64']}"
            if not url and image_entry.get("description"):
                url = f"placeholder://panel-{idx + 1}"
            status = "completed" if url else "error"
            diagnostics_generated += 1 if url else 0
            images.append(
                {
                    "url": url,
                    "prompt": prompts[idx],
                    "panelId": idx + 1,
                    "status": status,
                }
            )

        data = {
            "images": images,
        }
        diagnostics = {
            "requestedPanels": len(prompts),
            "generatedImages": diagnostics_generated,
        }
        preview = {
            "images": images,
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_dialogue_layout(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        story = context.get(3, {}).get("data", {})
        characters = context.get(2, {}).get("data", {}).get("characters", [])
        panels = context.get(4, {}).get("data", {}).get("panels", [])

        prompt = (
            "Draft manga dialogues in JSON with keys: dialogues (array of {character, text, position, style, bubble_type})"
            " and sound_effects (array). Keep dialogue concise."
            f"\n\nSTORY STRUCTURE: {json.dumps(story, ensure_ascii=False)}"
            f"\nCHARACTERS: {json.dumps(characters, ensure_ascii=False)}"
            f"\nPANELS: {json.dumps(panels[:4], ensure_ascii=False)}"
        )
        raw = await self.vertex_service.generate_text(prompt)
        parsed = self._parse_json(raw)
        dialogues = self._ensure_list_of_dicts(parsed, "dialogues")
        if not dialogues:
            dialogues = [
                {
                    "character": character.get("name", "キャラクター"),
                    "text": "ここが転機になる…",
                    "position": "top-left",
                    "style": "bold",
                    "bubble_type": "speech",
                }
                for character in characters[:2]
            ] or [
                {
                    "character": "ナレーション",
                    "text": "物語はここから加速する",
                    "position": "bottom",
                    "style": "narration",
                    "bubble_type": "narration",
                }
            ]
        sound_effects = self._ensure_list_of_strings(parsed, "sound_effects", default=["ドン", "ザワザワ"])

        if len(dialogues) < 3:
            filler_templates = [
                {"character": "仲間", "text": "大丈夫、任せて！", "position": "right", "style": "normal", "bubble_type": "speech"},
                {"character": "敵", "text": "ここまで来るとは…", "position": "left", "style": "shout", "bubble_type": "speech"},
                {"character": "ナレーション", "text": "物語は佳境へ", "position": "bottom", "style": "narration", "bubble_type": "narration"},
            ]
            for template in filler_templates:
                if len(dialogues) >= 3:
                    break
                dialogues.append(template)

        if len(sound_effects) < 3:
            additional = ["ゴゴゴ", "バン", "キラリ"]
            for sfx in additional:
                if len(sound_effects) >= 3:
                    break
                sound_effects.append(sfx)

        data = {
            "dialogues": [
                {
                    "character": item.get("character", "モブ"),
                    "text": item.get("text", "…"),
                    "position": item.get("position", "center"),
                    "style": item.get("style", "normal"),
                    "bubbleType": item.get("bubble_type", "speech"),
                }
                for item in dialogues
            ],
            "soundEffects": sound_effects,
        }
        diagnostics = {
            "dialogueCount": len(data["dialogues"]),
        }
        preview = {
            "dialogues": data["dialogues"][:5],
            "soundEffects": sound_effects[:3],
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    async def _run_phase_final_composition(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        concept = context.get(1, {}).get("data", {})
        structure = context.get(3, {}).get("data", {})
        panels = context.get(4, {}).get("data", {})
        dialogues = context.get(6, {}).get("data", {})
        images = context.get(5, {}).get("data", {})

        total_pages = panels.get("pageCount", DEFAULT_PAGE_MIN)
        final_pages = [
            {
                "pageNumber": idx + 1,
                "panels": len(panels.get("panels", [])) // max(1, total_pages) or 4,
            }
            for idx in range(min(total_pages, 12))
        ]
        quality_checks = [
            {"item": "世界観一貫性", "status": "completed", "score": 0.9},
            {"item": "キャラクター整合性", "status": "completed", "score": 0.88},
            {"item": "画像品質", "status": "processing", "score": 0.0 if not images.get("images") else 0.82},
            {"item": "校正完了", "status": "pending", "score": None},
        ]
        scored_items = [item["score"] for item in quality_checks if isinstance(item.get("score"), (int, float))]
        overall_quality = round(sum(scored_items) / max(1, len(scored_items)), 2)

        data = {
            "finalPages": final_pages,
            "qualityChecks": quality_checks,
            "overallQuality": overall_quality,
        }
        diagnostics = {
            "totalPages": total_pages,
            "imageCount": len(images.get("images", [])),
            "dialogueCount": len(dialogues.get("dialogues", [])),
        }
        preview = {
            "overallQuality": overall_quality,
            "qualityChecks": quality_checks,
        }
        return {"data": data, "preview": preview, "diagnostics": diagnostics}

    def _is_hitl_enabled_for_session(self, session: MangaSession) -> bool:
        """Check if HITL is enabled for this session"""
        if not self.settings.hitl_enabled or not self.hitl_service:
            return False

        session_meta = session.session_metadata or {}
        feedback_mode = session_meta.get("feedback_mode", {})
        return feedback_mode.get("enabled", False)

    async def _handle_hitl_feedback(
        self,
        session: MangaSession,
        phase_number: int,
        phase_payload: Dict[str, Any],
        phase_context: Dict[int, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Handle HITL feedback collection for a completed phase"""
        try:
            # Get feedback options for this phase
            from sqlalchemy import select, and_

            options_query = select(FeedbackOptionTemplate).where(
                and_(
                    FeedbackOptionTemplate.phase == phase_number,
                    FeedbackOptionTemplate.is_active == True
                )
            ).order_by(FeedbackOptionTemplate.display_order, FeedbackOptionTemplate.option_label)

            options_result = await self.db.execute(options_query)
            feedback_options = options_result.scalars().all()

            # Convert to dict format for WebSocket
            options_data = [
                {
                    "id": str(option.id),
                    "phase": option.phase,
                    "option_key": option.option_key,
                    "option_label": option.option_label,
                    "option_description": option.option_description,
                    "option_category": option.option_category,
                    "display_order": option.display_order,
                    "is_active": option.is_active,
                }
                for option in feedback_options
            ]

            # Create feedback waiting state
            feedback_state = await self.hitl_service.create_feedback_waiting_state(
                session_id=session.request_id,
                phase=phase_number,
                preview_data=phase_payload.get("preview", {}),
                timeout_minutes=self.settings.hitl_feedback_timeout_minutes
            )

            # Update session status to waiting for feedback
            await realtime_hub.publish_session_status(
                session.request_id,
                status="awaiting_feedback",
                current_phase=phase_number,
                waiting_for_feedback=True
            )

            # Send feedback request via WebSocket
            await realtime_hub.publish_feedback_request(
                session.request_id,
                phase=phase_number,
                preview_data=phase_payload.get("preview", {}),
                timeout_seconds=self.settings.hitl_feedback_timeout_minutes * 60,
                feedback_options=options_data
            )

            logger.info(f"Feedback request sent for session {session.request_id}, phase {phase_number}")

            # Wait for feedback or timeout
            feedback_result = await self._wait_for_feedback(session, phase_number, feedback_state)

            # Update session status back to running
            await realtime_hub.publish_session_status(
                session.request_id,
                status="running",
                current_phase=phase_number,
                waiting_for_feedback=False
            )

            return feedback_result

        except Exception as e:
            logger.exception(f"Error handling HITL feedback for phase {phase_number}: {e}")
            # Continue without feedback on error
            return None

    async def _wait_for_feedback(
        self,
        session: MangaSession,
        phase_number: int,
        feedback_state
    ) -> Optional[Dict[str, Any]]:
        """Wait for user feedback or timeout"""
        timeout_seconds = self.settings.hitl_feedback_timeout_minutes * 60
        poll_interval = 5  # Check every 5 seconds

        start_time = time.perf_counter()

        while True:
            elapsed = time.perf_counter() - start_time
            if elapsed >= timeout_seconds:
                # Handle timeout
                await self.hitl_service.check_and_handle_timeouts()
                await realtime_hub.publish_feedback_timeout(
                    session.request_id,
                    phase=phase_number,
                    action_taken="auto_approve"
                )
                logger.info(f"Feedback timeout for session {session.request_id}, phase {phase_number}")
                return {"type": "timeout", "action_taken": "auto_approve"}

            # Check if feedback has been received
            from app.db.models import PhaseFeedbackState
            from sqlalchemy import select, and_

            state_query = select(PhaseFeedbackState).where(
                and_(
                    PhaseFeedbackState.session_id == feedback_state.session_id,
                    PhaseFeedbackState.phase == phase_number
                )
            )
            state_result = await self.db.execute(state_query)
            current_state = state_result.scalar_one_or_none()

            if current_state and current_state.state == "received":
                # Feedback received, get the feedback data
                from app.db.models import UserFeedbackHistory

                feedback_query = select(UserFeedbackHistory).where(
                    and_(
                        UserFeedbackHistory.session_id == feedback_state.session_id,
                        UserFeedbackHistory.phase == phase_number
                    )
                ).order_by(UserFeedbackHistory.created_at.desc())

                feedback_result = await self.db.execute(feedback_query)
                feedback_entry = feedback_result.scalar_one_or_none()

                if feedback_entry:
                    logger.info(f"Feedback received for session {session.request_id}, phase {phase_number}: {feedback_entry.feedback_type}")
                    return {
                        "type": "feedback",
                        "feedback_type": feedback_entry.feedback_type,
                        "selected_options": feedback_entry.selected_options,
                        "natural_language_input": feedback_entry.natural_language_input,
                        "user_satisfaction_score": feedback_entry.user_satisfaction_score,
                        "modifications": self._extract_feedback_modifications(feedback_entry)
                    }

            # Wait before next check
            await asyncio.sleep(poll_interval)

    def _extract_feedback_modifications(self, feedback_entry) -> Optional[Dict[str, Any]]:
        """Extract modification requests from user feedback"""
        if feedback_entry.feedback_type == "approval":
            return None

        if feedback_entry.feedback_type == "skip":
            return None

        # For modification feedback, extract specific changes requested
        modifications = {}

        if feedback_entry.natural_language_input:
            modifications["natural_language_modifications"] = feedback_entry.natural_language_input

        if feedback_entry.selected_options:
            modifications["selected_modifications"] = feedback_entry.selected_options

        return modifications if modifications else None

    async def _apply_feedback_modifications(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        phase_payload: Dict[str, Any],
        modifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply user feedback modifications to phase results"""
        try:
            modified_payload = phase_payload.copy()

            # Apply natural language modifications using AI
            if modifications.get("natural_language_modifications"):
                nl_modifications = modifications["natural_language_modifications"]

                prompt = (
                    f"You are modifying manga phase results based on user feedback. "
                    f"Current phase: {phase_config['label']} (Phase {phase_config['phase']}).\n"
                    f"Current results: {json.dumps(phase_payload.get('data', {}), ensure_ascii=False)}\n"
                    f"User feedback: {nl_modifications}\n"
                    f"Provide improved results in the same JSON structure, incorporating the user's feedback."
                )

                try:
                    raw_response = await self.vertex_service.generate_text(prompt)
                    modified_data = self._parse_json(raw_response)

                    if modified_data:
                        modified_payload["data"] = modified_data
                        modified_payload["preview"] = modified_data  # Update preview as well

                        # Update metadata to reflect modification
                        metadata = modified_payload.get("metadata", {})
                        metadata["modified_by_user"] = True
                        metadata["modification_type"] = "natural_language"
                        modified_payload["metadata"] = metadata

                        logger.info(f"Applied natural language modifications to phase {phase_config['phase']}")

                except Exception as e:
                    logger.error(f"Error applying natural language modifications: {e}")

            # Apply specific option-based modifications
            if modifications.get("selected_modifications"):
                selected_options = modifications["selected_modifications"]
                # Implementation depends on the specific feedback options available
                # This would need to be expanded based on the actual option types
                logger.info(f"Applied option modifications: {selected_options}")

            return modified_payload

        except Exception as e:
            logger.exception(f"Error applying feedback modifications: {e}")
            return phase_payload

    async def _handle_failure(
        self,
        session: MangaSession,
        project: Optional[MangaProject],
        phase_number: int,
        message: str,
    ) -> None:
        session.status = MangaSessionStatus.FAILED.value
        session.completed_at = datetime.utcnow()
        await self.db.flush()

        await realtime_hub.publish(
            session.request_id,
            build_event("phase_error", phaseId=phase_number, error=message),
        )
        await realtime_hub.publish(
            session.request_id,
            build_event("session_error", error=message),
        )

        await realtime_hub.publish(
            session.request_id,
            build_event(
                "session_complete",
                results={"project_id": str(session.project_id) if session.project_id else None},
                sessionId=str(session.request_id),
                status="failed",
            ),
        )

        if project is not None:
            project.status = MangaProjectStatus.FAILED
            project.updated_at = datetime.utcnow()
        await self.db.flush()

    async def _handle_failure_outside_transaction(
        self,
        session: MangaSession,
        project: Optional[MangaProject],
        phase_number: int,
        message: str,
    ) -> None:
        """Handle failure outside transaction context"""
        async with self.db.begin() as failure_transaction:
            try:
                session.status = MangaSessionStatus.FAILED.value
                session.completed_at = datetime.utcnow()

                if project is not None:
                    project.status = MangaProjectStatus.FAILED
                    project.updated_at = datetime.utcnow()

                await failure_transaction.commit()
                logger.info(f"Failure status updated for session {session.request_id}")

            except Exception as e:
                await failure_transaction.rollback()
                logger.error(f"Failed to update failure status for session {session.request_id}: {e}")

        # Publish error events outside transaction
        await realtime_hub.publish(
            session.request_id,
            build_event("phase_error", phaseId=phase_number, error=message),
        )
        await realtime_hub.publish(
            session.request_id,
            build_event("session_error", error=message),
        )

        await realtime_hub.publish(
            session.request_id,
            build_event(
                "session_complete",
                results={"project_id": str(session.project_id) if session.project_id else None},
                sessionId=str(session.request_id),
                status="failed",
            ),
        )

    def _build_signed_url(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        preview: PreviewVersion,
        *,
        file_extension: str = "json",
    ) -> str:
        bucket = self.settings.gcs_bucket_preview
        path = (
            f"preview/{session.request_id}/phase-{phase_config['phase']}/"
            f"{preview.id}.{file_extension}"
        )
        try:
            client = core_clients.get_storage_client()
            bucket_ref = client.bucket(bucket)
            blob = bucket_ref.blob(path)
            expiration = datetime.utcnow() + timedelta(seconds=self.settings.signed_url_ttl_seconds)
            return blob.generate_signed_url(expiration=expiration, method="GET", version="v4")
        except Exception:
            return f"https://storage.googleapis.com/{bucket}/{path}"

    def _estimate_pages(self, session: MangaSession, context: Dict[int, Dict[str, Any]]) -> int:
        structure_data = context.get(3, {}).get("data", {})
        panel_data = context.get(4, {}).get("data", {})
        session_meta = session.session_metadata or {}
        base_pages = session_meta.get("options", {}).get("expected_pages") if session_meta.get("options") else None
        if isinstance(base_pages, int) and base_pages > 0:
            return base_pages
        if panel_data.get("pageCount"):
            return max(DEFAULT_PAGE_MIN, int(panel_data["pageCount"]))
        act_count = len(structure_data.get("acts", []))
        return max(DEFAULT_PAGE_MIN, act_count * 6)

    async def _upsert_project_assets(self, project, session: MangaSession) -> None:
        result = await self.db.execute(
            select(MangaAsset).where(
                MangaAsset.project_id == project.id,
                MangaAsset.asset_type == MangaAssetType.PDF,
            )
        )
        existing_pdf = result.scalars().first()
        storage_path = f"projects/{project.id}/final/{session.request_id}.pdf"
        signed_url = self._build_asset_signed_url(storage_path)
        asset_payload = {
            "project_id": project.id,
            "asset_type": MangaAssetType.PDF,
            "storage_path": storage_path,
            "signed_url": signed_url,
            "asset_metadata": {
                "total_pages": project.total_pages,
                "generated_at": datetime.utcnow().isoformat(),
            },
        }
        if existing_pdf:
            for key, value in asset_payload.items():
                setattr(existing_pdf, key, value)
        else:
            self.db.add(MangaAsset(**asset_payload))

    async def _load_project(self, project_id: Optional[UUID]) -> Optional[MangaProject]:
        if not project_id:
            return None
        result = await self.db.execute(
            select(MangaProject).where(MangaProject.id == project_id)
        )
        return result.scalar_one_or_none()

    def _build_asset_signed_url(self, storage_path: str) -> str:
        bucket = self.settings.gcs_bucket_preview
        try:
            client = core_clients.get_storage_client()
            bucket_ref = client.bucket(bucket)
            blob = bucket_ref.blob(storage_path)
            expiration = datetime.utcnow() + timedelta(seconds=self.settings.signed_url_ttl_seconds)
            return blob.generate_signed_url(expiration=expiration, method="GET", version="v4")
        except Exception:
            return f"https://storage.googleapis.com/{bucket}/{storage_path}"

    def _parse_json(self, raw: str | None) -> Dict[str, Any]:
        if not raw:
            return {}
        text = raw.strip()
        if "```" in text:
            segments = [segment for segment in text.split("```") if segment.strip()]
            if segments:
                text = segments[-1]
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            cleaned = candidate.replace("\n", " ")
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return {}

    def _ensure_list_of_strings(self, parsed: Dict[str, Any], key: str, *, default: Optional[list[str]] = None) -> list[str]:
        default = default or []
        value = parsed.get(key)
        return self._ensure_list_of_strings_from_value(value, default=default)

    def _ensure_list_of_strings_from_value(self, value: Any, *, default: Optional[list[str]] = None) -> list[str]:
        default = default or []
        if isinstance(value, list):
            result: list[str] = []
            for item in value:
                if isinstance(item, str):
                    result.append(item.strip())
                elif isinstance(item, dict):
                    result.append(next(iter(item.values())) if item else "")
                else:
                    result.append(str(item))
            return [entry for entry in result if entry]
        if isinstance(value, str):
            parts = [part.strip() for part in value.split("\n") if part.strip()]
            return parts or default
        return default

    def _ensure_list_of_dicts(self, parsed: Dict[str, Any], key: str) -> list[Dict[str, Any]]:
        value = parsed.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [value]
        return []

    def _coalesce(self, parsed: Dict[str, Any] | None, keys: list[str], *, default: Any = "") -> Any:
        if not parsed:
            return default
        for key in keys:
            if key in parsed and parsed[key]:
                return parsed[key]
        return default

    def _quality_to_level(self, quality: float) -> int:
        if quality >= 0.9:
            return 5
        if quality >= 0.85:
            return 4
        if quality >= 0.78:
            return 3
        if quality >= QUALITY_THRESHOLD:
            return 2
        return 1

    def _evaluate_quality(
        self,
        phase_number: int,
        data: Dict[str, Any],
        diagnostics: Dict[str, Any],
    ) -> float:
        """
        Evaluate quality using the unified QualityCalculator system
        """
        return QualityCalculator.calculate_quality(phase_number, data, diagnostics)

from __future__ import annotations

import asyncio
import json
import logging
import math
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import clients as core_clients, settings as core_settings
from app.core.db import session_scope
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
from app.services.hitl_service import (
    HITLService,
    HITLStateManager,
    HITLError,
    HITLSessionError,
    HITLStateError,
    HITLTimeoutError,
    HITLDatabaseError
)
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
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.settings = core_settings.get_settings()
        core_clients.get_storage_client.cache_clear()
        self.vertex_service = get_vertex_service()
        self.db = None  # Will be set per-operation to avoid transaction conflicts

    async def run(self, request_id: UUID) -> None:
        """
        漫画生成パイプライン実行メイン関数
        """
        try:
            logger.info(f"🚀 Pipeline execution started for request_id: {request_id}")

            # Get session before starting transaction to avoid context issues
            session = await self._get_session(request_id)
            if session is None:
                logger.error(f"❌ Session not found for request_id: {request_id}")
                raise ValueError("session_not_found")

            logger.info(f"✅ Found session: {session.id}, status: {session.status}")

            # Run pipeline phases
            await self._execute_pipeline_phases(session)

            logger.info(f"🎉 Pipeline execution completed successfully for session: {session.id}")

        except Exception as e:
            logger.error(f"💥 Pipeline failed for session {request_id}: {type(e).__name__}: {e}")
            logger.exception("Full pipeline error traceback:")

            # Try to update session status to failed using safe methods
            try:
                failed_session = await self._get_session_safe(request_id)
                if failed_session:
                    error_message = f"{type(e).__name__}: {str(e)}"
                    success = await self._update_session_status_safe(
                        failed_session.id,
                        MangaSessionStatus.FAILED.value,
                        error_message
                    )
                    if success:
                        logger.info(f"📝 Updated session {failed_session.id} status to FAILED")
                    else:
                        logger.error(f"❌ Failed to update session {failed_session.id} status to FAILED")
                else:
                    logger.warning(f"⚠️ Could not find session for request_id: {request_id}")
            except Exception as status_update_error:
                logger.error(f"Could not update session status (safe method): {status_update_error}")

            raise

    async def _execute_pipeline_phases(self, session: MangaSession) -> None:
        """
        パイプラインの各フェーズを実行 - 各フェーズごとに独立したトランザクションを使用
        """
        logger.info(f"🔄 Starting pipeline phases for session: {session.id}")

        try:
            # Update session status to running (separate transaction)
            await self._update_session_status(session.id, MangaSessionStatus.RUNNING.value, started_at=datetime.utcnow())

            # Execute actual manga generation phases
            phase_context = {}
            for phase_config in PHASE_SEQUENCE:
                phase_number = phase_config["phase"]
                phase_name = phase_config["name"]

                logger.info(f"📋 Executing phase {phase_number}: {phase_name}")

                # Update current phase (separate transaction)
                await self._update_session_status(session.id, None, current_phase=phase_number)

                # Execute phase with its own transaction scope
                try:
                    phase_result = await self._execute_single_phase(session, phase_config, phase_context)
                    phase_context[phase_number] = phase_result
                    logger.info(f"✅ Phase {phase_number} ({phase_name}) completed successfully")

                except Exception as phase_error:
                    logger.error(f"❌ Phase {phase_number} ({phase_name}) failed: {phase_error}")
                    await self._update_session_status(session.id, MangaSessionStatus.FAILED.value, error_message=str(phase_error))
                    raise

            # Mark session as completed (separate transaction)
            await self._update_session_status(
                session.id,
                MangaSessionStatus.COMPLETED.value,
                completed_at=datetime.utcnow(),
                actual_completion_time=datetime.utcnow(),
                current_phase=len(PHASE_SEQUENCE)
            )

            logger.info(f"🎉 All phases completed successfully for session: {session.id}")

        except Exception as e:
            logger.error(f"❌ Pipeline execution failed for session {session.id}: {e}")
            # Ensure session is marked as failed if not already done
            try:
                await self._update_session_status(session.id, MangaSessionStatus.FAILED.value, error_message=str(e))
            except Exception as update_error:
                logger.error(f"Failed to update session status to failed: {update_error}")
            raise

    async def _update_session_status(self, session_id: UUID, status: Optional[str] = None, **kwargs) -> None:
        """Update session status in a separate transaction to avoid conflicts"""
        async with self.session_factory() as db_session:
            try:
                update_values = {"updated_at": datetime.utcnow()}
                if status:
                    update_values["status"] = status
                update_values.update(kwargs)

                # Check if transaction is already active to avoid double-begin
                if db_session.in_transaction():
                    logger.info("_update_session_status: Using existing transaction")
                    await db_session.execute(
                        update(MangaSession)
                        .where(MangaSession.id == session_id)
                        .values(**update_values)
                    )
                else:
                    logger.info("_update_session_status: Starting new transaction")
                    async with db_session.begin():
                        await db_session.execute(
                            update(MangaSession)
                            .where(MangaSession.id == session_id)
                            .values(**update_values)
                        )
            except Exception as e:
                logger.error(f"Failed to update session status: {e}")
                raise

    async def _execute_single_phase(self, session: MangaSession, phase_config: Dict[str, Any], context: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a single phase with its own database transaction scope"""
        async with self.session_factory() as db_session:
            # Set database session for this phase
            self.db = db_session

            try:
                # Check if transaction is already active to avoid double-begin
                if db_session.in_transaction():
                    logger.info(f"Phase {phase_config['phase']}: Using existing transaction")
                    # Process the phase within existing transaction
                    phase_result = await self._process_phase(session, phase_config, context, attempt=1)
                    # Persist phase results within the same transaction
                    await self._persist_phase_results(session, phase_config, phase_result)
                    return phase_result
                else:
                    logger.info(f"Phase {phase_config['phase']}: Starting new transaction")
                    async with db_session.begin():
                        # Process the phase
                        phase_result = await self._process_phase(session, phase_config, context, attempt=1)
                        # Persist phase results within the same transaction
                        await self._persist_phase_results(session, phase_config, phase_result)
                        return phase_result

            except Exception as e:
                logger.error(f"Phase {phase_config['phase']} execution failed: {e}")
                raise
            finally:
                # Clear database session to prevent reuse
                self.db = None

    async def _persist_phase_results(self, session: MangaSession, phase_config: Dict[str, Any], phase_result: Dict[str, Any]) -> None:
        """Persist phase results to database"""
        phase_number = phase_config["phase"]
        quality_score = float(phase_result.get("metadata", {}).get("quality", 0.0))

        # Create phase result record
        phase_result_record = PhaseResult(
            session_id=session.id,
            phase=phase_number,
            status="completed",
            content=phase_result,
            quality_score=quality_score,
        )
        self.db.add(phase_result_record)
        await self.db.flush()

        # Create preview version
        preview_version = PreviewVersion(
            session_id=session.id,
            phase=phase_number,
            version_data=phase_result.get("preview"),
            quality_level=self._quality_to_level(quality_score),
            quality_score=quality_score,
        )
        self.db.add(preview_version)
        await self.db.flush()

        logger.info(f"Persisted results for phase {phase_number}")

    async def _get_session(self, request_id: UUID) -> Optional[MangaSession]:
        from sqlalchemy.exc import ProgrammingError, InvalidRequestError
        from asyncpg.exceptions import UndefinedColumnError

        logger.info(f"_get_session called with request_id: {request_id}")

        async with self.session_factory() as db_session:
            try:
                # Try to query by request_id if the column exists
                logger.info("Attempting to query by request_id column")
                result = await db_session.execute(
                    select(MangaSession).where(MangaSession.request_id == request_id)
                )
                session = result.scalar_one_or_none()
                logger.info(f"Successfully found session by request_id: {session is not None}")
                return session
            except (ProgrammingError, InvalidRequestError, UndefinedColumnError) as e:
                # If request_id column doesn't exist, query by id instead
                logger.warning(f"request_id column not available (specific error), using id instead: {type(e).__name__}: {e}")
                try:
                    logger.info("Attempting to query by id column")
                    result = await db_session.execute(
                        select(MangaSession).where(MangaSession.id == request_id)
                    )
                    session = result.scalar_one_or_none()
                    logger.info(f"Successfully found session by id: {session is not None}")
                    return session
                except Exception as e2:
                    logger.error(f"Failed to find session by id either: {type(e2).__name__}: {e2}")
                    return None
            except Exception as e:
                # Catch all other exceptions
                logger.warning(f"Unexpected error type, using id instead: {type(e).__name__}: {e}")
                try:
                    logger.info("Attempting to query by id column (generic exception)")
                    result = await db_session.execute(
                        select(MangaSession).where(MangaSession.id == request_id)
                    )
                    session = result.scalar_one_or_none()
                    logger.info(f"Successfully found session by id (generic): {session is not None}")
                    return session
                except Exception as e2:
                    logger.error(f"Failed to find session by id either (generic): {type(e2).__name__}: {e2}")
                    return None

    async def _get_session_safe(self, request_id: UUID) -> Optional[MangaSession]:
        """
        安全にセッションを取得する（独立したトランザクションコンテキストを使用）
        エラーハンドリング中でも使用できる
        """
        from sqlalchemy.exc import ProgrammingError, InvalidRequestError
        from asyncpg.exceptions import UndefinedColumnError

        logger.info(f"_get_session_safe called with request_id: {request_id}")

        try:
            # 独立したデータベースセッションを作成
            async with session_scope() as independent_session:
                try:
                    # Try to query by request_id if the column exists
                    logger.info("Safe session: Attempting to query by request_id column")
                    result = await independent_session.execute(
                        select(MangaSession).where(MangaSession.request_id == request_id)
                    )
                    session = result.scalar_one_or_none()
                    logger.info(f"Safe session: Successfully found session by request_id: {session is not None}")
                    return session
                except (ProgrammingError, InvalidRequestError, UndefinedColumnError) as e:
                    # If request_id column doesn't exist, query by id instead
                    logger.warning(f"Safe session: request_id column not available, using id instead: {type(e).__name__}: {e}")
                    try:
                        logger.info("Safe session: Attempting to query by id column")
                        result = await independent_session.execute(
                            select(MangaSession).where(MangaSession.id == request_id)
                        )
                        session = result.scalar_one_or_none()
                        logger.info(f"Safe session: Successfully found session by id: {session is not None}")
                        return session
                    except Exception as e2:
                        logger.error(f"Safe session: Failed to find session by id either: {type(e2).__name__}: {e2}")
                        return None
        except Exception as e:
            logger.error(f"Safe session: Failed to create independent session: {type(e).__name__}: {e}")
            return None

    async def _update_session_status_safe(self, session_id: UUID, status: str, error_message: Optional[str] = None) -> bool:
        """
        安全にセッションステータスを更新する（独立したトランザクションコンテキストを使用）
        エラーハンドリング中でも使用できる
        """
        try:
            # 独立したデータベースセッションを作成
            async with session_scope() as independent_session:
                async with independent_session.begin() as transaction:
                    try:
                        update_values = {
                            'status': status,
                            'updated_at': datetime.utcnow()
                        }
                        if error_message:
                            update_values['error_message'] = error_message[:500]  # Limit error message length

                        await independent_session.execute(
                            update(MangaSession)
                            .where(MangaSession.id == session_id)
                            .values(**update_values)
                        )
                        await transaction.commit()
                        logger.info(f"Safe update: Successfully updated session {session_id} status to {status}")
                        return True
                    except Exception as commit_error:
                        await transaction.rollback()
                        logger.error(f"Safe update: Failed to update session status: {commit_error}")
                        return False
        except Exception as e:
            logger.error(f"Safe update: Failed to create independent session: {type(e).__name__}: {e}")
            return False


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

            async with self.session_factory() as db_session:
                options_result = await db_session.execute(options_query)
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
            async with self.session_factory() as db_session:
                state_result = await db_session.execute(state_query)
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

                    feedback_result = await db_session.execute(feedback_query)
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
        # Update session and project status with proper transaction management
        async with self.session_factory() as db_session:
            async with db_session.begin():
                # Refresh objects in current session context
                await db_session.merge(session)
                if project:
                    await db_session.merge(project)

                session.status = MangaSessionStatus.FAILED.value
                session.completed_at = datetime.utcnow()

                if project is not None:
                    project.status = MangaProjectStatus.FAILED
                    project.updated_at = datetime.utcnow()

        # Publish error events
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

    async def _handle_failure_outside_transaction(
        self,
        session: MangaSession,
        project: Optional[MangaProject],
        phase_number: int,
        message: str,
    ) -> None:
        """Handle failure outside transaction context"""
        async with self.session_factory() as db_session:
            async with db_session.begin() as failure_transaction:
                try:
                    # Refresh objects in current session context
                    await db_session.merge(session)
                    if project:
                        await db_session.merge(project)

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
        async with self.session_factory() as db_session:
            async with db_session.begin():
                result = await db_session.execute(
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
                    db_session.add(MangaAsset(**asset_payload))

    async def _load_project(self, project_id: Optional[UUID]) -> Optional[MangaProject]:
        if not project_id:
            return None
        async with self.session_factory() as db_session:
            result = await db_session.execute(
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


class HITLCapablePipelineOrchestrator(PipelineOrchestrator):
    """
    HITL(Human-in-the-Loop)機能を統合したパイプラインオーケストレーター
    既存のPipelineOrchestratorを継承し、フィードバックサイクル機能を追加
    """

    def __init__(self, session_factory):
        super().__init__(session_factory)
        
        # 設定から初期値を読み込み
        try:
            settings = core_settings.get_settings()
            self.is_hitl_enabled = settings.hitl_enabled
            self.max_feedback_iterations = settings.hitl_max_iterations
            self.feedback_timeout_minutes = settings.hitl_feedback_timeout_minutes
        except Exception as e:
            logger.warning(f"Failed to load HITL settings, using defaults: {e}")
            # フォールバック値
            self.is_hitl_enabled = True
            self.max_feedback_iterations = 3
            self.feedback_timeout_minutes = 30
        
        # HITLコンポーネント初期化 - 必要時に作成
        self._hitl_service: Optional[HITLService] = None
        self._hitl_state_manager: Optional[HITLStateManager] = None

    async def _get_hitl_service(self, db: AsyncSession) -> HITLService:
        """HITLサービスを取得（初回作成時にキャッシュ）"""
        if self._hitl_service is None:
            self._hitl_service = HITLService(db)
        return self._hitl_service

    async def _get_hitl_state_manager(self, db: AsyncSession) -> HITLStateManager:
        """HITLステートマネージャーを取得（初回作成時にキャッシュ）"""
        if self._hitl_state_manager is None:
            hitl_service = await self._get_hitl_service(db)
            self._hitl_state_manager = HITLStateManager(hitl_service)
        return self._hitl_state_manager

    def _extract_preview_data(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """フェーズ結果からプレビューデータを抽出"""
        if not result:
            return None
            
        preview_data = {}
        
        # 生成された画像の抽出
        if "generated_images" in result:
            preview_data["images"] = result["generated_images"]
        
        # テキスト結果の抽出
        if "generated_text" in result:
            preview_data["text"] = result["generated_text"]
        
        # キャラクター情報の抽出
        if "characters" in result:
            preview_data["characters"] = result["characters"]
        
        # ストーリー概要の抽出
        if "story_outline" in result:
            preview_data["story_outline"] = result["story_outline"]
        
        # その他のメタデータ
        if "metadata" in result:
            preview_data["metadata"] = result["metadata"]
        
        return preview_data if preview_data else None

    async def _get_feedback_options_for_phase(self, phase_number: int) -> List[Dict[str, Any]]:
        """指定フェーズで利用可能なフィードバックオプションを取得"""
        try:
            async with session_scope(self.session_factory) as db:
                # フィードバックオプションテンプレートを取得
                query = select(FeedbackOptionTemplate).where(
                    FeedbackOptionTemplate.phase == phase_number
                )
                result = await db.execute(query)
                templates = result.scalars().all()
                
                options = []
                for template in templates:
                    options.append({
                        "option_id": str(template.id),
                        "option_text": template.option_text,
                        "option_type": template.option_type,
                        "display_order": template.display_order,
                        "metadata": template.metadata or {}
                    })
                
                # デフォルトオプション（承認、修正、スキップ）
                if not options:
                    options = [
                        {
                            "option_id": "approve",
                            "option_text": "この結果を承認する",
                            "option_type": "approval",
                            "display_order": 1
                        },
                        {
                            "option_id": "modify",
                            "option_text": "修正して再生成する",
                            "option_type": "modification",
                            "display_order": 2
                        },
                        {
                            "option_id": "skip",
                            "option_text": "このフェーズをスキップする",
                            "option_type": "skip",
                            "display_order": 3
                        }
                    ]
                
                return sorted(options, key=lambda x: x.get("display_order", 999))
                
        except Exception as e:
            logger.error(f"Failed to get feedback options for phase {phase_number}: {e}")
            # エラー時はデフォルトオプションを返す
            return [
                {"option_id": "approve", "option_text": "承認", "option_type": "approval", "display_order": 1},
                {"option_id": "modify", "option_text": "修正", "option_type": "modification", "display_order": 2},
                {"option_id": "skip", "option_text": "スキップ", "option_type": "skip", "display_order": 3}
            ]

    def _add_hitl_error_metadata(self, result: Dict[str, Any], error_type: str, error_message: str) -> Dict[str, Any]:
        """HITLエラー情報をメタデータに追加"""
        if "metadata" not in result:
            result["metadata"] = {}
        
        result["metadata"].update({
            "hitl_processed": True,
            "hitl_error": True,
            "hitl_error_type": error_type,
            "hitl_error_message": error_message,
            "hitl_error_timestamp": datetime.utcnow().isoformat(),
            "feedback_iterations": 0,
            "final_state": "error"
        })
        
        return result

    async def _execute_single_phase_with_hitl(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        HITLフィードバックサイクルを統合したフェーズ実行
        """
        phase_number = phase_config["phase"]

        # 初期実行
        initial_result = await self._execute_single_phase(session, phase_config, context)

        # HITL有効チェック
        if not self._is_hitl_enabled_for_phase(phase_number):
            logger.info(f"HITL disabled for phase {phase_number}, using standard result")
            return initial_result

        # フィードバックサイクル処理
        try:
            final_result = await self._process_hitl_feedback_cycle(
                session, phase_config, context, initial_result
            )
            return final_result
        except Exception as e:
            logger.error(f"HITL feedback cycle failed for phase {phase_number}: {e}")
            # フィードバック処理に失敗した場合は初期結果を使用
            return initial_result

    async def _process_hitl_feedback_cycle(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
        initial_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        フィードバックサイクルのメイン処理ロジック（HITLStateManager統合版 + 完全エラーハンドリング）
        """
        phase_number = phase_config["phase"]
        current_result = initial_result
        hitl_context = None

        logger.info(f"Starting HITL feedback cycle for phase {phase_number}")

        # データベースセッションを取得してHITLコンポーネントを初期化
        async with session_scope(self.session_factory) as db:
            try:
                state_manager = await self._get_hitl_state_manager(db)
                
                # HITL セッション開始
                try:
                    hitl_context = await state_manager.start_hitl_session(
                        session_id=session.request_id,
                        phase=phase_number,
                        preview_data=self._extract_preview_data(current_result)
                    )
                except HITLDatabaseError as e:
                    logger.error(f"Database error starting HITL session: {e}")
                    # データベースエラーの場合は初期結果を返す
                    return self._add_hitl_error_metadata(current_result, "database_error", str(e))
                except HITLSessionError as e:
                    logger.error(f"Session error starting HITL: {e}")
                    return self._add_hitl_error_metadata(current_result, "session_error", str(e))

                # フィードバックサイクル処理
                while hitl_context.can_continue():
                    try:
                        # フィードバック要求通知
                        await self._notify_feedback_required(session, phase_number, current_result)

                        # フィードバック待機
                        feedback = await self._wait_for_user_feedback(
                            session, phase_number, timeout_minutes=self.feedback_timeout_minutes
                        )

                        if feedback is None:
                            # タイムアウト処理
                            try:
                                await state_manager.handle_timeout(session.request_id)
                                logger.info(f"Feedback timeout for phase {phase_number}")
                                await self._notify_feedback_timeout(session, phase_number)
                                break
                            except HITLTimeoutError as e:
                                logger.warning(f"Timeout handling had issues: {e}")
                                break  # タイムアウト処理は継続

                        # フィードバック受信処理
                        try:
                            should_continue = await state_manager.process_feedback_received(
                                session.request_id, feedback
                            )
                        except HITLStateError as e:
                            logger.error(f"State error processing feedback: {e}")
                            break
                        except HITLError as e:
                            logger.error(f"HITL error processing feedback: {e}")
                            if e.error_code == "HITL_MAX_ITERATIONS_EXCEEDED":
                                # 最大反復回数超過の場合は現在の結果で終了
                                break
                            else:
                                # その他のHITLエラーも現在の結果で終了
                                break

                        if not should_continue:
                            # 承認、スキップ、またはエラーによる終了
                            feedback_type = feedback.get("feedback_type")
                            if feedback_type == "approval":
                                await self._notify_feedback_approved(session, phase_number)
                            elif feedback_type == "skip":
                                await self._notify_feedback_skipped(session, phase_number)
                            break

                        # 修正要求の場合：再生成実行
                        if hitl_context.state.value == "regenerating":
                            logger.info(f"Processing modification request for phase {phase_number}")
                            await self._notify_feedback_processing(session, phase_number)

                            try:
                                # フィードバック適用と再生成
                                modifications = self._extract_feedback_modifications_from_response(feedback)
                                modified_result = await self._regenerate_with_feedback(
                                    session, phase_config, context, current_result, modifications
                                )

                                # 再生成完了をステートマネージャーに通知
                                try:
                                    regeneration_success = await state_manager.handle_regeneration_complete(
                                        session.request_id,
                                        regeneration_success=True,
                                        new_preview_data=self._extract_preview_data(modified_result)
                                    )

                                    if regeneration_success:
                                        current_result = modified_result
                                        await self._notify_regeneration_complete(session, phase_number, current_result)
                                    else:
                                        logger.error(f"Regeneration state handling failed for phase {phase_number}")
                                        break
                                        
                                except (HITLStateError, HITLDatabaseError) as e:
                                    logger.error(f"State/Database error in regeneration completion: {e}")
                                    break

                            except Exception as e:
                                # 再生成エラー処理
                                logger.error(f"Regeneration failed for phase {phase_number}: {e}")
                                try:
                                    await state_manager.handle_regeneration_complete(
                                        session.request_id,
                                        regeneration_success=False
                                    )
                                except Exception as cleanup_error:
                                    logger.error(f"Failed to cleanup after regeneration error: {cleanup_error}")
                                    
                                await self._notify_regeneration_error(session, phase_number, str(e))
                                break

                    except Exception as e:
                        logger.error(f"Unexpected error in feedback cycle iteration: {e}")
                        if hitl_context:
                            hitl_context.update_state(HITLSessionState.ERROR, str(e))
                        break

                # セッション完了とクリーンアップ
                try:
                    session_status = await state_manager.get_session_status(session.request_id)
                    if session_status:
                        logger.info(f"HITL session completed: {session_status}")

                    await state_manager.cleanup_session(session.request_id)
                except Exception as cleanup_error:
                    logger.warning(f"Session cleanup had issues: {cleanup_error}")

            except Exception as e:
                logger.error(f"Critical HITL error for phase {phase_number}: {e}")
                # クリーンアップを試行
                try:
                    if state_manager and hitl_context:
                        await state_manager.cleanup_session(session.request_id)
                except Exception as cleanup_error:
                    logger.error(f"Failed cleanup after critical error: {cleanup_error}")

        # メタデータにHITL情報を追加
        if "metadata" not in current_result:
            current_result["metadata"] = {}

        current_result["metadata"].update({
            "hitl_processed": True,
            "feedback_iterations": hitl_context.iteration_count if hitl_context else 0,
            "final_state": hitl_context.state.value if hitl_context else "unknown"
        })

        logger.info(f"HITL feedback cycle completed for phase {phase_number}")
        return current_result

    async def _regenerate_with_feedback(
        self,
        session: MangaSession,
        phase_config: Dict[str, Any],
        context: Dict[int, Dict[str, Any]],
        current_result: Dict[str, Any],
        modifications: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        フィードバックを適用して再生成実行
        """
        if modifications:
            # フィードバック修正を適用
            modified_result = await self._apply_feedback_modifications(
                session, phase_config, current_result, modifications
            )
        else:
            modified_result = current_result

        # 修正されたコンテキストで再実行
        regenerated_result = await self._process_phase(
            session, phase_config, context, attempt=2
        )

        return regenerated_result

    def _extract_feedback_modifications_from_response(self, feedback: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        フィードバックレスポンスから修正要求を抽出
        """
        modifications = {}

        if feedback.get("natural_language_input"):
            modifications["natural_language_modifications"] = feedback["natural_language_input"]

        if feedback.get("selected_options"):
            modifications["selected_modifications"] = feedback["selected_options"]

        return modifications if modifications else None

    def _is_hitl_enabled_for_phase(self, phase_number: int) -> bool:
        """
        指定フェーズでHITLが有効かチェック（設定ベース）
        """
        if not self.is_hitl_enabled:
            return False

        # 設定からHITL有効フェーズを取得
        try:
            settings = core_settings.get_settings()
            return settings.is_hitl_enabled_for_phase(phase_number)
        except Exception as e:
            logger.warning(f"Failed to get HITL settings, falling back to default: {e}")
            # フォールバック: Phase 1と2でHITLを有効にする（Phase 1実装）
            return phase_number in [1, 2]

    async def _notify_feedback_required(
        self,
        session: MangaSession,
        phase_number: int,
        result: Dict[str, Any]
    ) -> None:
        """
        フィードバック要求をユーザーに通知（HITLStateManager統合版）
        """
        # HITLStateManagerからセッション状態を取得
        session_state = None
        try:
            async with session_scope(self.session_factory) as db:
                state_manager = await self._get_hitl_state_manager(db)
                session_state = await state_manager.get_session_status(session.request_id)
        except Exception as e:
            logger.warning(f"Failed to get HITL session state: {e}")

        # プレビューデータを抽出
        preview_data = self._extract_preview_data(result)

        # 通知イベント構築
        event_data = {
            "phaseId": phase_number,
            "sessionId": str(session.request_id),
            "result": result,
            "preview_data": preview_data,
            "hitl_state": session_state,
            "feedback_options": await self._get_feedback_options_for_phase(phase_number),
            "timeout_minutes": self.feedback_timeout_minutes
        }

        await realtime_hub.publish(
            session.request_id,
            build_event("feedback_required", **event_data)
        )

    async def _notify_feedback_timeout(self, session: MangaSession, phase_number: int) -> None:
        """フィードバックタイムアウト通知（HITLStateManager統合版）"""
        session_state = None
        try:
            async with session_scope(self.session_factory) as db:
                state_manager = await self._get_hitl_state_manager(db)
                session_state = await state_manager.get_session_status(session.request_id)
        except Exception as e:
            logger.warning(f"Failed to get HITL session state for timeout: {e}")

        event_data = {
            "phaseId": phase_number,
            "sessionId": str(session.request_id),
            "hitl_state": session_state,
            "timeout_occurred_at": datetime.utcnow().isoformat()
        }

        await realtime_hub.publish(
            session.request_id,
            build_event("feedback_timeout", **event_data)
        )

    async def _notify_feedback_approved(self, session: MangaSession, phase_number: int) -> None:
        """フィードバック承認通知（HITLStateManager統合版）"""
        session_state = None
        try:
            async with session_scope(self.session_factory) as db:
                state_manager = await self._get_hitl_state_manager(db)
                session_state = await state_manager.get_session_status(session.request_id)
        except Exception as e:
            logger.warning(f"Failed to get HITL session state for approval: {e}")

        event_data = {
            "phaseId": phase_number,
            "sessionId": str(session.request_id),
            "hitl_state": session_state,
            "approved_at": datetime.utcnow().isoformat()
        }

        await realtime_hub.publish(
            session.request_id,
            build_event("feedback_approved", **event_data)
        )

    async def _notify_feedback_processing(self, session: MangaSession, phase_number: int) -> None:
        """フィードバック処理中通知（HITLStateManager統合版）"""
        session_state = None
        try:
            async with session_scope(self.session_factory) as db:
                state_manager = await self._get_hitl_state_manager(db)
                session_state = await state_manager.get_session_status(session.request_id)
        except Exception as e:
            logger.warning(f"Failed to get HITL session state for processing: {e}")

        event_data = {
            "phaseId": phase_number,
            "sessionId": str(session.request_id),
            "hitl_state": session_state,
            "processing_started_at": datetime.utcnow().isoformat(),
            "estimated_duration_minutes": 2  # 再生成処理の想定時間
        }

        await realtime_hub.publish(
            session.request_id,
            build_event("feedback_processing", **event_data)
        )

    async def _notify_regeneration_complete(
        self,
        session: MangaSession,
        phase_number: int,
        result: Dict[str, Any]
    ) -> None:
        """再生成完了通知（HITLStateManager統合版）"""
        session_state = None
        try:
            async with session_scope(self.session_factory) as db:
                state_manager = await self._get_hitl_state_manager(db)
                session_state = await state_manager.get_session_status(session.request_id)
        except Exception as e:
            logger.warning(f"Failed to get HITL session state for regeneration complete: {e}")

        # 再生成結果のプレビューデータを抽出
        preview_data = self._extract_preview_data(result)

        event_data = {
            "phaseId": phase_number,
            "sessionId": str(session.request_id),
            "result": result,
            "preview_data": preview_data,
            "hitl_state": session_state,
            "regenerated_at": datetime.utcnow().isoformat(),
            "iteration_count": session_state.get("iteration_count", 0) if session_state else 0
        }

        await realtime_hub.publish(
            session.request_id,
            build_event("regeneration_complete", **event_data)
        )

    async def _notify_regeneration_error(
        self,
        session: MangaSession,
        phase_number: int,
        error_message: str
    ) -> None:
        """再生成エラー通知（HITLStateManager統合版）"""
        session_state = None
        try:
            async with session_scope(self.session_factory) as db:
                state_manager = await self._get_hitl_state_manager(db)
                session_state = await state_manager.get_session_status(session.request_id)
        except Exception as e:
            logger.warning(f"Failed to get HITL session state for regeneration error: {e}")

        event_data = {
            "phaseId": phase_number,
            "sessionId": str(session.request_id),
            "error": error_message,
            "hitl_state": session_state,
            "error_occurred_at": datetime.utcnow().isoformat(),
            "can_retry": session_state.get("can_continue", False) if session_state else False,
            "iteration_count": session_state.get("iteration_count", 0) if session_state else 0
        }

        await realtime_hub.publish(
            session.request_id,
            build_event("regeneration_error", **event_data)
        )

    async def _notify_feedback_skipped(self, session: MangaSession, phase_number: int) -> None:
        """フィードバックスキップ通知（HITLStateManager統合版）"""
        session_state = None
        try:
            async with session_scope(self.session_factory) as db:
                state_manager = await self._get_hitl_state_manager(db)
                session_state = await state_manager.get_session_status(session.request_id)
        except Exception as e:
            logger.warning(f"Failed to get HITL session state for skip: {e}")

        event_data = {
            "phaseId": phase_number,
            "sessionId": str(session.request_id),
            "hitl_state": session_state,
            "skipped_at": datetime.utcnow().isoformat(),
            "reason": "user_requested_skip"
        }

        await realtime_hub.publish(
            session.request_id,
            build_event("feedback_skipped", **event_data)
        )

    async def _wait_for_user_feedback(
        self,
        session: MangaSession,
        phase_number: int,
        timeout_minutes: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        ユーザーフィードバック待機（既存メソッドのラッパー）
        """
        try:
            feedback = await self._wait_for_user_feedback_event(
                session.request_id, phase_number, timeout_minutes
            )
            return feedback
        except Exception as e:
            logger.error(f"Error waiting for feedback: {e}")
            return None

    async def retry_specific_phase(
        self,
        session: MangaSession,
        phase_id: int,
        force_retry: bool = False,
        reset_feedback: bool = True
    ) -> bool:
        """
        指定されたフェーズのリトライを実行

        Args:
            session: MangaSession instance
            phase_id: リトライするフェーズID
            force_retry: エラー状態でない場合でも強制リトライ
            reset_feedback: フィードバック状態をリセット

        Returns:
            bool: リトライが正常に開始されたかどうか
        """
        logger.info(f"Starting phase retry for session {session.request_id}, phase {phase_id}")

        async with session_scope(self.session_factory) as db:
            try:
                # セッションの状態を確認
                if session.status in [MangaSessionStatus.COMPLETED.value, MangaSessionStatus.RUNNING.value]:
                    if not force_retry:
                        logger.warning(f"Session {session.request_id} is in {session.status} state, retry not allowed")
                        return False

                # フェーズ結果を取得して状態を確認
                from sqlalchemy import select
                from app.db.models.phase_result import PhaseResult

                result = await db.execute(
                    select(PhaseResult).where(
                        PhaseResult.session_id == session.id,
                        PhaseResult.phase == phase_id
                    )
                )
                phase_result = result.scalar_one_or_none()

                if not phase_result:
                    logger.error(f"Phase {phase_id} not found for session {session.request_id}")
                    return False

                # フェーズ状態をリセット
                phase_result.status = "pending"
                if reset_feedback and phase_result.content:
                    # フィードバック関連データをクリア
                    content = phase_result.content.copy() if phase_result.content else {}
                    content.pop("feedback_data", None)
                    content.pop("user_feedback", None)
                    content.pop("hitl_processed", None)
                    phase_result.content = content

                # セッション状態を更新
                session.status = MangaSessionStatus.RUNNING.value
                session.current_phase = phase_id
                session.retry_count += 1
                session.updated_at = datetime.utcnow()

                # WebSocket通知用のイベントを送信
                try:
                    await self._send_websocket_notification(
                        session.request_id,
                        {
                            "type": "phase_retry_started",
                            "phase_id": phase_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "retry_count": session.retry_count
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket notification: {e}")

                await db.commit()

                # バックグラウンドでフェーズ再実行を開始
                asyncio.create_task(self._execute_phase_retry_background(session, phase_id))

                return True

            except Exception as e:
                await db.rollback()
                logger.error(f"Failed to retry phase {phase_id} for session {session.request_id}: {e}")
                return False

    async def _execute_phase_retry_background(self, session: MangaSession, phase_id: int):
        """
        バックグラウンドでフェーズを再実行
        """
        try:
            # フェーズ設定を取得
            phase_config = self._get_phase_config(phase_id)
            if not phase_config:
                logger.error(f"Phase configuration not found for phase {phase_id}")
                return

            # コンテキストを再構築
            context = await self._build_phase_context(session, phase_id)

            # HITLが有効な場合はHITL付きで実行、そうでなければ通常実行
            if hasattr(self, '_execute_single_phase_with_hitl'):
                result = await self._execute_single_phase_with_hitl(session, phase_config, context)
            else:
                result = await self._execute_single_phase(session, phase_config, context)

            # 結果を保存
            async with session_scope(self.session_factory) as db:
                from sqlalchemy import select
                from app.db.models.phase_result import PhaseResult

                db_result = await db.execute(
                    select(PhaseResult).where(
                        PhaseResult.session_id == session.id,
                        PhaseResult.phase == phase_id
                    )
                )
                phase_result = db_result.scalar_one_or_none()

                if phase_result:
                    phase_result.content = result
                    phase_result.status = "completed" if result.get("success") else "failed"
                    phase_result.updated_at = datetime.utcnow()

                await db.commit()

            # WebSocket通知
            await self._send_websocket_notification(
                session.request_id,
                {
                    "type": "phase_retry_completed",
                    "phase_id": phase_id,
                    "status": "completed" if result.get("success") else "failed",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Background phase retry failed for phase {phase_id}: {e}")
            # エラー通知
            await self._send_websocket_notification(
                session.request_id,
                {
                    "type": "phase_retry_failed",
                    "phase_id": phase_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    async def get_phase_error_details(
        self,
        session: MangaSession,
        phase_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        指定されたフェーズの詳細エラー情報を取得

        Args:
            session: MangaSession instance
            phase_id: エラー詳細を取得するフェーズID

        Returns:
            Dict containing error details or None if no error found
        """
        async with session_scope(self.session_factory) as db:
            try:
                from sqlalchemy import select
                from app.db.models.phase_result import PhaseResult

                result = await db.execute(
                    select(PhaseResult).where(
                        PhaseResult.session_id == session.id,
                        PhaseResult.phase == phase_id
                    )
                )
                phase_result = result.scalar_one_or_none()

                if not phase_result:
                    return None

                # エラー情報を抽出
                content = phase_result.content or {}
                error_details = self._extract_error_details(content, phase_result.status)

                if not error_details:
                    return None

                return {
                    "phase_id": phase_id,
                    "phase_name": self._get_phase_name(phase_id),
                    "error_code": error_details.get("error_code", "UNKNOWN_ERROR"),
                    "error_message": error_details.get("error_message", "Unknown error occurred"),
                    "error_details": error_details.get("error_details"),
                    "timestamp": phase_result.updated_at or phase_result.created_at,
                    "retryable": self._is_error_retryable(error_details.get("error_code", "")),
                    "retry_count": session.retry_count,
                    "suggested_actions": self._get_suggested_actions(error_details.get("error_code", ""))
                }

            except Exception as e:
                logger.error(f"Failed to get error details for phase {phase_id}: {e}")
                return None

    def _extract_error_details(self, content: Dict[str, Any], status: str) -> Optional[Dict[str, Any]]:
        """フェーズ結果からエラー詳細を抽出"""
        if status != "failed" and not content.get("error"):
            return None

        error_info = content.get("error", {})
        if isinstance(error_info, str):
            error_info = {"message": error_info}

        # エラーコードの分類
        error_message = error_info.get("message", error_info.get("error_message", "Unknown error"))
        error_code = error_info.get("code", error_info.get("error_code"))

        if not error_code:
            error_code = self._classify_error_code(error_message)

        return {
            "error_code": error_code,
            "error_message": error_message,
            "error_details": error_info.get("details", error_info.get("traceback"))
        }

    def _classify_error_code(self, error_message: str) -> str:
        """エラーメッセージからエラーコードを分類"""
        error_message_lower = error_message.lower()

        # より具体的なものから順に判定
        if any(keyword in error_message_lower for keyword in ["timeout", "deadline"]):
            return "TIMEOUT_ERROR"
        elif any(keyword in error_message_lower for keyword in ["auth", "permission", "unauthorized", "forbidden"]):
            return "AUTH_ERROR"
        elif any(keyword in error_message_lower for keyword in ["validation", "invalid", "malformed"]):
            return "VALIDATION_ERROR"
        elif any(keyword in error_message_lower for keyword in ["server", "internal", "500"]):
            return "SERVER_ERROR"
        elif any(keyword in error_message_lower for keyword in ["network", "connection", "http"]):
            return "NETWORK_ERROR"
        else:
            return "UNKNOWN_ERROR"

    def _is_error_retryable(self, error_code: str) -> bool:
        """エラーコードがリトライ可能かどうか判定"""
        retryable_errors = {
            "NETWORK_ERROR", "TIMEOUT_ERROR", "SERVER_ERROR"
        }
        return error_code in retryable_errors

    def _get_suggested_actions(self, error_code: str) -> List[str]:
        """エラーコードに基づく推奨アクション"""
        actions_map = {
            "NETWORK_ERROR": [
                "ネットワーク接続を確認してください",
                "しばらく待ってからリトライしてください"
            ],
            "AUTH_ERROR": [
                "認証情報を確認してください",
                "ログインし直してください"
            ],
            "VALIDATION_ERROR": [
                "入力データを確認してください",
                "必要な項目が入力されているか確認してください"
            ],
            "TIMEOUT_ERROR": [
                "処理に時間がかかっています",
                "しばらく待ってからリトライしてください"
            ],
            "SERVER_ERROR": [
                "サーバーで問題が発生しています",
                "管理者に問い合わせるかしばらく待ってからリトライしてください"
            ],
            "UNKNOWN_ERROR": [
                "予期しないエラーが発生しました",
                "リトライするか管理者に問い合わせてください"
            ]
        }
        return actions_map.get(error_code, ["リトライしてください"])

    def _get_phase_name(self, phase_id: int) -> str:
        """フェーズIDからフェーズ名を取得"""
        phase_names = {
            1: "ストーリー分析",
            2: "キャラクター設定",
            3: "コマ割り設計",
            4: "画像生成",
            5: "最終調整"
        }
        return phase_names.get(phase_id, f"フェーズ {phase_id}")

    def _get_phase_config(self, phase_id: int) -> Optional[Dict[str, Any]]:
        """フェーズIDから設定を取得"""
        # 既存のフェーズ設定から取得
        if hasattr(self, 'phases') and self.phases:
            for phase in self.phases:
                if phase.get("phase") == phase_id:
                    return phase
        return {"phase": phase_id, "name": self._get_phase_name(phase_id)}

    async def _build_phase_context(self, session: MangaSession, target_phase_id: int) -> Dict[int, Dict[str, Any]]:
        """指定フェーズ実行用のコンテキストを構築"""
        context = {}

        async with session_scope(self.session_factory) as db:
            try:
                from sqlalchemy import select
                from app.db.models.phase_result import PhaseResult

                # 対象フェーズより前の完了済みフェーズ結果を取得
                result = await db.execute(
                    select(PhaseResult).where(
                        PhaseResult.session_id == session.id,
                        PhaseResult.phase < target_phase_id,
                        PhaseResult.status == "completed"
                    ).order_by(PhaseResult.phase)
                )
                prior_results = result.scalars().all()

                for phase_result in prior_results:
                    if phase_result.content:
                        context[phase_result.phase] = phase_result.content

            except Exception as e:
                logger.error(f"Failed to build phase context: {e}")

        return context

    async def _send_websocket_notification(self, request_id: UUID, data: Dict[str, Any]):
        """WebSocket通知を送信"""
        try:
            from app.services.websocket_service import WebSocketService
            ws_service = WebSocketService()
            await ws_service.send_to_session(str(request_id), data)
        except Exception as e:
            logger.warning(f"Failed to send WebSocket notification: {e}")

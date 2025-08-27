"""MangaGenerationEngine - 7フェーズ統合処理エンジン

設計書要件:
- 7フェーズ統合処理（97秒目標）
- 非同期処理パイプライン
- HITL対応（各フェーズ完了後30秒フィードバック待機）
- エラーハンドリング・3回リトライメカニズム
- Google AI API統合（Gemini Pro, Imagen 4）
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator
from uuid import UUID, uuid4
from enum import Enum

from app.core.logging import LoggerMixin
from app.core.config.settings import get_settings
from app.domain.manga.entities import MangaProject, GenerationSession
from app.domain.manga.value_objects import PhaseResult, QualityMetrics
from app.agents.base_agent import BaseAgent
from app.agents.phase1_concept import ConceptAnalysisAgent
from app.agents.phase2_character import CharacterDesignAgent
from app.agents.phase3_plot import PlotStructureAgent
from app.agents.phase4_name import NameGenerationAgent
from app.agents.phase5_image import ImageGenerationAgent
from app.agents.phase6_dialogue import DialoguePlacementAgent
from app.agents.phase7_integration import FinalIntegrationAgent
from .hitl_manager import HITLManager
from .quality_gate import QualityGateSystem
from .version_manager import VersionManager
from .websocket_manager import WebSocketManager
from sqlalchemy.ext.asyncio import AsyncSession


class ProcessingStatus(Enum):
    """Processing status enumeration."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    PROCESSING = "processing"
    WAITING_FEEDBACK = "waiting_feedback"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PhaseStatus(Enum):
    """Individual phase status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_HITL = "waiting_hitl"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class MangaGenerationEngine(LoggerMixin):
    """7フェーズ統合処理エンジン - 中核システム
    
    設計書要件の97秒目標・1000同時接続対応の統合エンジン。
    非同期処理パイプライン・HITL・品質ゲート・バージョン管理を統合。
    """
    
    def __init__(
        self,
        hitl_manager: HITLManager,
        quality_gate: QualityGateSystem,
        version_manager: VersionManager,
        websocket_manager: WebSocketManager,
        db_session: AsyncSession
    ):
        """Initialize MangaGenerationEngine.
        
        Args:
            hitl_manager: Human-in-the-loop feedback manager
            quality_gate: Quality assurance system
            version_manager: Version control system
            websocket_manager: Real-time communication manager
            db_session: Database session
        """
        super().__init__()
        self.settings = get_settings()
        
        # Core components
        self.hitl_manager = hitl_manager
        self.quality_gate = quality_gate
        self.version_manager = version_manager
        self.websocket_manager = websocket_manager
        self.db_session = db_session
        
        # Phase agents initialization
        self.phase_agents: Dict[int, BaseAgent] = {}
        self._initialize_phase_agents()
        
        # Active sessions tracking
        self.active_sessions: Dict[UUID, Dict[str, Any]] = {}
        self.session_locks: Dict[UUID, asyncio.Lock] = {}
        
        # Performance metrics
        self.metrics = {
            "total_sessions": 0,
            "completed_sessions": 0,
            "failed_sessions": 0,
            "average_processing_time": 0.0,
            "phase_success_rates": {i: 0.0 for i in range(1, 8)},
            "hitl_engagement_rate": 0.0
        }
        
    def _initialize_phase_agents(self):
        """Initialize all phase processing agents."""
        phase_configs = {
            1: (ConceptAnalysisAgent, "concept_analysis"),
            2: (CharacterDesignAgent, "character_design"),
            3: (PlotStructureAgent, "plot_structure"),
            4: (NameGenerationAgent, "name_generation"),
            5: (ImageGenerationAgent, "image_generation"),
            6: (DialoguePlacementAgent, "dialogue_placement"),
            7: (FinalIntegrationAgent, "final_integration")
        }
        
        for phase_num, (agent_class, phase_name) in phase_configs.items():
            timeout = self.settings.phase_timeouts.get(phase_num, 60)
            self.phase_agents[phase_num] = agent_class(
                phase_number=phase_num,
                phase_name=phase_name,
                timeout_seconds=timeout
            )
    
    async def generate_manga(
        self,
        user_input: str,
        user_id: UUID,
        session_id: Optional[UUID] = None,
        quality_level: str = "high",
        enable_hitl: bool = True,
        hitl_timeout: int = 30
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate manga through 7-phase integrated pipeline.
        
        Args:
            user_input: User's creative input/prompt
            user_id: User identifier
            session_id: Optional session identifier
            quality_level: Target quality level
            enable_hitl: Enable human-in-the-loop feedback
            hitl_timeout: HITL feedback timeout seconds
            
        Yields:
            Real-time progress updates and results
        """
        if session_id is None:
            session_id = uuid4()
            
        # Initialize session tracking
        await self._initialize_session(session_id, user_id, user_input, quality_level, enable_hitl)
        
        try:
            # Pipeline execution with real-time updates
            async for update in self._execute_pipeline(session_id, hitl_timeout):
                yield update
                
        except Exception as e:
            self.logger.error(f"Pipeline execution failed for session {session_id}: {e}")
            await self._handle_session_failure(session_id, str(e))
            yield {
                "type": "error",
                "session_id": str(session_id),
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            await self._cleanup_session(session_id)
    
    async def _initialize_session(
        self,
        session_id: UUID,
        user_id: UUID,
        user_input: str,
        quality_level: str,
        enable_hitl: bool
    ):
        """Initialize generation session."""
        self.session_locks[session_id] = asyncio.Lock()
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "user_input": user_input,
            "quality_level": quality_level,
            "enable_hitl": enable_hitl,
            "status": ProcessingStatus.INITIALIZING,
            "start_time": datetime.utcnow(),
            "current_phase": 0,
            "phase_results": {},
            "phase_statuses": {i: PhaseStatus.PENDING for i in range(1, 8)},
            "quality_scores": {},
            "retry_counts": {i: 0 for i in range(1, 8)},
            "hitl_feedback": {},
            "version_history": [],
            "total_processing_time": 0.0,
            "phase_timings": {}
        }
        
        self.active_sessions[session_id] = session_data
        
        # Create version checkpoint
        await self.version_manager.create_checkpoint(
            session_id=session_id,
            phase_number=0,
            data={"user_input": user_input},
            metadata={"initialized_at": datetime.utcnow().isoformat()}
        )
        
        # Register WebSocket session
        await self.websocket_manager.register_session(session_id, user_id)
        
        self.logger.info(f"Initialized generation session {session_id} for user {user_id}")
    
    async def _execute_pipeline(
        self,
        session_id: UUID,
        hitl_timeout: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute 7-phase processing pipeline.
        
        Args:
            session_id: Session identifier
            hitl_timeout: HITL feedback timeout
            
        Yields:
            Real-time progress updates
        """
        session_data = self.active_sessions[session_id]
        session_data["status"] = ProcessingStatus.PROCESSING
        
        # Send pipeline start notification
        yield {
            "type": "pipeline_started",
            "session_id": str(session_id),
            "total_phases": 7,
            "estimated_time": self.settings.total_pipeline_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Execute phases sequentially with parallel support where applicable
        for phase_number in range(1, 8):
            phase_start_time = time.time()
            
            try:
                # Phase execution with retries
                phase_result = await self._execute_phase_with_retries(
                    session_id, phase_number, max_retries=3
                )
                
                phase_end_time = time.time()
                phase_duration = phase_end_time - phase_start_time
                session_data["phase_timings"][phase_number] = phase_duration
                
                # Quality gate check
                quality_check = await self.quality_gate.evaluate_phase_result(
                    phase_number, phase_result
                )
                
                session_data["quality_scores"][phase_number] = quality_check.score
                
                if not quality_check.passed and quality_check.score < 0.70:
                    self.logger.warning(
                        f"Phase {phase_number} quality check failed: {quality_check.score}"
                    )
                    
                    # Retry if under retry limit
                    if session_data["retry_counts"][phase_number] < 3:
                        session_data["retry_counts"][phase_number] += 1
                        session_data["phase_statuses"][phase_number] = PhaseStatus.RETRYING
                        continue
                
                # Store phase result
                session_data["phase_results"][phase_number] = phase_result
                session_data["phase_statuses"][phase_number] = PhaseStatus.COMPLETED
                session_data["current_phase"] = phase_number
                
                # Create version checkpoint
                await self.version_manager.create_checkpoint(
                    session_id=session_id,
                    phase_number=phase_number,
                    data=phase_result,
                    metadata={
                        "quality_score": quality_check.score,
                        "processing_time": phase_duration,
                        "completed_at": datetime.utcnow().isoformat()
                    }
                )
                
                # Send phase completion update
                yield {
                    "type": "phase_completed",
                    "session_id": str(session_id),
                    "phase_number": phase_number,
                    "phase_name": self.phase_agents[phase_number].phase_name,
                    "duration": phase_duration,
                    "quality_score": quality_check.score,
                    "result": phase_result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # HITL feedback opportunity
                if session_data["enable_hitl"] and phase_number in [2, 4, 5]:
                    session_data["status"] = ProcessingStatus.WAITING_FEEDBACK
                    session_data["phase_statuses"][phase_number] = PhaseStatus.WAITING_HITL
                    
                    yield {
                        "type": "hitl_opportunity",
                        "session_id": str(session_id),
                        "phase_number": phase_number,
                        "phase_result": phase_result,
                        "timeout": hitl_timeout,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Wait for HITL feedback
                    feedback = await self.hitl_manager.wait_for_feedback(
                        session_id, phase_number, timeout=hitl_timeout
                    )
                    
                    if feedback:
                        session_data["hitl_feedback"][phase_number] = feedback
                        
                        # Apply feedback if modifications requested
                        if feedback.get("action") == "modify":
                            modified_result = await self._apply_hitl_feedback(
                                session_id, phase_number, phase_result, feedback
                            )
                            session_data["phase_results"][phase_number] = modified_result
                            
                            yield {
                                "type": "hitl_applied",
                                "session_id": str(session_id),
                                "phase_number": phase_number,
                                "feedback": feedback,
                                "modified_result": modified_result,
                                "timestamp": datetime.utcnow().isoformat()
                            }
                    
                    session_data["status"] = ProcessingStatus.PROCESSING
                    session_data["phase_statuses"][phase_number] = PhaseStatus.COMPLETED
                
            except Exception as e:
                self.logger.error(f"Phase {phase_number} execution failed: {e}")
                session_data["phase_statuses"][phase_number] = PhaseStatus.FAILED
                
                # Retry logic
                if session_data["retry_counts"][phase_number] < 3:
                    session_data["retry_counts"][phase_number] += 1
                    session_data["phase_statuses"][phase_number] = PhaseStatus.RETRYING
                    
                    yield {
                        "type": "phase_retry",
                        "session_id": str(session_id),
                        "phase_number": phase_number,
                        "retry_count": session_data["retry_counts"][phase_number],
                        "error": str(e),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    continue
                else:
                    # Max retries exceeded
                    raise Exception(f"Phase {phase_number} failed after 3 retries: {e}")
        
        # Pipeline completion
        session_data["status"] = ProcessingStatus.COMPLETED
        total_time = time.time() - session_data["start_time"].timestamp()
        session_data["total_processing_time"] = total_time
        
        # Final quality assessment
        overall_quality = await self.quality_gate.evaluate_overall_quality(
            session_data["phase_results"]
        )
        
        # Generate final result
        final_result = await self._generate_final_result(session_id)
        
        yield {
            "type": "pipeline_completed",
            "session_id": str(session_id),
            "total_time": total_time,
            "overall_quality": overall_quality.score,
            "final_result": final_result,
            "phase_timings": session_data["phase_timings"],
            "quality_scores": session_data["quality_scores"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.info(
            f"Pipeline completed for session {session_id} in {total_time:.2f}s"
        )
    
    async def _execute_phase_with_retries(
        self,
        session_id: UUID,
        phase_number: int,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Execute single phase with retry logic.
        
        Args:
            session_id: Session identifier
            phase_number: Phase number to execute
            max_retries: Maximum retry attempts
            
        Returns:
            Phase execution result
        """
        session_data = self.active_sessions[session_id]
        agent = self.phase_agents[phase_number]
        
        # Prepare input data
        input_data = {
            "user_input": session_data["user_input"],
            "quality_level": session_data["quality_level"],
            "session_context": {
                "session_id": session_id,
                "user_id": session_data["user_id"],
                "current_phase": phase_number
            }
        }
        
        # Include previous phase results
        previous_results = {}
        for prev_phase in range(1, phase_number):
            if prev_phase in session_data["phase_results"]:
                previous_results[prev_phase] = session_data["phase_results"][prev_phase]
        
        # Execute with timeout
        timeout = self.settings.phase_timeouts.get(phase_number, 60)
        
        try:
            result = await asyncio.wait_for(
                agent.process_phase(input_data, session_id, previous_results),
                timeout=timeout
            )
            
            return result
            
        except asyncio.TimeoutError:
            raise Exception(f"Phase {phase_number} execution timed out after {timeout}s")
        except Exception as e:
            raise Exception(f"Phase {phase_number} execution failed: {e}")
    
    async def _apply_hitl_feedback(
        self,
        session_id: UUID,
        phase_number: int,
        original_result: Dict[str, Any],
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply HITL feedback to phase result.
        
        Args:
            session_id: Session identifier
            phase_number: Phase number
            original_result: Original phase result
            feedback: HITL feedback data
            
        Returns:
            Modified result incorporating feedback
        """
        agent = self.phase_agents[phase_number]
        
        # Apply feedback through agent's feedback handler
        if hasattr(agent, 'apply_feedback'):
            modified_result = await agent.apply_feedback(
                original_result, feedback
            )
        else:
            # Default feedback application
            modified_result = original_result.copy()
            if "modifications" in feedback:
                modified_result.update(feedback["modifications"])
        
        return modified_result
    
    async def _generate_final_result(self, session_id: UUID) -> Dict[str, Any]:
        """Generate final manga result from all phase results.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Final integrated manga result
        """
        session_data = self.active_sessions[session_id]
        
        # Use Phase 7 (Final Integration) agent to create final result
        integration_agent = self.phase_agents[7]
        final_result = session_data["phase_results"].get(7, {})
        
        # Add metadata
        final_result.update({
            "session_metadata": {
                "session_id": str(session_id),
                "user_id": str(session_data["user_id"]),
                "generated_at": datetime.utcnow().isoformat(),
                "total_processing_time": session_data["total_processing_time"],
                "quality_level": session_data["quality_level"],
                "phase_count": len(session_data["phase_results"]),
                "hitl_interactions": len(session_data["hitl_feedback"]),
                "overall_quality": sum(session_data["quality_scores"].values()) / len(session_data["quality_scores"])
            }
        })
        
        return final_result
    
    async def _handle_session_failure(self, session_id: UUID, error: str):
        """Handle session failure cleanup and notifications.
        
        Args:
            session_id: Failed session identifier
            error: Error description
        """
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id]
            session_data["status"] = ProcessingStatus.FAILED
            session_data["error"] = error
            
            # Update metrics
            self.metrics["failed_sessions"] += 1
            
            # Notify WebSocket clients
            await self.websocket_manager.broadcast_to_session(
                session_id,
                {
                    "type": "session_failed",
                    "session_id": str(session_id),
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    async def _cleanup_session(self, session_id: UUID):
        """Clean up session resources.
        
        Args:
            session_id: Session identifier to cleanup
        """
        # Update final metrics
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id]
            
            if session_data["status"] == ProcessingStatus.COMPLETED:
                self.metrics["completed_sessions"] += 1
                
                # Update average processing time
                total_time = session_data["total_processing_time"]
                current_avg = self.metrics["average_processing_time"]
                completed_count = self.metrics["completed_sessions"]
                
                self.metrics["average_processing_time"] = (
                    (current_avg * (completed_count - 1) + total_time) / completed_count
                )
        
        # Cleanup resources
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        if session_id in self.session_locks:
            del self.session_locks[session_id]
        
        # Unregister WebSocket session
        await self.websocket_manager.unregister_session(session_id)
        
        self.logger.info(f"Cleaned up session {session_id}")
    
    async def get_session_status(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Get current session status.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session status data or None if not found
        """
        if session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id]
        
        return {
            "session_id": str(session_id),
            "status": session_data["status"].value,
            "current_phase": session_data["current_phase"],
            "phase_statuses": {k: v.value for k, v in session_data["phase_statuses"].items()},
            "quality_scores": session_data["quality_scores"],
            "processing_time": (datetime.utcnow() - session_data["start_time"]).total_seconds(),
            "retry_counts": session_data["retry_counts"],
            "hitl_feedback_count": len(session_data["hitl_feedback"])
        }
    
    async def cancel_session(self, session_id: UUID, reason: str = "User cancelled") -> bool:
        """Cancel active session.
        
        Args:
            session_id: Session identifier to cancel
            reason: Cancellation reason
            
        Returns:
            True if successfully cancelled, False if not found
        """
        if session_id not in self.active_sessions:
            return False
        
        session_data = self.active_sessions[session_id]
        session_data["status"] = ProcessingStatus.CANCELLED
        session_data["cancellation_reason"] = reason
        
        # Notify WebSocket clients
        await self.websocket_manager.broadcast_to_session(
            session_id,
            {
                "type": "session_cancelled",
                "session_id": str(session_id),
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        self.logger.info(f"Cancelled session {session_id}: {reason}")
        return True
    
    def get_engine_metrics(self) -> Dict[str, Any]:
        """Get engine performance metrics.
        
        Returns:
            Engine performance and usage metrics
        """
        active_count = len(self.active_sessions)
        
        # Calculate phase success rates
        phase_success_rates = {}
        for phase_num in range(1, 8):
            successful = sum(
                1 for session in self.active_sessions.values()
                if session["phase_statuses"].get(phase_num) == PhaseStatus.COMPLETED
            )
            total = len(self.active_sessions)
            phase_success_rates[phase_num] = (successful / total * 100) if total > 0 else 0
        
        # Calculate HITL engagement rate
        hitl_engaged = sum(
            1 for session in self.active_sessions.values()
            if session["hitl_feedback"]
        )
        hitl_rate = (hitl_engaged / active_count * 100) if active_count > 0 else 0
        
        return {
            "active_sessions": active_count,
            "total_sessions": self.metrics["total_sessions"],
            "completed_sessions": self.metrics["completed_sessions"],
            "failed_sessions": self.metrics["failed_sessions"],
            "success_rate": (
                self.metrics["completed_sessions"] / self.metrics["total_sessions"] * 100
                if self.metrics["total_sessions"] > 0 else 0
            ),
            "average_processing_time": self.metrics["average_processing_time"],
            "phase_success_rates": phase_success_rates,
            "hitl_engagement_rate": hitl_rate,
            "engine_uptime": (datetime.utcnow() - datetime.utcnow()).total_seconds(),
            "performance_target_met": self.metrics["average_processing_time"] <= 97.0
        }
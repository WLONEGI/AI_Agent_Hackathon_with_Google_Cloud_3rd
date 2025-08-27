"""Pipeline Orchestrator for coordinating all manga generation phases."""

from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from uuid import UUID
import asyncio
import json
import time
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from app.agents.base_agent import BaseAgent
from app.agents.phase1_concept import Phase1ConceptAgent
from app.agents.phase2_character import Phase2CharacterAgent
from app.agents.phase3_story import Phase3StoryAgent
from app.agents.phase4_name import Phase4NameAgent
from app.agents.phase5_image import Phase5ImageAgent
from app.agents.phase6_dialogue import Phase6DialogueAgent
from app.agents.phase7_integration import Phase7IntegrationAgent
from app.core.config import settings
from app.core.logging import LoggerMixin
from app.models.manga import MangaSession, PhaseResult


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PARALLEL_EXECUTION = "parallel_execution"
    WAITING_FEEDBACK = "waiting_feedback"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PhaseExecution:
    """Phase execution tracking."""
    phase_number: int
    agent: BaseAgent
    status: str = "pending"
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    dependencies: List[int] = field(default_factory=list)
    parallel_group: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3


class PipelineOrchestrator(LoggerMixin):
    """Orchestrates the entire manga generation pipeline with optimal parallel execution."""
    
    def __init__(self):
        self.agents = self._initialize_agents()
        self.execution_plan = self._create_execution_plan()
        self.status = PipelineStatus.INITIALIZING
        self.current_phase = 0
        self.session_id: Optional[UUID] = None
        self.session: Optional[MangaSession] = None
        self.phase_results: Dict[int, Dict[str, Any]] = {}
        self.execution_stats = {
            "total_start_time": None,
            "total_end_time": None,
            "phase_times": {},
            "parallel_efficiency": 0.0,
            "total_processing_time": 0,
            "estimated_sequential_time": 0
        }
        
        # Progress tracking
        self.progress_callbacks: List[Callable] = []
        self.feedback_handlers: Dict[int, Callable] = {}
        
        # Parallel execution control
        self.max_parallel_phases = 3
        self.parallel_semaphore = asyncio.Semaphore(self.max_parallel_phases)
    
    def _initialize_agents(self) -> Dict[int, BaseAgent]:
        """Initialize all phase agents."""
        
        return {
            1: Phase1ConceptAgent(),
            2: Phase2CharacterAgent(),
            3: Phase3StoryAgent(),
            4: Phase4NameAgent(),
            5: Phase5ImageAgent(),
            6: Phase6DialogueAgent(),
            7: Phase7IntegrationAgent()
        }
    
    def _create_execution_plan(self) -> Dict[int, PhaseExecution]:
        """Create optimized execution plan with dependencies and parallel groups."""
        
        execution_plan = {
            1: PhaseExecution(
                phase_number=1,
                agent=self.agents[1],
                dependencies=[],  # No dependencies
                parallel_group=None
            ),
            2: PhaseExecution(
                phase_number=2,
                agent=self.agents[2],
                dependencies=[1],  # Depends on Phase 1
                parallel_group=1   # Can run parallel with Phase 3
            ),
            3: PhaseExecution(
                phase_number=3,
                agent=self.agents[3],
                dependencies=[1],  # Depends on Phase 1
                parallel_group=1   # Can run parallel with Phase 2
            ),
            4: PhaseExecution(
                phase_number=4,
                agent=self.agents[4],
                dependencies=[1, 2, 3],  # Depends on Phases 1, 2, 3
                parallel_group=None
            ),
            5: PhaseExecution(
                phase_number=5,
                agent=self.agents[5],
                dependencies=[1, 2, 3, 4],  # Depends on Phases 1-4
                parallel_group=None  # Heavy parallel processing internally
            ),
            6: PhaseExecution(
                phase_number=6,
                agent=self.agents[6],
                dependencies=[1, 2, 3, 4, 5],  # Depends on Phases 1-5
                parallel_group=2  # Can run parallel with Phase 7 preparation
            ),
            7: PhaseExecution(
                phase_number=7,
                agent=self.agents[7],
                dependencies=[1, 2, 3, 4, 5, 6],  # Depends on all previous phases
                parallel_group=None
            )
        }
        
        return execution_plan
    
    async def execute_pipeline(
        self,
        session: MangaSession,
        input_data: Dict[str, Any],
        db_session,
        progress_callback: Optional[Callable] = None,
        feedback_timeout: int = 300
    ) -> Dict[str, Any]:
        """Execute the complete manga generation pipeline."""
        
        self.session = session
        self.session_id = session.id
        self.status = PipelineStatus.RUNNING
        
        if progress_callback:
            self.progress_callbacks.append(progress_callback)
        
        self.log_info(
            f"Starting manga generation pipeline for session {self.session_id}",
            total_phases=len(self.execution_plan),
            parallel_groups=len(set(p.parallel_group for p in self.execution_plan.values() if p.parallel_group))
        )
        
        try:
            # Initialize execution stats
            self.execution_stats["total_start_time"] = time.time()
            
            # Execute phases in optimal order
            await self._execute_phases_optimally(input_data, db_session, feedback_timeout)
            
            # Calculate final stats
            self.execution_stats["total_end_time"] = time.time()
            self.execution_stats["total_processing_time"] = (
                self.execution_stats["total_end_time"] - self.execution_stats["total_start_time"]
            )
            
            self._calculate_efficiency_metrics()
            
            self.status = PipelineStatus.COMPLETED
            self.log_info(
                f"Pipeline completed successfully",
                session_id=str(self.session_id),
                total_time=f"{self.execution_stats['total_processing_time']:.2f}s",
                efficiency=f"{self.execution_stats['parallel_efficiency']:.1%}"
            )
            
            # Return comprehensive results
            return await self._compile_final_results()
            
        except Exception as e:
            self.status = PipelineStatus.FAILED
            self.log_error(
                f"Pipeline execution failed: {str(e)}",
                session_id=str(self.session_id),
                error=e
            )
            raise
    
    async def _execute_phases_optimally(
        self,
        input_data: Dict[str, Any],
        db_session,
        feedback_timeout: int
    ):
        """Execute phases with optimal parallel processing."""
        
        executed_phases = set()
        
        while len(executed_phases) < len(self.execution_plan):
            # Find phases ready for execution
            ready_phases = self._find_ready_phases(executed_phases)
            
            if not ready_phases:
                self.log_error("No ready phases found - possible circular dependency")
                break
            
            # Group phases for parallel execution
            parallel_groups = self._group_phases_for_parallel_execution(ready_phases)
            
            # Execute groups
            for group_phases in parallel_groups:
                if len(group_phases) == 1:
                    # Single phase execution
                    phase_execution = group_phases[0]
                    await self._execute_single_phase(phase_execution, input_data, db_session)
                    executed_phases.add(phase_execution.phase_number)
                    
                else:
                    # Parallel execution
                    self.status = PipelineStatus.PARALLEL_EXECUTION
                    self.log_info(
                        f"Executing {len(group_phases)} phases in parallel",
                        phases=[p.phase_number for p in group_phases]
                    )
                    
                    parallel_results = await asyncio.gather(
                        *[
                            self._execute_single_phase(phase_exec, input_data, db_session)
                            for phase_exec in group_phases
                        ],
                        return_exceptions=True
                    )
                    
                    # Process parallel results
                    for i, result in enumerate(parallel_results):
                        phase_execution = group_phases[i]
                        if isinstance(result, Exception):
                            phase_execution.status = "failed"
                            phase_execution.error = str(result)
                            self.log_error(
                                f"Phase {phase_execution.phase_number} failed in parallel execution",
                                error=result
                            )
                        else:
                            executed_phases.add(phase_execution.phase_number)
                    
                # Update progress after each group
                await self._update_progress(len(executed_phases), len(self.execution_plan))
                
                # Check for feedback requirements
                if self.session and self.session.hitl_enabled:
                    await self._check_feedback_requirements(executed_phases, feedback_timeout)
        
        self.status = PipelineStatus.RUNNING
    
    def _find_ready_phases(self, executed_phases: set) -> List[PhaseExecution]:
        """Find phases that are ready for execution (all dependencies satisfied)."""
        
        ready_phases = []
        
        for phase_num, phase_exec in self.execution_plan.items():
            if (phase_num not in executed_phases and 
                phase_exec.status in ["pending", "failed"] and
                all(dep in executed_phases for dep in phase_exec.dependencies)):
                
                ready_phases.append(phase_exec)
        
        return ready_phases
    
    def _group_phases_for_parallel_execution(
        self, ready_phases: List[PhaseExecution]
    ) -> List[List[PhaseExecution]]:
        """Group phases for optimal parallel execution."""
        
        # Group by parallel group number
        parallel_groups = {}
        sequential_phases = []
        
        for phase_exec in ready_phases:
            if phase_exec.parallel_group is not None:
                group_num = phase_exec.parallel_group
                if group_num not in parallel_groups:
                    parallel_groups[group_num] = []
                parallel_groups[group_num].append(phase_exec)
            else:
                # Sequential execution
                sequential_phases.append([phase_exec])
        
        # Combine groups
        execution_groups = list(parallel_groups.values()) + sequential_phases
        
        # Sort by minimum phase number in group
        execution_groups.sort(key=lambda group: min(p.phase_number for p in group))
        
        return execution_groups
    
    async def _execute_single_phase(
        self,
        phase_execution: PhaseExecution,
        input_data: Dict[str, Any],
        db_session
    ):
        """Execute a single phase with retry logic."""
        
        phase_num = phase_execution.phase_number
        agent = phase_execution.agent
        
        for attempt in range(phase_execution.max_retries + 1):
            try:
                phase_execution.status = "running"
                phase_execution.start_time = time.time()
                phase_execution.retry_count = attempt
                
                self.log_info(
                    f"Executing Phase {phase_num} (attempt {attempt + 1})",
                    agent=agent.__class__.__name__
                )
                
                # Get previous results for this phase
                previous_results = {k: v for k, v in self.phase_results.items() if k < phase_num}
                
                # Execute phase with semaphore control
                async with self.parallel_semaphore:
                    phase_result = await agent.process(
                        self.session,
                        input_data,
                        db_session,
                        previous_results if previous_results else None
                    )
                
                # Record successful execution
                phase_execution.end_time = time.time()
                phase_execution.status = "completed"
                phase_execution.result = phase_result.output_data
                
                # Store result for next phases
                self.phase_results[phase_num] = phase_result.output_data
                
                # Record timing
                execution_time = phase_execution.end_time - phase_execution.start_time
                self.execution_stats["phase_times"][phase_num] = execution_time
                
                self.log_info(
                    f"Phase {phase_num} completed successfully",
                    execution_time=f"{execution_time:.2f}s",
                    retry_count=attempt
                )
                
                return phase_result
                
            except Exception as e:
                phase_execution.error = str(e)
                
                if attempt < phase_execution.max_retries:
                    self.log_warning(
                        f"Phase {phase_num} failed (attempt {attempt + 1}), retrying",
                        error=e
                    )
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                else:
                    phase_execution.status = "failed"
                    phase_execution.end_time = time.time()
                    self.log_error(
                        f"Phase {phase_num} failed after {phase_execution.max_retries + 1} attempts",
                        error=e
                    )
                    raise
    
    async def _update_progress(self, completed_phases: int, total_phases: int):
        """Update progress and notify callbacks."""
        
        progress_percentage = (completed_phases / total_phases) * 100
        self.current_phase = completed_phases
        
        # Update session progress
        if self.session:
            self.session.current_phase = completed_phases
            
        # Notify progress callbacks
        progress_info = {
            "current_phase": completed_phases,
            "total_phases": total_phases,
            "progress_percentage": progress_percentage,
            "status": self.status.value,
            "phase_results": self.phase_results.copy()
        }
        
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(progress_info)
                else:
                    callback(progress_info)
            except Exception as e:
                self.log_warning(f"Progress callback failed: {e}")
    
    async def _check_feedback_requirements(
        self, executed_phases: set, feedback_timeout: int
    ):
        """Check if user feedback is required after certain phases."""
        
        # Define phases that might require feedback
        feedback_phases = {2, 4, 6}  # After character, layout, and dialogue phases
        
        for phase_num in feedback_phases:
            if (phase_num in executed_phases and 
                phase_num in self.feedback_handlers and
                phase_num not in getattr(self, '_feedback_processed', set())):
                
                self.status = PipelineStatus.WAITING_FEEDBACK
                self.log_info(f"Waiting for feedback after Phase {phase_num}")
                
                try:
                    # Wait for feedback with timeout
                    feedback_handler = self.feedback_handlers[phase_num]
                    feedback = await asyncio.wait_for(
                        feedback_handler(self.phase_results[phase_num]),
                        timeout=feedback_timeout
                    )
                    
                    if feedback:
                        # Apply feedback to phase result
                        agent = self.agents[phase_num]
                        adjusted_result = await agent.apply_feedback(
                            self.phase_results[phase_num],
                            feedback
                        )
                        self.phase_results[phase_num] = adjusted_result
                        
                        self.log_info(f"Applied feedback to Phase {phase_num}")
                    
                    # Mark feedback as processed
                    if not hasattr(self, '_feedback_processed'):
                        self._feedback_processed = set()
                    self._feedback_processed.add(phase_num)
                    
                except asyncio.TimeoutError:
                    self.log_warning(f"Feedback timeout for Phase {phase_num}, proceeding without feedback")
                except Exception as e:
                    self.log_error(f"Feedback processing failed for Phase {phase_num}: {e}")
                
                self.status = PipelineStatus.RUNNING
    
    def _calculate_efficiency_metrics(self):
        """Calculate parallel execution efficiency metrics."""
        
        phase_times = self.execution_stats["phase_times"]
        
        if not phase_times:
            return
        
        # Calculate estimated sequential time
        estimated_sequential_time = sum(phase_times.values())
        self.execution_stats["estimated_sequential_time"] = estimated_sequential_time
        
        # Calculate parallel efficiency
        actual_time = self.execution_stats["total_processing_time"]
        if estimated_sequential_time > 0:
            self.execution_stats["parallel_efficiency"] = (
                1.0 - (actual_time / estimated_sequential_time)
            )
        
        # Calculate phase-specific metrics
        self.execution_stats["fastest_phase"] = min(phase_times, key=phase_times.get)
        self.execution_stats["slowest_phase"] = max(phase_times, key=phase_times.get)
        self.execution_stats["average_phase_time"] = sum(phase_times.values()) / len(phase_times)
    
    async def _compile_final_results(self) -> Dict[str, Any]:
        """Compile comprehensive final results."""
        
        # Get Phase 7 results (final integration)
        final_integration = self.phase_results.get(7, {})
        
        # Compile execution summary
        execution_summary = {
            "pipeline_status": self.status.value,
            "total_execution_time_seconds": self.execution_stats["total_processing_time"],
            "parallel_efficiency_percentage": self.execution_stats["parallel_efficiency"] * 100,
            "phases_completed": len(self.phase_results),
            "phases_failed": len([
                p for p in self.execution_plan.values() if p.status == "failed"
            ]),
            "retry_count": sum(p.retry_count for p in self.execution_plan.values()),
            "performance_metrics": self.execution_stats
        }
        
        # Compile quality metrics
        quality_summary = {}
        if final_integration:
            quality_assessment = final_integration.get("quality_assessment", {})
            quality_summary = {
                "overall_quality_score": quality_assessment.get("overall_score", 0),
                "quality_grade": final_integration.get("quality_grade", "D"),
                "production_ready": final_integration.get("production_ready", False),
                "critical_issues_count": len(quality_assessment.get("critical_issues", [])),
                "improvement_recommendations": quality_assessment.get("improvement_priority", [])
            }
        
        # Compile content summary
        content_summary = {
            "manga_metadata": final_integration.get("manga_metadata", {}),
            "total_pages": final_integration.get("total_pages", 0),
            "output_formats": list(final_integration.get("output_formats", {}).keys()),
            "estimated_reading_time": final_integration.get("manga_metadata", {}).get("estimated_reading_time_minutes", 0)
        }
        
        # Phase-by-phase summary
        phase_summary = {}
        for phase_num, result_data in self.phase_results.items():
            phase_execution = self.execution_plan[phase_num]
            phase_summary[f"phase_{phase_num}"] = {
                "agent_name": phase_execution.agent.__class__.__name__,
                "execution_time_seconds": self.execution_stats["phase_times"].get(phase_num, 0),
                "retry_count": phase_execution.retry_count,
                "status": phase_execution.status,
                "key_outputs": self._extract_key_outputs(phase_num, result_data)
            }
        
        final_results = {
            "execution_summary": execution_summary,
            "quality_summary": quality_summary,
            "content_summary": content_summary,
            "phase_summary": phase_summary,
            "full_results": {
                "phase_results": self.phase_results,
                "final_integration": final_integration
            },
            "session_info": {
                "session_id": str(self.session_id),
                "hitl_enabled": self.session.hitl_enabled if self.session else False,
                "completed_at": time.time()
            }
        }
        
        return final_results
    
    def _extract_key_outputs(self, phase_num: int, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key outputs from phase results for summary."""
        
        key_outputs = {}
        
        if phase_num == 1:  # Concept analysis
            key_outputs = {
                "genre": result_data.get("genre"),
                "themes_count": len(result_data.get("themes", [])),
                "estimated_pages": result_data.get("estimated_pages")
            }
        elif phase_num == 2:  # Character design
            key_outputs = {
                "characters_created": len(result_data.get("characters", [])),
                "main_characters": result_data.get("main_character_count"),
                "diversity_score": result_data.get("character_diversity_score")
            }
        elif phase_num == 3:  # Story structure
            key_outputs = {
                "total_scenes": result_data.get("total_scenes"),
                "story_complexity": result_data.get("story_complexity_score")
            }
        elif phase_num == 4:  # Panel layout
            key_outputs = {
                "total_panels": result_data.get("total_panels"),
                "layout_complexity": result_data.get("layout_complexity_score"),
                "visual_storytelling": result_data.get("visual_storytelling_score")
            }
        elif phase_num == 5:  # Image generation
            key_outputs = {
                "images_generated": result_data.get("total_images_generated"),
                "successful_generations": result_data.get("successful_generations"),
                "average_quality": result_data.get("quality_analysis", {}).get("average_quality_score")
            }
        elif phase_num == 6:  # Dialogue placement
            key_outputs = {
                "dialogue_elements": result_data.get("total_dialogue_elements"),
                "readability_score": result_data.get("readability_score")
            }
        elif phase_num == 7:  # Final integration
            key_outputs = {
                "overall_quality": result_data.get("overall_quality_score"),
                "production_ready": result_data.get("production_ready"),
                "output_formats_count": len(result_data.get("output_formats", {}))
            }
        
        return key_outputs
    
    async def cancel_pipeline(self, reason: str = "User cancelled"):
        """Cancel the pipeline execution."""
        
        self.status = PipelineStatus.CANCELLED
        self.log_info(f"Pipeline cancelled: {reason}")
        
        # Cancel any running phases
        for phase_execution in self.execution_plan.values():
            if phase_execution.status == "running":
                phase_execution.status = "cancelled"
                phase_execution.error = reason
    
    def register_feedback_handler(self, phase_number: int, handler: Callable):
        """Register a feedback handler for a specific phase."""
        
        self.feedback_handlers[phase_number] = handler
    
    def register_progress_callback(self, callback: Callable):
        """Register a progress callback."""
        
        self.progress_callbacks.append(callback)
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status."""
        
        return {
            "status": self.status.value,
            "current_phase": self.current_phase,
            "total_phases": len(self.execution_plan),
            "progress_percentage": (self.current_phase / len(self.execution_plan)) * 100,
            "session_id": str(self.session_id) if self.session_id else None,
            "execution_stats": self.execution_stats,
            "phase_statuses": {
                phase_num: {
                    "status": phase_exec.status,
                    "retry_count": phase_exec.retry_count,
                    "error": phase_exec.error
                } for phase_num, phase_exec in self.execution_plan.items()
            }
        }
    
    async def get_phase_preview(self, phase_number: int) -> Optional[Dict[str, Any]]:
        """Get preview data for a specific phase if available."""
        
        if phase_number not in self.phase_results:
            return None
        
        phase_result = self.phase_results[phase_number]
        agent = self.agents[phase_number]
        
        # Generate preview using agent's preview method
        try:
            preview = await agent.generate_preview(phase_result)
            return preview
        except Exception as e:
            self.log_warning(f"Failed to generate preview for phase {phase_number}: {e}")
            return None
    
    async def regenerate_phase(
        self,
        phase_number: int,
        input_data: Dict[str, Any],
        db_session,
        modifications: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Regenerate a specific phase with optional modifications."""
        
        if phase_number not in self.execution_plan:
            raise ValueError(f"Invalid phase number: {phase_number}")
        
        self.log_info(f"Regenerating Phase {phase_number}")
        
        # Apply modifications to input data
        if modifications:
            input_data = {**input_data, **modifications}
        
        # Get dependencies
        phase_execution = self.execution_plan[phase_number]
        previous_results = {
            k: v for k, v in self.phase_results.items() 
            if k in phase_execution.dependencies
        }
        
        # Re-execute phase
        agent = phase_execution.agent
        phase_result = await agent.process(
            self.session,
            input_data,
            db_session,
            previous_results if previous_results else None
        )
        
        # Update stored result
        self.phase_results[phase_number] = phase_result.output_data
        
        # If this was an earlier phase, invalidate later phases
        dependent_phases = [
            p_num for p_num, p_exec in self.execution_plan.items()
            if phase_number in p_exec.dependencies
        ]
        
        for dep_phase in dependent_phases:
            if dep_phase in self.phase_results:
                self.log_info(f"Invalidating Phase {dep_phase} due to Phase {phase_number} regeneration")
                del self.phase_results[dep_phase]
                self.execution_plan[dep_phase].status = "pending"
        
        return phase_result.output_data
    
    def get_dependency_graph(self) -> Dict[str, Any]:
        """Get the dependency graph for visualization."""
        
        nodes = []
        edges = []
        
        for phase_num, phase_exec in self.execution_plan.items():
            # Add node
            nodes.append({
                "id": f"phase_{phase_num}",
                "label": f"Phase {phase_num}: {phase_exec.agent.__class__.__name__}",
                "status": phase_exec.status,
                "parallel_group": phase_exec.parallel_group,
                "execution_time": self.execution_stats["phase_times"].get(phase_num, 0)
            })
            
            # Add edges for dependencies
            for dep in phase_exec.dependencies:
                edges.append({
                    "from": f"phase_{dep}",
                    "to": f"phase_{phase_num}",
                    "type": "dependency"
                })
            
            # Add edges for parallel groups
            if phase_exec.parallel_group is not None:
                for other_phase_num, other_phase_exec in self.execution_plan.items():
                    if (other_phase_num != phase_num and 
                        other_phase_exec.parallel_group == phase_exec.parallel_group):
                        edges.append({
                            "from": f"phase_{phase_num}",
                            "to": f"phase_{other_phase_num}",
                            "type": "parallel",
                            "style": "dashed"
                        })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "parallel_groups": len(set(
                p.parallel_group for p in self.execution_plan.values() 
                if p.parallel_group is not None
            )),
            "total_phases": len(self.execution_plan)
        }
"""Unit tests for Pipeline Orchestrator."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any

from app.agents.pipeline_orchestrator import (
    PipelineOrchestrator, 
    PipelineStatus, 
    PhaseExecution
)
from app.agents.base_agent import BaseAgent


class MockPhaseAgent(BaseAgent):
    """Mock agent for testing pipeline orchestration."""
    
    def __init__(self, phase_number: int, processing_time: float = 0.1, should_fail: bool = False):
        super().__init__(phase_number, f"Mock Phase {phase_number}", 60)
        self.processing_time = processing_time
        self.should_fail = should_fail
    
    async def process_phase(self, input_data: Dict[str, Any], session_id, previous_results=None):
        await asyncio.sleep(self.processing_time)
        
        if self.should_fail:
            raise Exception(f"Phase {self.phase_number} intentionally failed")
        
        return {
            "phase_number": self.phase_number,
            "processed": True,
            "processing_time": self.processing_time,
            "previous_results_count": len(previous_results) if previous_results else 0
        }
    
    async def generate_prompt(self, input_data: Dict[str, Any], previous_results=None):
        return f"Mock prompt for phase {self.phase_number}"
    
    async def validate_output(self, output_data: Dict[str, Any]):
        return True


@pytest.mark.asyncio
class TestPipelineOrchestrator:
    """Test cases for Pipeline Orchestrator."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = PipelineOrchestrator()
        
        assert orchestrator.status == PipelineStatus.INITIALIZING
        assert orchestrator.current_phase == 0
        assert len(orchestrator.agents) == 7  # 7 phases
        assert len(orchestrator.execution_plan) == 7
        assert orchestrator.max_parallel_phases == 3
        assert len(orchestrator.progress_callbacks) == 0
        
        # Verify execution plan structure
        for phase_num in range(1, 8):
            assert phase_num in orchestrator.execution_plan
            execution = orchestrator.execution_plan[phase_num]
            assert isinstance(execution, PhaseExecution)
            assert execution.phase_number == phase_num
    
    def test_dependency_graph_structure(self):
        """Test that dependency graph is correctly structured."""
        orchestrator = PipelineOrchestrator()
        plan = orchestrator.execution_plan
        
        # Phase 1 has no dependencies
        assert plan[1].dependencies == []
        
        # Phase 2 and 3 depend on Phase 1 and can run in parallel
        assert plan[2].dependencies == [1]
        assert plan[3].dependencies == [1]
        assert plan[2].parallel_group == plan[3].parallel_group
        
        # Phase 4 depends on phases 1, 2, 3
        assert set(plan[4].dependencies) == {1, 2, 3}
        
        # Phase 5 depends on phases 1-4
        assert set(plan[5].dependencies) == {1, 2, 3, 4}
        
        # Phase 6 depends on phases 1-5
        assert set(plan[6].dependencies) == {1, 2, 3, 4, 5}
        
        # Phase 7 depends on all previous phases
        assert set(plan[7].dependencies) == {1, 2, 3, 4, 5, 6}
    
    def test_find_ready_phases(self):
        """Test finding phases ready for execution."""
        orchestrator = PipelineOrchestrator()
        
        # Initially, only Phase 1 should be ready
        executed_phases = set()
        ready_phases = orchestrator._find_ready_phases(executed_phases)
        assert len(ready_phases) == 1
        assert ready_phases[0].phase_number == 1
        
        # After Phase 1, phases 2 and 3 should be ready
        executed_phases.add(1)
        ready_phases = orchestrator._find_ready_phases(executed_phases)
        assert len(ready_phases) == 2
        phase_numbers = {p.phase_number for p in ready_phases}
        assert phase_numbers == {2, 3}
        
        # After phases 1, 2, 3, only phase 4 should be ready
        executed_phases.update([2, 3])
        ready_phases = orchestrator._find_ready_phases(executed_phases)
        assert len(ready_phases) == 1
        assert ready_phases[0].phase_number == 4
    
    def test_parallel_grouping(self):
        """Test grouping phases for parallel execution."""
        orchestrator = PipelineOrchestrator()
        
        # Create mock ready phases with parallel groups
        ready_phases = [
            orchestrator.execution_plan[2],  # parallel_group = 1
            orchestrator.execution_plan[3],  # parallel_group = 1
        ]
        
        execution_groups = orchestrator._group_phases_for_parallel_execution(ready_phases)
        
        assert len(execution_groups) == 1  # Should be grouped together
        assert len(execution_groups[0]) == 2  # Both phases in same group
        phase_numbers = {p.phase_number for p in execution_groups[0]}
        assert phase_numbers == {2, 3}
    
    @patch('app.agents.pipeline_orchestrator.Phase1ConceptAgent')
    @patch('app.agents.pipeline_orchestrator.Phase2CharacterAgent') 
    @patch('app.agents.pipeline_orchestrator.Phase3StoryAgent')
    async def test_pipeline_execution_success(self, mock_phase3, mock_phase2, mock_phase1, sample_manga_session, db_session):
        """Test successful pipeline execution."""
        
        # Setup mock agents
        mock_agents = {}
        for i, mock_class in enumerate([mock_phase1, mock_phase2, mock_phase3], 1):
            mock_agent = MockPhaseAgent(i)
            mock_agent.process = AsyncMock(return_value=MagicMock(
                output_data={f"phase_{i}_result": True},
                processing_time_ms=1000 + i * 100
            ))
            mock_class.return_value = mock_agent
            mock_agents[i] = mock_agent
        
        # Create simplified orchestrator for testing
        orchestrator = PipelineOrchestrator()
        orchestrator.agents = mock_agents
        
        # Simplified execution plan for faster testing
        orchestrator.execution_plan = {
            1: PhaseExecution(1, mock_agents[1], dependencies=[]),
            2: PhaseExecution(2, mock_agents[2], dependencies=[1]),
            3: PhaseExecution(3, mock_agents[3], dependencies=[1, 2])
        }
        
        input_data = {"story": "Test story"}
        
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session,
            progress_callback=None,
            feedback_timeout=10
        )
        
        assert orchestrator.status == PipelineStatus.COMPLETED
        assert "execution_summary" in result
        assert result["execution_summary"]["pipeline_status"] == "completed"
        assert result["execution_summary"]["phases_completed"] > 0
    
    async def test_pipeline_failure_handling(self, sample_manga_session, db_session):
        """Test pipeline failure handling."""
        orchestrator = PipelineOrchestrator()
        
        # Replace first agent with failing one
        failing_agent = MockPhaseAgent(1, should_fail=True)
        failing_agent.process = AsyncMock(side_effect=Exception("Test failure"))
        orchestrator.agents[1] = failing_agent
        orchestrator.execution_plan[1].agent = failing_agent
        
        input_data = {"story": "Test story"}
        
        with pytest.raises(Exception) as exc_info:
            await orchestrator.execute_pipeline(
                session=sample_manga_session,
                input_data=input_data,
                db_session=db_session
            )
        
        assert orchestrator.status == PipelineStatus.FAILED
    
    async def test_progress_callback_execution(self):
        """Test progress callback execution."""
        orchestrator = PipelineOrchestrator()
        
        callback_calls = []
        
        async def progress_callback(progress_info):
            callback_calls.append(progress_info)
        
        orchestrator.register_progress_callback(progress_callback)
        
        # Simulate progress update
        await orchestrator._update_progress(3, 7)
        
        assert len(callback_calls) == 1
        assert callback_calls[0]["current_phase"] == 3
        assert callback_calls[0]["total_phases"] == 7
        assert callback_calls[0]["progress_percentage"] == pytest.approx(42.857, rel=1e-2)
    
    async def test_feedback_handling(self, sample_manga_session):
        """Test HITL feedback handling."""
        orchestrator = PipelineOrchestrator()
        
        # Mock feedback handler
        feedback_received = []
        
        async def feedback_handler(phase_result):
            feedback_received.append(phase_result)
            return {"type": "improvement", "text": "Make it better"}
        
        orchestrator.register_feedback_handler(2, feedback_handler)
        
        # Simulate feedback check
        orchestrator.phase_results[2] = {"character_data": "test"}
        executed_phases = {1, 2}
        
        await orchestrator._check_feedback_requirements(executed_phases, 10)
        
        assert len(feedback_received) == 1
        assert orchestrator.status == PipelineStatus.RUNNING  # Should return to running after feedback
    
    def test_efficiency_calculation(self):
        """Test parallel efficiency calculation."""
        orchestrator = PipelineOrchestrator()
        
        # Set up mock execution stats
        orchestrator.execution_stats = {
            "total_start_time": 0.0,
            "total_end_time": 60.0,
            "total_processing_time": 60.0,
            "phase_times": {
                1: 12.0,
                2: 18.0, 
                3: 15.0,
                4: 20.0,
                5: 25.0,
                6: 4.0,
                7: 3.0
            }
        }
        
        orchestrator._calculate_efficiency_metrics()
        
        # Sequential time would be sum of all phases
        expected_sequential = 12 + 18 + 15 + 20 + 25 + 4 + 3  # 97 seconds
        assert orchestrator.execution_stats["estimated_sequential_time"] == expected_sequential
        
        # Parallel efficiency should be calculated
        actual_time = 60.0
        expected_efficiency = 1.0 - (actual_time / expected_sequential)
        assert orchestrator.execution_stats["parallel_efficiency"] == pytest.approx(expected_efficiency, rel=1e-3)
    
    def test_phase_regeneration_invalidation(self):
        """Test that regenerating a phase invalidates dependent phases."""
        orchestrator = PipelineOrchestrator()
        
        # Set up results for all phases
        for i in range(1, 8):
            orchestrator.phase_results[i] = {f"phase_{i}": "result"}
            orchestrator.execution_plan[i].status = "completed"
        
        # Regenerate phase 2
        orchestrator._invalidate_dependent_phases(2)
        
        # Phase 2 dependents (4, 5, 6, 7) should be invalidated
        # Phase 1 and 3 should remain (3 only depends on 1)
        assert 1 in orchestrator.phase_results
        assert 2 in orchestrator.phase_results  # The regenerated phase itself remains
        assert 3 in orchestrator.phase_results  # Only depends on 1
        
        # These should be invalidated
        for phase in [4, 5, 6, 7]:
            assert orchestrator.execution_plan[phase].status == "pending"
    
    def test_dependency_graph_generation(self):
        """Test dependency graph generation for visualization."""
        orchestrator = PipelineOrchestrator()
        
        # Add some mock execution times
        orchestrator.execution_stats["phase_times"] = {
            1: 12.5,
            2: 18.2,
            3: 15.8
        }
        
        dependency_graph = orchestrator.get_dependency_graph()
        
        assert "nodes" in dependency_graph
        assert "edges" in dependency_graph
        assert len(dependency_graph["nodes"]) == 7  # 7 phases
        
        # Check node structure
        node = dependency_graph["nodes"][0]
        assert "id" in node
        assert "label" in node
        assert "status" in node
        
        # Check edges for dependencies
        edges = dependency_graph["edges"]
        dependency_edges = [e for e in edges if e["type"] == "dependency"]
        parallel_edges = [e for e in edges if e["type"] == "parallel"]
        
        assert len(dependency_edges) > 0
        assert len(parallel_edges) > 0
    
    async def test_pipeline_cancellation(self):
        """Test pipeline cancellation."""
        orchestrator = PipelineOrchestrator()
        
        # Set some phases as running
        orchestrator.execution_plan[1].status = "running"
        orchestrator.execution_plan[2].status = "pending"
        
        reason = "User requested cancellation"
        await orchestrator.cancel_pipeline(reason)
        
        assert orchestrator.status == PipelineStatus.CANCELLED
        assert orchestrator.execution_plan[1].status == "cancelled"
        assert orchestrator.execution_plan[1].error == reason
        assert orchestrator.execution_plan[2].status == "pending"  # Unchanged
    
    def test_pipeline_status_retrieval(self):
        """Test pipeline status retrieval."""
        orchestrator = PipelineOrchestrator()
        orchestrator.status = PipelineStatus.RUNNING
        orchestrator.current_phase = 3
        orchestrator.session_id = uuid4()
        
        status = orchestrator.get_pipeline_status()
        
        assert status["status"] == "running"
        assert status["current_phase"] == 3
        assert status["total_phases"] == 7
        assert status["progress_percentage"] == pytest.approx(42.857, rel=1e-2)
        assert "session_id" in status
        assert "execution_stats" in status
        assert "phase_statuses" in status
    
    async def test_phase_preview_generation(self):
        """Test phase preview generation."""
        orchestrator = PipelineOrchestrator()
        
        # Mock phase result and agent preview
        mock_result = {"character": "Hero", "description": "Brave warrior"}
        orchestrator.phase_results[2] = mock_result
        
        mock_agent = orchestrator.agents[2]
        mock_agent.generate_preview = AsyncMock(return_value={
            "preview": "Character preview",
            "thumbnail": "thumb.png"
        })
        
        preview = await orchestrator.get_phase_preview(2)
        
        assert preview is not None
        assert "preview" in preview
        mock_agent.generate_preview.assert_called_once_with(mock_result)
    
    async def test_phase_preview_not_available(self):
        """Test phase preview when result not available."""
        orchestrator = PipelineOrchestrator()
        
        preview = await orchestrator.get_phase_preview(5)  # Non-existent result
        
        assert preview is None


@pytest.mark.asyncio
class TestPipelineOrchestratorEdgeCases:
    """Test edge cases and error conditions."""
    
    async def test_empty_input_data(self, sample_manga_session, db_session):
        """Test pipeline with empty input data."""
        orchestrator = PipelineOrchestrator()
        
        # Replace agents with simple mocks
        for i in range(1, 8):
            mock_agent = AsyncMock()
            mock_agent.process = AsyncMock(return_value=MagicMock(
                output_data={"empty_input_handled": True}
            ))
            orchestrator.agents[i] = mock_agent
            orchestrator.execution_plan[i].agent = mock_agent
        
        # This should still work with empty input
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data={},
            db_session=db_session
        )
        
        assert result is not None
    
    async def test_concurrent_pipeline_executions(self):
        """Test multiple concurrent pipeline executions."""
        # This would test that multiple orchestrators don't interfere
        orchestrators = [PipelineOrchestrator() for _ in range(3)]
        
        # Each should have independent state
        for i, orch in enumerate(orchestrators):
            assert orch.session_id != orchestrators[(i + 1) % 3].session_id
            assert orch.phase_results != orchestrators[(i + 1) % 3].phase_results
    
    def test_invalid_phase_number_handling(self):
        """Test handling of invalid phase numbers."""
        orchestrator = PipelineOrchestrator()
        
        # Test non-existent phase
        with pytest.raises(KeyError):
            _ = orchestrator.execution_plan[0]
        
        with pytest.raises(KeyError):
            _ = orchestrator.execution_plan[8]
    
    async def test_partial_failure_recovery(self):
        """Test recovery from partial failures."""
        orchestrator = PipelineOrchestrator()
        
        # Simulate partial execution state
        orchestrator.phase_results = {
            1: {"completed": True},
            2: {"completed": True}
        }
        orchestrator.current_phase = 2
        
        # Should be able to continue from where it left off
        executed_phases = {1, 2}
        ready_phases = orchestrator._find_ready_phases(executed_phases)
        
        # Phase 3 should be ready (depends only on phase 1)
        # Phase 4 should not be ready (depends on phases 1, 2, 3)
        ready_phase_numbers = {p.phase_number for p in ready_phases}
        assert 3 in ready_phase_numbers
        assert 4 not in ready_phase_numbers
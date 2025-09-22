import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.pipeline_service import HITLCapablePipelineOrchestrator
from app.services.hitl_service import (
    HITLStateManager,
    HITLService,
    HITLSessionState,
    HITLSessionError,
    HITLStateError
)
from app.db.models import MangaSession


class TestHITLIntegration:
    """Integration tests for HITL (Human-in-the-Loop) system"""

    @pytest.fixture
    def mock_session_factory(self):
        """Mock session factory for database operations"""
        return Mock()

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.fixture
    def mock_session_scope(self, mock_db_session):
        """Mock session scope context manager"""
        async def mock_scope(session_factory):
            class MockScope:
                async def __aenter__(self):
                    return mock_db_session
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return MockScope()
        return mock_scope

    @pytest.fixture
    def orchestrator(self, mock_session_factory):
        """Create HITLCapablePipelineOrchestrator for testing"""
        with patch('app.services.pipeline_service.core_settings.get_settings') as mock_settings:
            mock_settings.return_value.hitl_enabled = True
            mock_settings.return_value.hitl_max_iterations = 3
            mock_settings.return_value.hitl_feedback_timeout_minutes = 30
            mock_settings.return_value.is_hitl_enabled_for_phase.return_value = True
            return HITLCapablePipelineOrchestrator(mock_session_factory)

    @pytest.fixture
    def manga_session(self):
        """Create mock manga session"""
        session = Mock(spec=MangaSession)
        session.request_id = uuid4()
        session.id = uuid4()
        return session

    @pytest.fixture
    def phase_config(self):
        """Phase configuration for testing"""
        return {
            "phase": 1,
            "name": "concept_generation",
            "enabled": True,
            "model": "gemini-2.5"
        }

    @pytest.fixture
    def test_context(self):
        """Execution context for testing"""
        return {1: {"user_prompt": "Create a fantasy manga about dragons"}}

    @pytest.fixture
    def initial_result(self):
        """Initial phase result"""
        return {
            "generated_images": ["concept1.jpg", "concept2.jpg"],
            "generated_text": "A story about a young dragon trainer",
            "characters": [{"name": "Akira", "description": "Dragon trainer"}],
            "metadata": {"quality_score": 0.75, "generation_time": 1.5}
        }

    @pytest.mark.asyncio
    async def test_hitl_approval_workflow(self, orchestrator, manga_session, phase_config, test_context, initial_result, mock_session_scope):
        """Test complete HITL workflow with user approval"""
        with patch('app.services.pipeline_service.session_scope', mock_session_scope):
            with patch('app.services.pipeline_service.realtime_hub.publish') as mock_publish:
                with patch.object(orchestrator, '_execute_single_phase') as mock_execute:
                    with patch.object(orchestrator, '_wait_for_user_feedback') as mock_wait:

                        # Setup mocks
                        mock_execute.return_value = initial_result
                        mock_wait.return_value = {"feedback_type": "approval"}

                        # Execute HITL-enabled phase
                        result = await orchestrator._execute_single_phase_with_hitl(
                            manga_session, phase_config, test_context
                        )

                        # Verify result contains HITL metadata
                        assert result["metadata"]["hitl_processed"] is True
                        assert result["metadata"]["final_state"] == "completed"
                        assert result["metadata"]["feedback_iterations"] == 0

                        # Verify WebSocket notifications were sent
                        assert mock_publish.call_count >= 2  # feedback_required + feedback_approved

                        # Verify approval notification
                        approval_calls = [call for call in mock_publish.call_args_list
                                        if "feedback_approved" in str(call)]
                        assert len(approval_calls) >= 1

    @pytest.mark.asyncio
    async def test_hitl_modification_workflow(self, orchestrator, manga_session, phase_config, test_context, initial_result, mock_session_scope):
        """Test complete HITL workflow with user modification"""
        with patch('app.services.pipeline_service.session_scope', mock_session_scope):
            with patch('app.services.pipeline_service.realtime_hub.publish') as mock_publish:
                with patch.object(orchestrator, '_execute_single_phase') as mock_execute:
                    with patch.object(orchestrator, '_wait_for_user_feedback') as mock_wait:
                        with patch.object(orchestrator, '_regenerate_with_feedback') as mock_regenerate:

                            # Setup mocks for modification workflow
                            mock_execute.return_value = initial_result

                            # First feedback: modification request
                            # Second feedback: approval
                            mock_wait.side_effect = [
                                {"feedback_type": "modification", "natural_language_input": "Make dragons more colorful"},
                                {"feedback_type": "approval"}
                            ]

                            modified_result = {
                                **initial_result,
                                "generated_images": ["colorful_concept1.jpg", "colorful_concept2.jpg"],
                                "metadata": {"quality_score": 0.85, "modification_applied": True}
                            }
                            mock_regenerate.return_value = modified_result

                            # Execute HITL-enabled phase
                            result = await orchestrator._execute_single_phase_with_hitl(
                                manga_session, phase_config, test_context
                            )

                            # Verify result contains HITL metadata with iteration
                            assert result["metadata"]["hitl_processed"] is True
                            assert result["metadata"]["final_state"] == "completed"
                            assert result["metadata"]["feedback_iterations"] == 1

                            # Verify regeneration was called
                            mock_regenerate.assert_called_once()

                            # Verify WebSocket notifications were sent
                            assert mock_publish.call_count >= 4  # feedback_required + processing + regeneration_complete + approved

    @pytest.mark.asyncio
    async def test_hitl_skip_workflow(self, orchestrator, manga_session, phase_config, test_context, initial_result, mock_session_scope):
        """Test complete HITL workflow with user skip"""
        with patch('app.services.pipeline_service.session_scope', mock_session_scope):
            with patch('app.services.pipeline_service.realtime_hub.publish') as mock_publish:
                with patch.object(orchestrator, '_execute_single_phase') as mock_execute:
                    with patch.object(orchestrator, '_wait_for_user_feedback') as mock_wait:

                        # Setup mocks
                        mock_execute.return_value = initial_result
                        mock_wait.return_value = {"feedback_type": "skip"}

                        # Execute HITL-enabled phase
                        result = await orchestrator._execute_single_phase_with_hitl(
                            manga_session, phase_config, test_context
                        )

                        # Verify result contains HITL metadata
                        assert result["metadata"]["hitl_processed"] is True
                        assert result["metadata"]["final_state"] == "completed"
                        assert result["metadata"]["feedback_iterations"] == 0

                        # Verify skip notification
                        skip_calls = [call for call in mock_publish.call_args_list
                                    if "feedback_skipped" in str(call)]
                        assert len(skip_calls) >= 1

    @pytest.mark.asyncio
    async def test_hitl_timeout_workflow(self, orchestrator, manga_session, phase_config, test_context, initial_result, mock_session_scope):
        """Test complete HITL workflow with timeout"""
        with patch('app.services.pipeline_service.session_scope', mock_session_scope):
            with patch('app.services.pipeline_service.realtime_hub.publish') as mock_publish:
                with patch.object(orchestrator, '_execute_single_phase') as mock_execute:
                    with patch.object(orchestrator, '_wait_for_user_feedback') as mock_wait:

                        # Setup mocks
                        mock_execute.return_value = initial_result
                        mock_wait.return_value = None  # Timeout

                        # Execute HITL-enabled phase
                        result = await orchestrator._execute_single_phase_with_hitl(
                            manga_session, phase_config, test_context
                        )

                        # Verify result contains HITL metadata
                        assert result["metadata"]["hitl_processed"] is True
                        assert result["metadata"]["final_state"] == "timeout"

                        # Verify timeout notification
                        timeout_calls = [call for call in mock_publish.call_args_list
                                       if "feedback_timeout" in str(call)]
                        assert len(timeout_calls) >= 1

    @pytest.mark.asyncio
    async def test_hitl_max_iterations_exceeded(self, orchestrator, manga_session, phase_config, test_context, initial_result, mock_session_scope):
        """Test HITL workflow when max iterations exceeded"""
        with patch('app.services.pipeline_service.session_scope', mock_session_scope):
            with patch('app.services.pipeline_service.realtime_hub.publish') as mock_publish:
                with patch.object(orchestrator, '_execute_single_phase') as mock_execute:
                    with patch.object(orchestrator, '_wait_for_user_feedback') as mock_wait:
                        with patch.object(orchestrator, '_regenerate_with_feedback') as mock_regenerate:

                            # Setup mocks
                            mock_execute.return_value = initial_result

                            # Multiple modification requests
                            mock_wait.return_value = {"feedback_type": "modification", "natural_language_input": "Change again"}
                            mock_regenerate.return_value = initial_result

                            # Execute HITL-enabled phase
                            result = await orchestrator._execute_single_phase_with_hitl(
                                manga_session, phase_config, test_context
                            )

                            # Verify result contains HITL metadata
                            assert result["metadata"]["hitl_processed"] is True
                            # Should stop after max iterations (3)
                            assert result["metadata"]["feedback_iterations"] == 3
                            assert result["metadata"]["final_state"] == "error"

    @pytest.mark.asyncio
    async def test_hitl_error_recovery(self, orchestrator, manga_session, phase_config, test_context, initial_result, mock_session_scope):
        """Test HITL error recovery and fallback"""
        with patch('app.services.pipeline_service.session_scope', mock_session_scope):
            with patch.object(orchestrator, '_execute_single_phase') as mock_execute:
                with patch.object(orchestrator, '_get_hitl_state_manager') as mock_get_manager:

                    # Setup mocks
                    mock_execute.return_value = initial_result

                    # Mock state manager to raise error
                    mock_manager = AsyncMock()
                    mock_manager.start_hitl_session.side_effect = HITLSessionError(
                        session_id=manga_session.request_id,
                        message="Database connection failed"
                    )
                    mock_get_manager.return_value = mock_manager

                    # Execute HITL-enabled phase
                    result = await orchestrator._execute_single_phase_with_hitl(
                        manga_session, phase_config, test_context
                    )

                    # Should fallback to initial result with error metadata
                    assert result["metadata"]["hitl_processed"] is True
                    assert result["metadata"]["hitl_error"] is True
                    assert result["metadata"]["hitl_error_type"] == "session_error"
                    assert "Database connection failed" in result["metadata"]["hitl_error_message"]

    @pytest.mark.asyncio
    async def test_hitl_disabled_for_phase(self, orchestrator, manga_session, phase_config, test_context, initial_result):
        """Test behavior when HITL is disabled for specific phase"""
        with patch.object(orchestrator, '_is_hitl_enabled_for_phase') as mock_enabled:
            with patch.object(orchestrator, '_execute_single_phase') as mock_execute:

                # Setup mocks
                mock_enabled.return_value = False
                mock_execute.return_value = initial_result

                # Execute phase with HITL disabled
                result = await orchestrator._execute_single_phase_with_hitl(
                    manga_session, phase_config, test_context
                )

                # Should return original result without HITL processing
                assert result == initial_result
                assert "hitl_processed" not in result.get("metadata", {})

    @pytest.mark.asyncio
    async def test_hitl_preview_data_extraction(self, orchestrator):
        """Test preview data extraction for different result types"""
        # Test with images
        image_result = {
            "generated_images": ["image1.jpg", "image2.jpg"],
            "metadata": {"quality": 0.8}
        }
        preview = orchestrator._extract_preview_data(image_result)
        assert preview["images"] == ["image1.jpg", "image2.jpg"]
        assert preview["metadata"]["quality"] == 0.8

        # Test with text
        text_result = {
            "generated_text": "Story concept",
            "characters": [{"name": "Hero"}]
        }
        preview = orchestrator._extract_preview_data(text_result)
        assert preview["text"] == "Story concept"
        assert preview["characters"] == [{"name": "Hero"}]

        # Test with empty result
        empty_preview = orchestrator._extract_preview_data({})
        assert empty_preview is None

    @pytest.mark.asyncio
    async def test_hitl_feedback_options_generation(self, orchestrator, mock_session_scope):
        """Test feedback options generation for different phases"""
        with patch('app.services.pipeline_service.session_scope', mock_session_scope):

            # Test default options when no templates
            options = await orchestrator._get_feedback_options_for_phase(1)

            assert len(options) == 3
            option_types = [opt["option_type"] for opt in options]
            assert "approval" in option_types
            assert "modification" in option_types
            assert "skip" in option_types

            # Verify options are sorted by display_order
            display_orders = [opt["display_order"] for opt in options]
            assert display_orders == sorted(display_orders)

    @pytest.mark.asyncio
    async def test_hitl_state_transitions(self, orchestrator, manga_session, phase_config, test_context, initial_result, mock_session_scope):
        """Test HITL state transitions during workflow"""
        with patch('app.services.pipeline_service.session_scope', mock_session_scope):
            with patch('app.services.pipeline_service.realtime_hub.publish') as mock_publish:
                with patch.object(orchestrator, '_execute_single_phase') as mock_execute:
                    with patch.object(orchestrator, '_wait_for_user_feedback') as mock_wait:

                        mock_execute.return_value = initial_result
                        mock_wait.return_value = {"feedback_type": "approval"}

                        # Track state transitions through WebSocket calls
                        await orchestrator._execute_single_phase_with_hitl(
                            manga_session, phase_config, test_context
                        )

                        # Verify state progression through WebSocket events
                        event_types = []
                        for call_args in mock_publish.call_args_list:
                            if len(call_args[0]) > 1:
                                event = call_args[0][1]
                                if hasattr(event, 'get') and event.get('type'):
                                    event_types.append(event['type'])

                        # Should include feedback_required and feedback_approved events
                        assert any('feedback_required' in event_type for event_type in event_types)
                        assert any('feedback_approved' in event_type for event_type in event_types)
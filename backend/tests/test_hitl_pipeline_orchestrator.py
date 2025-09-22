import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

from app.services.pipeline_service import HITLCapablePipelineOrchestrator
from app.services.hitl_service import HITLStateManager, HITLService, HITLSessionContext, HITLSessionState
from app.db.models import MangaSession


class TestHITLCapablePipelineOrchestrator:
    """Test suite for HITLCapablePipelineOrchestrator"""

    @pytest.fixture
    def mock_session_factory(self):
        """Mock session factory"""
        return Mock()

    @pytest.fixture
    def orchestrator(self, mock_session_factory):
        """Create HITLCapablePipelineOrchestrator instance for testing"""
        with patch('app.services.pipeline_service.core_settings.get_settings') as mock_settings:
            mock_settings.return_value.hitl_enabled = True
            mock_settings.return_value.hitl_max_iterations = 3
            mock_settings.return_value.hitl_feedback_timeout_minutes = 30
            return HITLCapablePipelineOrchestrator(mock_session_factory)

    @pytest.fixture
    def mock_session(self):
        """Create mock MangaSession"""
        session = Mock(spec=MangaSession)
        session.request_id = uuid4()
        session.id = uuid4()
        return session

    @pytest.fixture
    def phase_config(self):
        """Create test phase configuration"""
        return {
            "phase": 1,
            "name": "concept_generation",
            "enabled": True
        }

    @pytest.fixture
    def test_context(self):
        """Create test execution context"""
        return {1: {"previous_result": "test"}}

    @pytest.fixture
    def test_result(self):
        """Create test phase result"""
        return {
            "generated_images": ["image1.jpg", "image2.jpg"],
            "generated_text": "Test concept",
            "metadata": {"quality_score": 0.85}
        }

    @pytest.mark.asyncio
    async def test_init_with_settings(self, mock_session_factory):
        """Test orchestrator initialization with settings"""
        with patch('app.services.pipeline_service.core_settings.get_settings') as mock_settings:
            mock_settings.return_value.hitl_enabled = True
            mock_settings.return_value.hitl_max_iterations = 5
            mock_settings.return_value.hitl_feedback_timeout_minutes = 45

            orchestrator = HITLCapablePipelineOrchestrator(mock_session_factory)

            assert orchestrator.is_hitl_enabled is True
            assert orchestrator.max_feedback_iterations == 5
            assert orchestrator.feedback_timeout_minutes == 45

    @pytest.mark.asyncio
    async def test_init_with_settings_fallback(self, mock_session_factory):
        """Test orchestrator initialization with settings fallback"""
        with patch('app.services.pipeline_service.core_settings.get_settings') as mock_settings:
            mock_settings.side_effect = Exception("Settings error")

            orchestrator = HITLCapablePipelineOrchestrator(mock_session_factory)

            # Should use fallback values
            assert orchestrator.is_hitl_enabled is True
            assert orchestrator.max_feedback_iterations == 3
            assert orchestrator.feedback_timeout_minutes == 30

    @pytest.mark.asyncio
    async def test_is_hitl_enabled_for_phase_with_settings(self, orchestrator):
        """Test HITL phase enablement check with settings"""
        with patch('app.services.pipeline_service.core_settings.get_settings') as mock_settings:
            mock_settings.return_value.is_hitl_enabled_for_phase.return_value = True

            result = orchestrator._is_hitl_enabled_for_phase(1)
            assert result is True

            mock_settings.return_value.is_hitl_enabled_for_phase.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_is_hitl_enabled_for_phase_fallback(self, orchestrator):
        """Test HITL phase enablement check with fallback"""
        with patch('app.services.pipeline_service.core_settings.get_settings') as mock_settings:
            mock_settings.side_effect = Exception("Settings error")

            # Should fallback to phase 1 and 2
            assert orchestrator._is_hitl_enabled_for_phase(1) is True
            assert orchestrator._is_hitl_enabled_for_phase(2) is True
            assert orchestrator._is_hitl_enabled_for_phase(3) is False

    @pytest.mark.asyncio
    async def test_is_hitl_enabled_for_phase_disabled(self, orchestrator):
        """Test HITL phase enablement when globally disabled"""
        orchestrator.is_hitl_enabled = False

        result = orchestrator._is_hitl_enabled_for_phase(1)
        assert result is False

    @pytest.mark.asyncio
    async def test_extract_preview_data(self, orchestrator, test_result):
        """Test preview data extraction"""
        preview_data = orchestrator._extract_preview_data(test_result)

        assert preview_data is not None
        assert preview_data["images"] == ["image1.jpg", "image2.jpg"]
        assert preview_data["text"] == "Test concept"
        assert preview_data["metadata"]["quality_score"] == 0.85

    @pytest.mark.asyncio
    async def test_extract_preview_data_empty(self, orchestrator):
        """Test preview data extraction with empty result"""
        preview_data = orchestrator._extract_preview_data({})
        assert preview_data is None

        preview_data = orchestrator._extract_preview_data(None)
        assert preview_data is None

    @pytest.mark.asyncio
    async def test_add_hitl_error_metadata(self, orchestrator, test_result):
        """Test adding HITL error metadata"""
        error_type = "database_error"
        error_message = "Connection failed"

        result = orchestrator._add_hitl_error_metadata(test_result, error_type, error_message)

        assert result["metadata"]["hitl_processed"] is True
        assert result["metadata"]["hitl_error"] is True
        assert result["metadata"]["hitl_error_type"] == error_type
        assert result["metadata"]["hitl_error_message"] == error_message
        assert "hitl_error_timestamp" in result["metadata"]

    @pytest.mark.asyncio
    async def test_get_feedback_options_for_phase(self, orchestrator):
        """Test getting feedback options for phase"""
        with patch('app.services.pipeline_service.session_scope') as mock_scope:
            mock_db = AsyncMock()
            mock_scope.return_value.__aenter__.return_value = mock_db
            mock_db.execute.return_value.scalars.return_value.all.return_value = []

            options = await orchestrator._get_feedback_options_for_phase(1)

            # Should return default options when no templates found
            assert len(options) == 3
            assert any(opt["option_type"] == "approval" for opt in options)
            assert any(opt["option_type"] == "modification" for opt in options)
            assert any(opt["option_type"] == "skip" for opt in options)

    @pytest.mark.asyncio
    async def test_execute_single_phase_with_hitl_disabled(self, orchestrator, mock_session, phase_config, test_context):
        """Test HITL phase execution when disabled for phase"""
        with patch.object(orchestrator, '_is_hitl_enabled_for_phase') as mock_enabled:
            with patch.object(orchestrator, '_execute_single_phase') as mock_execute:
                mock_enabled.return_value = False
                mock_execute.return_value = {"test": "result"}

                result = await orchestrator._execute_single_phase_with_hitl(
                    mock_session, phase_config, test_context
                )

                assert result == {"test": "result"}
                mock_execute.assert_called_once_with(mock_session, phase_config, test_context)

    @pytest.mark.asyncio
    async def test_execute_single_phase_with_hitl_enabled(self, orchestrator, mock_session, phase_config, test_context):
        """Test HITL phase execution when enabled"""
        with patch.object(orchestrator, '_is_hitl_enabled_for_phase') as mock_enabled:
            with patch.object(orchestrator, '_execute_single_phase') as mock_execute:
                with patch.object(orchestrator, '_process_hitl_feedback_cycle') as mock_process:
                    mock_enabled.return_value = True
                    mock_execute.return_value = {"initial": "result"}
                    mock_process.return_value = {"final": "result"}

                    result = await orchestrator._execute_single_phase_with_hitl(
                        mock_session, phase_config, test_context
                    )

                    assert result == {"final": "result"}
                    mock_execute.assert_called_once()
                    mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_single_phase_with_hitl_error_fallback(self, orchestrator, mock_session, phase_config, test_context):
        """Test HITL phase execution with error fallback"""
        with patch.object(orchestrator, '_is_hitl_enabled_for_phase') as mock_enabled:
            with patch.object(orchestrator, '_execute_single_phase') as mock_execute:
                with patch.object(orchestrator, '_process_hitl_feedback_cycle') as mock_process:
                    mock_enabled.return_value = True
                    mock_execute.return_value = {"initial": "result"}
                    mock_process.side_effect = Exception("HITL error")

                    result = await orchestrator._execute_single_phase_with_hitl(
                        mock_session, phase_config, test_context
                    )

                    # Should fallback to initial result
                    assert result == {"initial": "result"}

    @pytest.mark.asyncio
    async def test_get_hitl_service(self, orchestrator):
        """Test HITL service getter with caching"""
        mock_db = AsyncMock()

        # First call should create service
        service1 = await orchestrator._get_hitl_service(mock_db)
        assert service1 is not None
        assert orchestrator._hitl_service is service1

        # Second call should return cached service
        service2 = await orchestrator._get_hitl_service(mock_db)
        assert service2 is service1

    @pytest.mark.asyncio
    async def test_get_hitl_state_manager(self, orchestrator):
        """Test HITL state manager getter with caching"""
        mock_db = AsyncMock()

        # First call should create state manager
        manager1 = await orchestrator._get_hitl_state_manager(mock_db)
        assert manager1 is not None
        assert orchestrator._hitl_state_manager is manager1

        # Second call should return cached manager
        manager2 = await orchestrator._get_hitl_state_manager(mock_db)
        assert manager2 is manager1

    @pytest.mark.asyncio
    async def test_notify_feedback_required(self, orchestrator, mock_session, test_result):
        """Test feedback required notification"""
        with patch('app.services.pipeline_service.realtime_hub.publish') as mock_publish:
            with patch('app.services.pipeline_service.session_scope') as mock_scope:
                with patch.object(orchestrator, '_get_hitl_state_manager') as mock_get_manager:
                    with patch.object(orchestrator, '_get_feedback_options_for_phase') as mock_get_options:
                        mock_db = AsyncMock()
                        mock_scope.return_value.__aenter__.return_value = mock_db

                        mock_manager = Mock()
                        mock_manager.get_session_status = AsyncMock(return_value={"state": "waiting"})
                        mock_get_manager.return_value = mock_manager
                        mock_get_options.return_value = [{"option_id": "test"}]

                        await orchestrator._notify_feedback_required(mock_session, 1, test_result)

                        mock_publish.assert_called_once()
                        call_args = mock_publish.call_args[0]
                        assert call_args[0] == mock_session.request_id

    @pytest.mark.asyncio
    async def test_notify_feedback_timeout(self, orchestrator, mock_session):
        """Test feedback timeout notification"""
        with patch('app.services.pipeline_service.realtime_hub.publish') as mock_publish:
            with patch('app.services.pipeline_service.session_scope') as mock_scope:
                with patch.object(orchestrator, '_get_hitl_state_manager') as mock_get_manager:
                    mock_db = AsyncMock()
                    mock_scope.return_value.__aenter__.return_value = mock_db

                    mock_manager = Mock()
                    mock_manager.get_session_status = AsyncMock(return_value={"state": "timeout"})
                    mock_get_manager.return_value = mock_manager

                    await orchestrator._notify_feedback_timeout(mock_session, 1)

                    mock_publish.assert_called_once()
                    call_args = mock_publish.call_args[0]
                    assert call_args[0] == mock_session.request_id

    @pytest.mark.asyncio
    async def test_notify_feedback_approved(self, orchestrator, mock_session):
        """Test feedback approved notification"""
        with patch('app.services.pipeline_service.realtime_hub.publish') as mock_publish:
            with patch('app.services.pipeline_service.session_scope') as mock_scope:
                with patch.object(orchestrator, '_get_hitl_state_manager') as mock_get_manager:
                    mock_db = AsyncMock()
                    mock_scope.return_value.__aenter__.return_value = mock_db

                    mock_manager = Mock()
                    mock_manager.get_session_status = AsyncMock(return_value={"state": "completed"})
                    mock_get_manager.return_value = mock_manager

                    await orchestrator._notify_feedback_approved(mock_session, 1)

                    mock_publish.assert_called_once()
                    call_args = mock_publish.call_args[0]
                    assert call_args[0] == mock_session.request_id

    @pytest.mark.asyncio
    async def test_extract_feedback_modifications_from_response(self, orchestrator):
        """Test feedback modification extraction"""
        feedback = {
            "feedback_type": "modification",
            "natural_language_input": "Make it brighter",
            "selected_options": ["brightness", "contrast"]
        }

        modifications = orchestrator._extract_feedback_modifications_from_response(feedback)

        assert modifications is not None
        assert modifications["natural_language_modifications"] == "Make it brighter"
        assert modifications["selected_modifications"] == ["brightness", "contrast"]

    @pytest.mark.asyncio
    async def test_extract_feedback_modifications_empty(self, orchestrator):
        """Test feedback modification extraction with empty feedback"""
        feedback = {"feedback_type": "approval"}

        modifications = orchestrator._extract_feedback_modifications_from_response(feedback)

        assert modifications is None
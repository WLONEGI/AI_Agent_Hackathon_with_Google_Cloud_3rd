import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.hitl_service import (
    HITLStateManager,
    HITLSessionContext,
    HITLSessionState,
    HITLService,
    HITLSessionError,
    HITLStateError,
    HITLError
)


class TestHITLStateManager:
    """Test suite for HITLStateManager"""

    @pytest.fixture
    def mock_hitl_service(self):
        """Mock HITLService for testing"""
        service = Mock(spec=HITLService)
        service.db = AsyncMock()  # Add db attribute that HITLStateManager expects
        service.create_feedback_waiting_state = AsyncMock()
        service.check_and_handle_timeouts = AsyncMock()
        return service

    @pytest.fixture
    def state_manager(self, mock_hitl_service):
        """Create HITLStateManager instance for testing"""
        return HITLStateManager(mock_hitl_service)

    @pytest.fixture
    def session_id(self):
        """Generate test session ID"""
        return uuid4()

    @pytest.mark.asyncio
    async def test_start_hitl_session_success(self, state_manager, session_id, mock_hitl_service):
        """Test successful HITL session start"""
        phase = 1
        preview_data = {"test": "data"}

        # Test session start
        context = await state_manager.start_hitl_session(
            session_id=session_id,
            phase=phase,
            preview_data=preview_data
        )

        # Verify context creation
        assert isinstance(context, HITLSessionContext)
        assert context.session_id == session_id
        assert context.current_phase == phase
        assert context.state == HITLSessionState.WAITING_FEEDBACK
        assert context.iteration_count == 0

        # Verify session is stored
        assert session_id in state_manager.active_sessions
        assert state_manager.active_sessions[session_id] == context

        # Verify service call
        mock_hitl_service.create_feedback_waiting_state.assert_called_once_with(
            session_id=session_id,
            phase=phase,
            preview_data=preview_data,
            timeout_minutes=30
        )

    @pytest.mark.asyncio
    async def test_start_hitl_session_database_error(self, state_manager, session_id, mock_hitl_service):
        """Test HITL session start with database error"""
        from app.services.hitl_service import HITLDatabaseError
        mock_hitl_service.create_feedback_waiting_state.side_effect = Exception("Database error")

        with pytest.raises(HITLDatabaseError) as exc_info:
            await state_manager.start_hitl_session(session_id, 1)

        assert "Database error" in str(exc_info.value)
        assert session_id in state_manager.active_sessions  # Context should still be stored for error recovery

    @pytest.mark.asyncio
    async def test_process_feedback_approval(self, state_manager, session_id):
        """Test feedback processing with approval"""
        # Setup active session
        context = HITLSessionContext(session_id, 1)
        context.update_state(HITLSessionState.WAITING_FEEDBACK)
        state_manager.active_sessions[session_id] = context

        feedback_data = {"feedback_type": "approval"}

        # Process feedback
        result = await state_manager.process_feedback_received(session_id, feedback_data)

        assert result is True
        assert context.state == HITLSessionState.COMPLETED
        assert context.feedback_data == feedback_data

    @pytest.mark.asyncio
    async def test_process_feedback_modification(self, state_manager, session_id):
        """Test feedback processing with modification request"""
        # Setup active session
        context = HITLSessionContext(session_id, 1)
        context.update_state(HITLSessionState.WAITING_FEEDBACK)
        state_manager.active_sessions[session_id] = context

        feedback_data = {"feedback_type": "modification", "natural_language_input": "Make it brighter"}

        # Process feedback
        result = await state_manager.process_feedback_received(session_id, feedback_data)

        assert result is True
        assert context.state == HITLSessionState.REGENERATING
        assert context.iteration_count == 1
        assert context.feedback_data == feedback_data

    @pytest.mark.asyncio
    async def test_process_feedback_max_iterations_exceeded(self, state_manager, session_id):
        """Test feedback processing when max iterations exceeded"""
        # Setup active session at max iterations
        context = HITLSessionContext(session_id, 1)
        context.update_state(HITLSessionState.WAITING_FEEDBACK)
        context.iteration_count = 3  # At max iterations
        state_manager.active_sessions[session_id] = context

        feedback_data = {"feedback_type": "modification"}

        # Process feedback should raise error
        with pytest.raises(HITLError) as exc_info:
            await state_manager.process_feedback_received(session_id, feedback_data)

        assert "Maximum iterations exceeded" in str(exc_info.value)
        assert context.state == HITLSessionState.ERROR

    @pytest.mark.asyncio
    async def test_process_feedback_invalid_type(self, state_manager, session_id):
        """Test feedback processing with invalid feedback type"""
        # Setup active session
        context = HITLSessionContext(session_id, 1)
        context.update_state(HITLSessionState.WAITING_FEEDBACK)
        state_manager.active_sessions[session_id] = context

        feedback_data = {"feedback_type": "invalid_type"}

        # Process feedback should raise error
        with pytest.raises(HITLError) as exc_info:
            await state_manager.process_feedback_received(session_id, feedback_data)

        assert "Invalid feedback type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_feedback_wrong_state(self, state_manager, session_id):
        """Test feedback processing when session is in wrong state"""
        # Setup active session in wrong state
        context = HITLSessionContext(session_id, 1)
        context.update_state(HITLSessionState.REGENERATING)  # Wrong state
        state_manager.active_sessions[session_id] = context

        feedback_data = {"feedback_type": "approval"}

        # Process feedback should raise state error
        with pytest.raises(HITLStateError) as exc_info:
            await state_manager.process_feedback_received(session_id, feedback_data)

        assert "Invalid state transition" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_feedback_no_session(self, state_manager, session_id):
        """Test feedback processing when no session exists"""
        feedback_data = {"feedback_type": "approval"}

        # Process feedback should raise session error
        with pytest.raises(HITLSessionError) as exc_info:
            await state_manager.process_feedback_received(session_id, feedback_data)

        assert "No active HITL session found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_regeneration_complete_success(self, state_manager, session_id, mock_hitl_service):
        """Test successful regeneration completion handling"""
        # Setup active session in regenerating state
        context = HITLSessionContext(session_id, 1)
        context.update_state(HITLSessionState.REGENERATING)
        state_manager.active_sessions[session_id] = context

        new_preview_data = {"updated": "data"}

        # Handle regeneration completion
        result = await state_manager.handle_regeneration_complete(
            session_id, regeneration_success=True, new_preview_data=new_preview_data
        )

        assert result is True
        assert context.state == HITLSessionState.WAITING_FEEDBACK

        # Verify service call
        mock_hitl_service.create_feedback_waiting_state.assert_called_once_with(
            session_id=session_id,
            phase=context.current_phase,
            preview_data=new_preview_data,
            timeout_minutes=30
        )

    @pytest.mark.asyncio
    async def test_handle_regeneration_complete_failure(self, state_manager, session_id):
        """Test regeneration completion handling with failure"""
        # Setup active session in regenerating state
        context = HITLSessionContext(session_id, 1)
        context.update_state(HITLSessionState.REGENERATING)
        state_manager.active_sessions[session_id] = context

        # Handle regeneration failure
        with pytest.raises(HITLError) as exc_info:
            await state_manager.handle_regeneration_complete(session_id, regeneration_success=False)

        assert "Regeneration failed" in str(exc_info.value)
        assert context.state == HITLSessionState.ERROR

    @pytest.mark.asyncio
    async def test_handle_timeout(self, state_manager, session_id, mock_hitl_service):
        """Test timeout handling"""
        # Setup active session
        context = HITLSessionContext(session_id, 1)
        context.update_state(HITLSessionState.WAITING_FEEDBACK)
        state_manager.active_sessions[session_id] = context

        # Handle timeout
        await state_manager.handle_timeout(session_id)

        assert context.state == HITLSessionState.TIMEOUT
        mock_hitl_service.check_and_handle_timeouts.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_timeout_no_session(self, state_manager, session_id, mock_hitl_service):
        """Test timeout handling when no session exists"""
        # Handle timeout for non-existent session (should not raise error)
        await state_manager.handle_timeout(session_id)

        # Should still call service cleanup
        mock_hitl_service.check_and_handle_timeouts.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_session(self, state_manager, session_id):
        """Test session cleanup"""
        # Setup active session
        context = HITLSessionContext(session_id, 1)
        state_manager.active_sessions[session_id] = context

        # Cleanup session
        await state_manager.cleanup_session(session_id)

        # Verify session removed
        assert session_id not in state_manager.active_sessions

    @pytest.mark.asyncio
    async def test_get_session_status(self, state_manager, session_id):
        """Test getting session status"""
        # Setup active session
        context = HITLSessionContext(session_id, 1)
        context.update_state(HITLSessionState.WAITING_FEEDBACK)
        context.iteration_count = 2
        state_manager.active_sessions[session_id] = context

        # Get status
        status = await state_manager.get_session_status(session_id)

        assert status is not None
        assert status["session_id"] == str(session_id)
        assert status["phase"] == 1
        assert status["state"] == "waiting_feedback"
        assert status["iteration_count"] == 2
        assert status["can_continue"] is True

    @pytest.mark.asyncio
    async def test_get_session_status_no_session(self, state_manager, session_id):
        """Test getting status for non-existent session"""
        status = await state_manager.get_session_status(session_id)
        assert status is None

    @pytest.mark.asyncio
    async def test_get_all_active_sessions(self, state_manager):
        """Test getting all active sessions"""
        # Setup multiple active sessions
        session_ids = [uuid4(), uuid4()]
        for i, session_id in enumerate(session_ids):
            context = HITLSessionContext(session_id, i + 1)
            state_manager.active_sessions[session_id] = context

        # Get all sessions
        all_sessions = await state_manager.get_all_active_sessions()

        assert len(all_sessions) == 2
        assert all(session["session_id"] in [str(sid) for sid in session_ids] for session in all_sessions)

    @pytest.mark.asyncio
    async def test_force_cleanup_stale_sessions(self, state_manager):
        """Test force cleanup of stale sessions"""
        # Setup stale session (older than 24 hours)
        stale_session_id = uuid4()
        stale_context = HITLSessionContext(stale_session_id, 1)
        # Manually set old timestamp
        stale_context.started_at = datetime(2023, 1, 1)  # Very old timestamp
        state_manager.active_sessions[stale_session_id] = stale_context

        # Setup fresh session
        fresh_session_id = uuid4()
        fresh_context = HITLSessionContext(fresh_session_id, 1)
        state_manager.active_sessions[fresh_session_id] = fresh_context

        # Force cleanup with 24 hour threshold
        cleanup_count = await state_manager.force_cleanup_stale_sessions(max_age_hours=24)

        assert cleanup_count == 1
        assert stale_session_id not in state_manager.active_sessions
        assert fresh_session_id in state_manager.active_sessions


class TestHITLSessionContext:
    """Test suite for HITLSessionContext"""

    def test_context_initialization(self):
        """Test context initialization"""
        session_id = uuid4()
        phase = 2

        context = HITLSessionContext(session_id, phase)

        assert context.session_id == session_id
        assert context.current_phase == phase
        assert context.state == HITLSessionState.IDLE
        assert context.iteration_count == 0
        assert context.max_iterations == 3
        assert context.feedback_data is None
        assert context.error_message is None
        assert isinstance(context.started_at, datetime)
        assert isinstance(context.last_state_change, datetime)

    def test_update_state(self):
        """Test state update functionality"""
        context = HITLSessionContext(uuid4(), 1)
        original_time = context.last_state_change

        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.001)

        error_message = "Test error"
        context.update_state(HITLSessionState.ERROR, error_message)

        assert context.state == HITLSessionState.ERROR
        assert context.error_message == error_message
        assert context.last_state_change > original_time

    def test_increment_iteration(self):
        """Test iteration increment and limit checking"""
        context = HITLSessionContext(uuid4(), 1)

        # Test successful increments
        assert context.increment_iteration() is True
        assert context.iteration_count == 1

        assert context.increment_iteration() is True
        assert context.iteration_count == 2

        assert context.increment_iteration() is True
        assert context.iteration_count == 3

        # Test limit exceeded
        assert context.increment_iteration() is False
        assert context.iteration_count == 4

    def test_can_continue(self):
        """Test continuation check logic"""
        context = HITLSessionContext(uuid4(), 1)

        # Normal state, can continue
        context.update_state(HITLSessionState.WAITING_FEEDBACK)
        assert context.can_continue() is True

        # Error state, cannot continue
        context.update_state(HITLSessionState.ERROR)
        assert context.can_continue() is False

        # Timeout state, cannot continue
        context.update_state(HITLSessionState.TIMEOUT)
        assert context.can_continue() is False

        # Max iterations exceeded, cannot continue
        context.update_state(HITLSessionState.WAITING_FEEDBACK)
        context.iteration_count = 5  # Over max
        assert context.can_continue() is False
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from uuid import uuid4

# Configure pytest for async testing
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_async_session():
    """Mock SQLAlchemy async session for database operations"""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.scalar_one = AsyncMock()
    session.scalar_one_or_none = AsyncMock()
    session.scalars = AsyncMock()
    session.add = Mock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def sample_session_id():
    """Generate a sample session ID for testing"""
    return uuid4()


@pytest.fixture
def sample_manga_session(sample_session_id):
    """Create a sample manga session for testing"""
    from app.db.models import MangaSession

    session = Mock(spec=MangaSession)
    session.id = uuid4()
    session.request_id = sample_session_id
    session.user_id = uuid4()
    session.status = "processing"
    session.waiting_for_feedback = False
    session.feedback_timeout_at = None
    session.total_feedback_count = 0
    return session


@pytest.fixture
def sample_feedback_data():
    """Create sample feedback data for testing"""
    return {
        "feedback_type": "modification",
        "natural_language_input": "Make the characters more vibrant and colorful",
        "selected_options": ["brightness", "saturation"],
        "user_satisfaction_score": 0.7,
        "processing_time_ms": 1500
    }


@pytest.fixture
def sample_phase_result():
    """Create sample phase result for testing"""
    return {
        "generated_images": [
            "gs://bucket/image1.jpg",
            "gs://bucket/image2.jpg"
        ],
        "generated_text": "A mystical forest where dragons and humans coexist peacefully",
        "characters": [
            {
                "name": "Akira",
                "description": "A young dragon trainer with magical abilities",
                "appearance": "Short black hair, emerald eyes"
            },
            {
                "name": "Zephyr",
                "description": "A wise ancient dragon with silver scales",
                "type": "Wind Dragon"
            }
        ],
        "story_outline": {
            "setting": "Magical forest kingdom",
            "conflict": "Ancient curse threatens the harmony",
            "resolution": "Unity between species saves the day"
        },
        "metadata": {
            "quality_score": 0.82,
            "generation_time": 2.3,
            "model_version": "gemini-2.5",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }


@pytest.fixture
def mock_settings():
    """Mock application settings for HITL testing"""
    settings = Mock()
    settings.hitl_enabled = True
    settings.hitl_feedback_timeout_minutes = 30
    settings.hitl_max_iterations = 3
    settings.hitl_max_retry_attempts = 3
    settings.hitl_default_quality_threshold = 0.72
    settings.hitl_enabled_phases = "1,2"
    settings.hitl_auto_approve_threshold = 0.9
    settings.hitl_require_manual_approval = False
    settings.hitl_development_mode = True
    settings.hitl_skip_on_error = True

    settings.get_hitl_enabled_phases.return_value = [1, 2]
    settings.is_hitl_enabled_for_phase.side_effect = lambda phase: phase in [1, 2]

    return settings


@pytest.fixture
def mock_realtime_hub():
    """Mock realtime hub for WebSocket communication testing"""
    hub = Mock()
    hub.publish = AsyncMock()
    hub.subscribe = AsyncMock()
    hub.unsubscribe = AsyncMock()
    return hub


@pytest.fixture
def mock_build_event():
    """Mock event builder for WebSocket events"""
    def build_event(event_type, **kwargs):
        return {
            "type": event_type,
            "timestamp": "2024-01-15T10:30:00Z",
            **kwargs
        }
    return build_event


# Test data generators
@pytest.fixture
def feedback_scenarios():
    """Generate various feedback scenarios for testing"""
    return [
        {
            "name": "approval",
            "feedback": {"feedback_type": "approval"},
            "expected_iterations": 0,
            "expected_final_state": "completed"
        },
        {
            "name": "single_modification",
            "feedback": [
                {"feedback_type": "modification", "natural_language_input": "Make it brighter"},
                {"feedback_type": "approval"}
            ],
            "expected_iterations": 1,
            "expected_final_state": "completed"
        },
        {
            "name": "multiple_modifications",
            "feedback": [
                {"feedback_type": "modification", "natural_language_input": "Add more colors"},
                {"feedback_type": "modification", "natural_language_input": "Increase contrast"},
                {"feedback_type": "approval"}
            ],
            "expected_iterations": 2,
            "expected_final_state": "completed"
        },
        {
            "name": "skip",
            "feedback": {"feedback_type": "skip"},
            "expected_iterations": 0,
            "expected_final_state": "completed"
        },
        {
            "name": "timeout",
            "feedback": None,  # Represents timeout
            "expected_iterations": 0,
            "expected_final_state": "timeout"
        }
    ]


@pytest.fixture
def error_scenarios():
    """Generate various error scenarios for testing"""
    return [
        {
            "name": "database_error",
            "error_type": "HITLDatabaseError",
            "error_message": "Database connection failed",
            "expected_error_type": "database_error"
        },
        {
            "name": "session_error",
            "error_type": "HITLSessionError",
            "error_message": "No active session found",
            "expected_error_type": "session_error"
        },
        {
            "name": "state_error",
            "error_type": "HITLStateError",
            "error_message": "Invalid state transition",
            "expected_error_type": "state_error"
        },
        {
            "name": "timeout_error",
            "error_type": "HITLTimeoutError",
            "error_message": "Feedback timeout exceeded",
            "expected_error_type": "timeout_error"
        }
    ]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers",
        "hitl: mark test as HITL functionality test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )


# Helper functions for tests
def assert_hitl_metadata(result, expected_state=None, expected_iterations=None):
    """Helper function to assert HITL metadata in results"""
    assert "metadata" in result
    metadata = result["metadata"]

    assert metadata.get("hitl_processed") is True

    if expected_state:
        assert metadata.get("final_state") == expected_state

    if expected_iterations is not None:
        assert metadata.get("feedback_iterations") == expected_iterations


def assert_error_metadata(result, expected_error_type=None):
    """Helper function to assert HITL error metadata in results"""
    assert "metadata" in result
    metadata = result["metadata"]

    assert metadata.get("hitl_processed") is True
    assert metadata.get("hitl_error") is True

    if expected_error_type:
        assert metadata.get("hitl_error_type") == expected_error_type

    assert "hitl_error_message" in metadata
    assert "hitl_error_timestamp" in metadata
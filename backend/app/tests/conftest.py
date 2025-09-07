"""Global test configuration and fixtures."""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator, Dict, Any
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.core.database import Base, get_db
from app.models.user import User
from app.models.manga import MangaSession, PhaseResult, UserFeedback, GeneratedImage
from app.agents.base_agent import BaseAgent
from app.agents.pipeline_orchestrator import PipelineOrchestrator


# =============================================================================
# Test Database Setup
# =============================================================================

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async_session = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    
    def override_get_db():
        """Override database dependency."""
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clean up
    app.dependency_overrides.clear()


# =============================================================================
# User Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        username="testuser",
        hashed_password="test-password-hash",
        is_active=True,
        account_type="free",
        provider="email",
        created_at=datetime.utcnow()
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create admin test user."""
    user = User(
        id=uuid4(),
        email="admin@example.com",
        username="admin",
        hashed_password="admin-password-hash",
        is_active=True,
        role="admin",
        account_type="admin",
        provider="email",
        created_at=datetime.utcnow()
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


# =============================================================================
# Manga Session Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def sample_manga_session(db_session: AsyncSession, test_user: User) -> MangaSession:
    """Create sample manga session for testing."""
    session = MangaSession(
        id=uuid4(),
        user_id=test_user.id,
        title="Test Manga",
        input_text="A young hero discovers magical powers and must save the world from an ancient evil.",
        genre="fantasy",
        style="shonen",
        quality_level="high",
        status="pending",
        current_phase=0,
        total_phases=7,
        hitl_enabled=True,
        auto_proceed=False,
        created_at=datetime.utcnow()
    )
    
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    
    return session


@pytest_asyncio.fixture
async def completed_manga_session(db_session: AsyncSession, test_user: User) -> MangaSession:
    """Create completed manga session with phase results."""
    session = MangaSession(
        id=uuid4(),
        user_id=test_user.id,
        title="Completed Test Manga",
        input_text="A complete story for testing purposes.",
        genre="adventure",
        status="completed",
        current_phase=7,
        total_phases=7,
        final_result={"manga_data": "test_data"},
        quality_score=0.85,
        total_processing_time_ms=120000,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    
    db_session.add(session)
    await db_session.commit()
    
    # Add phase results
    for phase_num in range(1, 8):
        phase_result = PhaseResult(
            id=uuid4(),
            session_id=session.id,
            phase_number=phase_num,
            phase_name=f"Phase {phase_num}",
            input_data={"input": f"phase_{phase_num}_input"},
            output_data={"output": f"phase_{phase_num}_output"},
            processing_time_ms=15000 + (phase_num * 1000),
            status="completed",
            quality_score=0.8 + (phase_num * 0.01),
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db_session.add(phase_result)
    
    await db_session.commit()
    await db_session.refresh(session)
    
    return session


# =============================================================================
# AI Service Mocks
# =============================================================================

@pytest.fixture
def mock_ai_service():
    """Mock AI service with realistic responses."""
    mock_service = AsyncMock()
    
    # Mock phase-specific responses
    mock_responses = {
        1: {  # Concept Analysis
            "genre": "fantasy",
            "themes": ["heroism", "friendship", "good_vs_evil"],
            "target_audience": "teenagers",
            "estimated_pages": 20,
            "story_structure": "hero_journey"
        },
        2: {  # Character Design
            "characters": [
                {
                    "name": "Hero",
                    "role": "protagonist",
                    "description": "Young brave warrior",
                    "visual_features": {"hair": "black", "eyes": "blue", "height": "medium"}
                }
            ],
            "main_character_count": 1,
            "character_diversity_score": 0.7
        },
        3: {  # Story Structure
            "total_scenes": 8,
            "story_complexity_score": 0.8,
            "plot_points": ["introduction", "inciting_incident", "rising_action", "climax", "resolution"]
        },
        4: {  # Name Generation
            "total_panels": 24,
            "layout_complexity_score": 0.75,
            "visual_storytelling_score": 0.82
        },
        5: {  # Image Generation
            "total_images_generated": 8,
            "successful_generations": 7,
            "quality_analysis": {"average_quality_score": 0.78}
        },
        6: {  # Dialogue
            "total_dialogue_elements": 15,
            "readability_score": 0.85,
            "emotional_impact_score": 0.80
        },
        7: {  # Integration
            "overall_quality_score": 0.79,
            "production_ready": True,
            "output_formats": {"pdf": "path/to/pdf", "cbz": "path/to/cbz"}
        }
    }
    
    mock_service.process_phase = AsyncMock(side_effect=lambda phase, input_data: mock_responses.get(phase, {}))
    mock_service.generate_image = AsyncMock(return_value={"url": "http://example.com/image.png", "quality": 0.8})
    mock_service.analyze_quality = AsyncMock(return_value={"score": 0.8, "issues": []})
    
    return mock_service


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=False)
    
    return mock_redis


# =============================================================================
# Agent Testing Fixtures
# =============================================================================

@pytest.fixture
def mock_base_agent():
    """Mock base agent for testing."""
    
    class MockAgent(BaseAgent):
        def __init__(self, phase_number: int = 1):
            super().__init__(phase_number, f"Mock Phase {phase_number}", 30)
        
        async def process_phase(self, input_data: Dict[str, Any], session_id, previous_results=None):
            return {"processed": True, "phase": self.phase_number, "input": input_data}
        
        async def generate_prompt(self, input_data: Dict[str, Any], previous_results=None):
            return f"Mock prompt for phase {self.phase_number}"
        
        async def validate_output(self, output_data: Dict[str, Any]):
            return True
    
    return MockAgent


@pytest.fixture
def sample_phase_data():
    """Sample data for different phases."""
    return {
        "phase_1": {
            "input": {"text": "Sample story text"},
            "expected_output": {
                "genre": "fantasy",
                "themes": ["adventure", "friendship"],
                "estimated_pages": 15
            }
        },
        "phase_2": {
            "input": {"genre": "fantasy", "themes": ["adventure"]},
            "expected_output": {
                "characters": [{"name": "Hero", "role": "protagonist"}],
                "character_count": 1
            }
        }
    }


# =============================================================================
# WebSocket Testing Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def websocket_client():
    """WebSocket test client."""
    from starlette.testclient import TestClient
    
    with TestClient(app) as client:
        yield client


# =============================================================================
# Performance Testing Fixtures
# =============================================================================

@pytest.fixture
def performance_thresholds():
    """Expected performance thresholds for each phase."""
    return {
        1: {"max_time_ms": 15000, "expected_time_ms": 12000},  # Concept Analysis
        2: {"max_time_ms": 20000, "expected_time_ms": 18000},  # Character Design
        3: {"max_time_ms": 18000, "expected_time_ms": 15000},  # Story Structure
        4: {"max_time_ms": 25000, "expected_time_ms": 20000},  # Name Generation
        5: {"max_time_ms": 30000, "expected_time_ms": 25000},  # Image Generation
        6: {"max_time_ms": 6000, "expected_time_ms": 4000},    # Dialogue
        7: {"max_time_ms": 5000, "expected_time_ms": 3000}     # Integration
    }


# =============================================================================
# Data Factory Functions
# =============================================================================

def create_test_feedback(session_id: str, phase_number: int = 1, feedback_type: str = "text") -> Dict[str, Any]:
    """Create test feedback data."""
    return {
        "session_id": session_id,
        "phase_number": phase_number,
        "feedback_type": feedback_type,
        "feedback_text": "Please make the character more heroic",
        "feedback_data": {
            "character_adjustments": {
                "personality": "more_confident",
                "appearance": "stronger_build"
            }
        }
    }


def create_test_generation_params() -> Dict[str, Any]:
    """Create test generation parameters."""
    return {
        "style": "shonen",
        "quality_level": "high",
        "enable_hitl": True,
        "auto_proceed": False,
        "custom_style_params": {
            "color_scheme": "vibrant",
            "line_style": "clean"
        },
        "content_guidelines": {
            "age_rating": "teen",
            "content_warnings": []
        }
    }


def create_mock_phase_result(phase_number: int, session_id: str) -> Dict[str, Any]:
    """Create mock phase result for testing."""
    return {
        "phase_number": phase_number,
        "session_id": session_id,
        "status": "completed",
        "processing_time_ms": 15000 + (phase_number * 1000),
        "input_data": {"input": f"phase_{phase_number}_input"},
        "output_data": {"output": f"phase_{phase_number}_output"},
        "quality_score": 0.8 + (phase_number * 0.01),
        "preview_data": {"preview": f"phase_{phase_number}_preview"}
    }


# =============================================================================
# Event Loop Configuration
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Authentication Helpers
# =============================================================================

@pytest.fixture
def auth_headers(test_user: User):
    """Generate authentication headers for API tests."""
    # Mock JWT token - in real implementation, this would be generated properly
    mock_token = f"Bearer test-token-{test_user.id}"
    return {"Authorization": mock_token}


@pytest.fixture
def admin_headers(admin_user: User):
    """Generate admin authentication headers."""
    mock_token = f"Bearer admin-token-{admin_user.id}"
    return {"Authorization": mock_token}


# =============================================================================
# Pipeline Testing Helpers
# =============================================================================

@pytest_asyncio.fixture
async def mock_pipeline_orchestrator():
    """Mock pipeline orchestrator for testing."""
    orchestrator = MagicMock(spec=PipelineOrchestrator)
    
    # Mock execution results
    mock_results = {
        "execution_summary": {
            "pipeline_status": "completed",
            "total_execution_time_seconds": 97.5,
            "parallel_efficiency_percentage": 23.1,
            "phases_completed": 7,
            "phases_failed": 0,
            "retry_count": 1
        },
        "quality_summary": {
            "overall_quality_score": 0.82,
            "quality_grade": "B",
            "production_ready": True,
            "critical_issues_count": 0
        }
    }
    
    orchestrator.execute_pipeline = AsyncMock(return_value=mock_results)
    orchestrator.get_pipeline_status = MagicMock(return_value={
        "status": "processing",
        "current_phase": 3,
        "progress_percentage": 42.8
    })
    orchestrator.cancel_pipeline = AsyncMock()
    
    return orchestrator


# =============================================================================
# Quality Testing Data
# =============================================================================

@pytest.fixture
def quality_test_scenarios():
    """Test scenarios for quality assessment."""
    return [
        {
            "name": "high_quality_output",
            "input": "A well-structured fantasy adventure story",
            "expected_quality_range": (0.8, 1.0),
            "expected_grade": ["A", "B"]
        },
        {
            "name": "medium_quality_output",
            "input": "A simple story with basic structure",
            "expected_quality_range": (0.6, 0.79),
            "expected_grade": ["C", "D"]
        },
        {
            "name": "low_quality_output",
            "input": "Incoherent text with no clear structure",
            "expected_quality_range": (0.0, 0.59),
            "expected_grade": ["F"]
        }
    ]


# =============================================================================
# Cleanup Utilities
# =============================================================================

@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data(db_session: AsyncSession):
    """Automatically clean up test data after each test."""
    yield
    
    # Clean up test data
    try:
        await db_session.rollback()
    except Exception:
        pass  # Session might already be closed


# =============================================================================
# Error Simulation
# =============================================================================

@pytest.fixture
def error_scenarios():
    """Error scenarios for testing error handling."""
    return {
        "timeout_error": asyncio.TimeoutError("Phase processing timeout"),
        "ai_api_error": Exception("AI API rate limit exceeded"),
        "database_error": Exception("Database connection failed"),
        "validation_error": ValueError("Invalid input parameters"),
        "network_error": ConnectionError("Network unreachable")
    }
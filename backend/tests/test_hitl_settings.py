import pytest
from pydantic import ValidationError

from app.core.settings import Settings


class TestHITLSettings:
    """Test suite for HITL configuration settings"""

    def test_hitl_default_settings(self):
        """Test HITL default configuration values"""
        # Create settings with minimal required fields
        minimal_config = {
            "database_url": "postgresql://test",
            "cloud_tasks_queue": "test-queue",
            "cloud_tasks_project": "test-project",
            "cloud_tasks_location": "test-location",
            "cloud_tasks_service_url": "https://test.com",
            "gcs_bucket_preview": "test-bucket",
            "firebase_project_id": "test-project",
            "firebase_client_email": "test@test.com",
            "firebase_private_key": "test-key",
            "vertex_credentials_json": '{"test": "data"}'
        }

        settings = Settings(**minimal_config)

        # Verify HITL defaults
        assert settings.hitl_enabled is True
        assert settings.hitl_feedback_timeout_minutes == 30
        assert settings.hitl_max_retry_attempts == 3
        assert settings.hitl_default_quality_threshold == 0.72
        assert settings.hitl_enabled_phases == "1,2"
        assert settings.hitl_max_iterations == 3
        assert settings.hitl_auto_approve_threshold == 0.9
        assert settings.hitl_require_manual_approval is False
        assert settings.hitl_development_mode is True
        assert settings.hitl_skip_on_error is True

    def test_hitl_custom_settings(self):
        """Test HITL custom configuration values"""
        config = {
            "database_url": "postgresql://test",
            "cloud_tasks_queue": "test-queue",
            "cloud_tasks_project": "test-project",
            "cloud_tasks_location": "test-location",
            "cloud_tasks_service_url": "https://test.com",
            "gcs_bucket_preview": "test-bucket",
            "firebase_project_id": "test-project",
            "firebase_client_email": "test@test.com",
            "firebase_private_key": "test-key",
            "vertex_credentials_json": '{"test": "data"}',
            # Custom HITL settings
            "hitl_enabled": False,
            "hitl_feedback_timeout_minutes": 60,
            "hitl_max_retry_attempts": 5,
            "hitl_default_quality_threshold": 0.8,
            "hitl_enabled_phases": "1,2,3,4",
            "hitl_max_iterations": 5,
            "hitl_auto_approve_threshold": 0.95,
            "hitl_require_manual_approval": True,
            "hitl_development_mode": False,
            "hitl_skip_on_error": False
        }

        settings = Settings(**config)

        # Verify custom values
        assert settings.hitl_enabled is False
        assert settings.hitl_feedback_timeout_minutes == 60
        assert settings.hitl_max_retry_attempts == 5
        assert settings.hitl_default_quality_threshold == 0.8
        assert settings.hitl_enabled_phases == "1,2,3,4"
        assert settings.hitl_max_iterations == 5
        assert settings.hitl_auto_approve_threshold == 0.95
        assert settings.hitl_require_manual_approval is True
        assert settings.hitl_development_mode is False
        assert settings.hitl_skip_on_error is False

    def test_hitl_enabled_phases_validation_valid(self):
        """Test valid HITL enabled phases configuration"""
        config = {
            "database_url": "postgresql://test",
            "cloud_tasks_queue": "test-queue",
            "cloud_tasks_project": "test-project",
            "cloud_tasks_location": "test-location",
            "cloud_tasks_service_url": "https://test.com",
            "gcs_bucket_preview": "test-bucket",
            "firebase_project_id": "test-project",
            "firebase_client_email": "test@test.com",
            "firebase_private_key": "test-key",
            "vertex_credentials_json": '{"test": "data"}'
        }

        # Test various valid configurations
        valid_phases = ["1", "1,2", "1,2,3", "1,2,3,4,5,6,7", "2,4,6", "7"]

        for phases in valid_phases:
            config["hitl_enabled_phases"] = phases
            settings = Settings(**config)
            assert settings.hitl_enabled_phases == phases

    def test_hitl_enabled_phases_validation_invalid(self):
        """Test invalid HITL enabled phases configuration"""
        config = {
            "database_url": "postgresql://test",
            "cloud_tasks_queue": "test-queue",
            "cloud_tasks_project": "test-project",
            "cloud_tasks_location": "test-location",
            "cloud_tasks_service_url": "https://test.com",
            "gcs_bucket_preview": "test-bucket",
            "firebase_project_id": "test-project",
            "firebase_client_email": "test@test.com",
            "firebase_private_key": "test-key",
            "vertex_credentials_json": '{"test": "data"}'
        }

        # Test invalid configurations
        invalid_phases = ["0", "8", "1,8", "0,1", "-1", "1,2,8", "abc", "1,abc"]

        for phases in invalid_phases:
            config["hitl_enabled_phases"] = phases
            with pytest.raises(ValidationError) as exc_info:
                Settings(**config)
            assert "Invalid hitl_enabled_phases format" in str(exc_info.value)

    def test_hitl_enabled_phases_empty(self):
        """Test empty HITL enabled phases configuration"""
        config = {
            "database_url": "postgresql://test",
            "cloud_tasks_queue": "test-queue",
            "cloud_tasks_project": "test-project",
            "cloud_tasks_location": "test-location",
            "cloud_tasks_service_url": "https://test.com",
            "gcs_bucket_preview": "test-bucket",
            "firebase_project_id": "test-project",
            "firebase_client_email": "test@test.com",
            "firebase_private_key": "test-key",
            "vertex_credentials_json": '{"test": "data"}',
            "hitl_enabled_phases": ""
        }

        settings = Settings(**config)
        assert settings.hitl_enabled_phases == ""

    def test_get_hitl_enabled_phases(self):
        """Test getting HITL enabled phases as list"""
        config = {
            "database_url": "postgresql://test",
            "cloud_tasks_queue": "test-queue",
            "cloud_tasks_project": "test-project",
            "cloud_tasks_location": "test-location",
            "cloud_tasks_service_url": "https://test.com",
            "gcs_bucket_preview": "test-bucket",
            "firebase_project_id": "test-project",
            "firebase_client_email": "test@test.com",
            "firebase_private_key": "test-key",
            "vertex_credentials_json": '{"test": "data"}'
        }

        # Test default
        settings = Settings(**config)
        phases = settings.get_hitl_enabled_phases()
        assert phases == [1, 2]

        # Test custom phases
        config["hitl_enabled_phases"] = "1,3,5"
        settings = Settings(**config)
        phases = settings.get_hitl_enabled_phases()
        assert phases == [1, 3, 5]

        # Test empty phases
        config["hitl_enabled_phases"] = ""
        settings = Settings(**config)
        phases = settings.get_hitl_enabled_phases()
        assert phases == []

        # Test HITL disabled
        config["hitl_enabled"] = False
        config["hitl_enabled_phases"] = "1,2,3"
        settings = Settings(**config)
        phases = settings.get_hitl_enabled_phases()
        assert phases == []

    def test_is_hitl_enabled_for_phase(self):
        """Test checking if HITL is enabled for specific phase"""
        config = {
            "database_url": "postgresql://test",
            "cloud_tasks_queue": "test-queue",
            "cloud_tasks_project": "test-project",
            "cloud_tasks_location": "test-location",
            "cloud_tasks_service_url": "https://test.com",
            "gcs_bucket_preview": "test-bucket",
            "firebase_project_id": "test-project",
            "firebase_client_email": "test@test.com",
            "firebase_private_key": "test-key",
            "vertex_credentials_json": '{"test": "data"}',
            "hitl_enabled_phases": "1,3,5"
        }

        settings = Settings(**config)

        # Test enabled phases
        assert settings.is_hitl_enabled_for_phase(1) is True
        assert settings.is_hitl_enabled_for_phase(3) is True
        assert settings.is_hitl_enabled_for_phase(5) is True

        # Test disabled phases
        assert settings.is_hitl_enabled_for_phase(2) is False
        assert settings.is_hitl_enabled_for_phase(4) is False
        assert settings.is_hitl_enabled_for_phase(6) is False
        assert settings.is_hitl_enabled_for_phase(7) is False

        # Test with HITL globally disabled
        config["hitl_enabled"] = False
        settings = Settings(**config)
        assert settings.is_hitl_enabled_for_phase(1) is False
        assert settings.is_hitl_enabled_for_phase(3) is False

    def test_hitl_timeout_minutes_validation(self):
        """Test HITL timeout minutes validation"""
        config = {
            "database_url": "postgresql://test",
            "cloud_tasks_queue": "test-queue",
            "cloud_tasks_project": "test-project",
            "cloud_tasks_location": "test-location",
            "cloud_tasks_service_url": "https://test.com",
            "gcs_bucket_preview": "test-bucket",
            "firebase_project_id": "test-project",
            "firebase_client_email": "test@test.com",
            "firebase_private_key": "test-key",
            "vertex_credentials_json": '{"test": "data"}'
        }

        # Test valid values
        for timeout in [1, 30, 60, 120]:
            config["hitl_feedback_timeout_minutes"] = timeout
            settings = Settings(**config)
            assert settings.hitl_feedback_timeout_minutes == timeout

        # Test invalid values (should raise validation error)
        for timeout in [0, -1, 121, 200]:
            config["hitl_feedback_timeout_minutes"] = timeout
            with pytest.raises(ValidationError):
                Settings(**config)

    def test_hitl_quality_threshold_validation(self):
        """Test HITL quality threshold validation"""
        config = {
            "database_url": "postgresql://test",
            "cloud_tasks_queue": "test-queue",
            "cloud_tasks_project": "test-project",
            "cloud_tasks_location": "test-location",
            "cloud_tasks_service_url": "https://test.com",
            "gcs_bucket_preview": "test-bucket",
            "firebase_project_id": "test-project",
            "firebase_client_email": "test@test.com",
            "firebase_private_key": "test-key",
            "vertex_credentials_json": '{"test": "data"}'
        }

        # Test valid values
        for threshold in [0.0, 0.5, 0.72, 1.0]:
            config["hitl_default_quality_threshold"] = threshold
            settings = Settings(**config)
            assert settings.hitl_default_quality_threshold == threshold

        # Test invalid values (should raise validation error)
        for threshold in [-0.1, 1.1, 2.0]:
            config["hitl_default_quality_threshold"] = threshold
            with pytest.raises(ValidationError):
                Settings(**config)

    def test_hitl_max_iterations_validation(self):
        """Test HITL max iterations validation"""
        config = {
            "database_url": "postgresql://test",
            "cloud_tasks_queue": "test-queue",
            "cloud_tasks_project": "test-project",
            "cloud_tasks_location": "test-location",
            "cloud_tasks_service_url": "https://test.com",
            "gcs_bucket_preview": "test-bucket",
            "firebase_project_id": "test-project",
            "firebase_client_email": "test@test.com",
            "firebase_private_key": "test-key",
            "vertex_credentials_json": '{"test": "data"}'
        }

        # Test valid values
        for iterations in [1, 3, 5, 10]:
            config["hitl_max_iterations"] = iterations
            settings = Settings(**config)
            assert settings.hitl_max_iterations == iterations

        # Test invalid values (should raise validation error)
        for iterations in [0, -1, 11, 20]:
            config["hitl_max_iterations"] = iterations
            with pytest.raises(ValidationError):
                Settings(**config)
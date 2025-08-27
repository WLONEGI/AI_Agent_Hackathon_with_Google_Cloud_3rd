"""Unit tests for BaseAgent class."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any

from app.agents.base_agent import BaseAgent
from app.models.manga import MangaSession, PhaseResult
from app.core.logging import LoggerMixin


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent."""
    
    def __init__(self, fail_validation: bool = False, fail_processing: bool = False):
        super().__init__(1, "Test Agent", 30)
        self._fail_validation = fail_validation
        self._fail_processing = fail_processing
    
    async def process_phase(self, input_data: Dict[str, Any], session_id, previous_results=None):
        """Mock phase processing."""
        if self._fail_processing:
            raise ValueError("Processing failed for testing")
        
        await asyncio.sleep(0.1)  # Simulate processing time
        return {
            "processed": True,
            "input_data": input_data,
            "previous_results": previous_results,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
    
    async def generate_prompt(self, input_data: Dict[str, Any], previous_results=None):
        """Mock prompt generation."""
        return f"Test prompt for input: {input_data}"
    
    async def validate_output(self, output_data: Dict[str, Any]):
        """Mock output validation."""
        if self._fail_validation:
            return False
        return "processed" in output_data


@pytest.mark.asyncio
class TestBaseAgent:
    """Test cases for BaseAgent functionality."""
    
    async def test_agent_initialization(self):
        """Test agent initialization."""
        agent = TestAgent()
        
        assert agent.phase_number == 1
        assert agent.phase_name == "Test Agent"
        assert agent.timeout_seconds == 30
        assert isinstance(agent.metrics, dict)
        assert "total_processed" in agent.metrics
        assert "total_failures" in agent.metrics
        assert "average_processing_time" in agent.metrics
    
    async def test_successful_processing(self, sample_manga_session, db_session):
        """Test successful phase processing."""
        agent = TestAgent()
        input_data = {"test": "data", "story": "A hero's journey"}
        
        with patch.object(agent, '_cache_result') as mock_cache, \
             patch.object(agent, '_update_metrics') as mock_metrics:
            
            result = await agent.process(
                session=sample_manga_session,
                input_data=input_data,
                db=db_session,
                previous_results=None
            )
            
            assert isinstance(result, PhaseResult)
            assert result.phase_number == 1
            assert result.phase_name == "Test Agent"
            assert result.status == "completed"
            assert result.input_data == input_data
            assert result.output_data["processed"] is True
            assert result.processing_time_ms > 0
            
            # Verify caching and metrics were called
            mock_cache.assert_called_once()
            mock_metrics.assert_called_once()
    
    async def test_processing_timeout(self, sample_manga_session, db_session):
        """Test processing timeout handling."""
        agent = TestAgent()
        agent.timeout_seconds = 0.1  # Very short timeout
        
        # Mock a slow processing function
        original_process = agent.process_phase
        agent.process_phase = AsyncMock(side_effect=lambda *args: asyncio.sleep(1))
        
        with pytest.raises(Exception) as exc_info:
            await agent.process(
                session=sample_manga_session,
                input_data={"test": "data"},
                db=db_session
            )
        
        assert "timeout" in str(exc_info.value).lower()
    
    async def test_validation_failure(self, sample_manga_session, db_session):
        """Test output validation failure."""
        agent = TestAgent(fail_validation=True)
        
        with pytest.raises(Exception) as exc_info:
            await agent.process(
                session=sample_manga_session,
                input_data={"test": "data"},
                db=db_session
            )
        
        assert "validation failed" in str(exc_info.value).lower()
    
    async def test_processing_failure(self, sample_manga_session, db_session):
        """Test processing failure handling."""
        agent = TestAgent(fail_processing=True)
        
        with pytest.raises(Exception) as exc_info:
            await agent.process(
                session=sample_manga_session,
                input_data={"test": "data"},
                db=db_session
            )
        
        assert "Processing failed for testing" in str(exc_info.value)
    
    async def test_metrics_update(self):
        """Test metrics updating functionality."""
        agent = TestAgent()
        
        # Initial metrics
        assert agent.metrics["total_processed"] == 0
        assert agent.metrics["total_failures"] == 0
        
        # Simulate successful processing
        await agent._update_metrics(1500, success=True)
        
        assert agent.metrics["total_processed"] == 1
        assert agent.metrics["total_failures"] == 0
        assert agent.metrics["average_processing_time"] == 1500
        
        # Simulate failed processing
        await agent._update_metrics(2000, success=False)
        
        assert agent.metrics["total_processed"] == 2
        assert agent.metrics["total_failures"] == 1
        assert agent.metrics["average_processing_time"] == 1750  # (1500 + 2000) / 2
    
    async def test_feedback_application(self):
        """Test feedback application functionality."""
        agent = TestAgent()
        original_result = {"content": "original", "quality": 0.7}
        feedback = {"type": "improvement", "suggestions": "Make it better"}
        
        adjusted_result = await agent.apply_feedback(original_result, feedback)
        
        assert adjusted_result["content"] == "original"  # Original preserved
        assert adjusted_result["feedback_applied"] == feedback
        assert "feedback_timestamp" in adjusted_result
    
    async def test_preview_generation(self):
        """Test preview generation."""
        agent = TestAgent()
        output_data = {"result": "test output", "images": ["image1.png"]}
        
        preview = await agent.generate_preview(output_data, "high")
        
        assert preview["phase"] == 1
        assert preview["name"] == "Test Agent"
        assert preview["data"] == output_data
        assert preview["quality"] == "high"
        assert "timestamp" in preview
    
    @patch('app.core.redis_client.redis_manager')
    async def test_cache_operations(self, mock_redis):
        """Test cache operations."""
        agent = TestAgent()
        session_id = uuid4()
        output_data = {"cached": "data"}
        
        # Test caching
        mock_redis.set = AsyncMock()
        await agent._cache_result(session_id, output_data)
        mock_redis.set.assert_called_once()
        
        # Test cache retrieval
        mock_redis.get = AsyncMock(return_value='{"cached": "data"}')
        cached_data = await agent._get_cached_result(session_id)
        assert cached_data == output_data
        
        # Test cache miss
        mock_redis.get = AsyncMock(return_value=None)
        cached_data = await agent._get_cached_result(session_id)
        assert cached_data is None
    
    async def test_phase_info_retrieval(self):
        """Test phase information retrieval."""
        agent = TestAgent()
        
        phase_info = agent.get_phase_info()
        
        assert phase_info["phase_number"] == 1
        assert phase_info["phase_name"] == "Test Agent"
        assert phase_info["timeout_seconds"] == 30
        assert "metrics" in phase_info
        assert phase_info["metrics"] == agent.metrics
    
    async def test_concurrent_processing(self, sample_manga_session, db_session):
        """Test concurrent processing doesn't interfere with metrics."""
        agent = TestAgent()
        
        # Process multiple sessions concurrently
        tasks = []
        for i in range(5):
            task = agent.process(
                session=sample_manga_session,
                input_data={"concurrent_test": i},
                db=db_session
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 5
        for result in results:
            assert result.status == "completed"
        
        # Metrics should reflect all processings
        assert agent.metrics["total_processed"] == 5
        assert agent.metrics["total_failures"] == 0


@pytest.mark.asyncio
class TestBaseAgentEdgeCases:
    """Test edge cases and error conditions."""
    
    async def test_empty_input_data(self, sample_manga_session, db_session):
        """Test processing with empty input data."""
        agent = TestAgent()
        
        result = await agent.process(
            session=sample_manga_session,
            input_data={},
            db=db_session
        )
        
        assert result.status == "completed"
        assert result.input_data == {}
    
    async def test_large_input_data(self, sample_manga_session, db_session):
        """Test processing with large input data."""
        agent = TestAgent()
        large_data = {
            "story": "A" * 10000,  # Large text
            "metadata": {f"key_{i}": f"value_{i}" for i in range(1000)}  # Many keys
        }
        
        result = await agent.process(
            session=sample_manga_session,
            input_data=large_data,
            db=db_session
        )
        
        assert result.status == "completed"
        assert len(result.input_data["story"]) == 10000
    
    async def test_unicode_handling(self, sample_manga_session, db_session):
        """Test Unicode and special character handling."""
        agent = TestAgent()
        unicode_data = {
            "japanese": "これは日本語のテストです",
            "emoji": "🎌🎨🔥",
            "special_chars": "!@#$%^&*()[]{}|\\:;\"'<>,.?/~`"
        }
        
        result = await agent.process(
            session=sample_manga_session,
            input_data=unicode_data,
            db=db_session
        )
        
        assert result.status == "completed"
        assert result.input_data["japanese"] == unicode_data["japanese"]
        assert result.input_data["emoji"] == unicode_data["emoji"]
    
    async def test_nested_previous_results(self, sample_manga_session, db_session):
        """Test processing with complex nested previous results."""
        agent = TestAgent()
        previous_results = {
            1: {
                "characters": [
                    {"name": "Hero", "traits": {"strength": 10, "wisdom": 8}},
                    {"name": "Villain", "traits": {"strength": 9, "cunning": 10}}
                ],
                "world": {
                    "locations": ["Forest", "Castle", "Cave"],
                    "rules": {"magic_exists": True, "technology_level": "medieval"}
                }
            }
        }
        
        result = await agent.process(
            session=sample_manga_session,
            input_data={"phase": 2},
            db=db_session,
            previous_results=previous_results
        )
        
        assert result.status == "completed"
        assert result.output_data["previous_results"] == previous_results


@pytest.mark.asyncio
class TestBaseAgentIntegration:
    """Integration tests with other components."""
    
    @patch('app.agents.base_agent.redis_manager')
    async def test_redis_integration(self, mock_redis_manager, sample_manga_session, db_session):
        """Test integration with Redis caching."""
        mock_redis_manager.set = AsyncMock()
        mock_redis_manager.get = AsyncMock(return_value=None)
        
        agent = TestAgent()
        result = await agent.process(
            session=sample_manga_session,
            input_data={"test": "redis_integration"},
            db=db_session
        )
        
        assert result.status == "completed"
        mock_redis_manager.set.assert_called()
    
    async def test_database_transaction_handling(self, sample_manga_session, db_session):
        """Test database transaction handling."""
        agent = TestAgent()
        
        # Simulate database error after processing but before commit
        with patch.object(db_session, 'commit', side_effect=Exception("DB Error")):
            with pytest.raises(Exception):
                await agent.process(
                    session=sample_manga_session,
                    input_data={"test": "db_transaction"},
                    db=db_session
                )
    
    async def test_logging_integration(self, sample_manga_session, db_session):
        """Test logging integration."""
        agent = TestAgent()
        
        with patch.object(agent, 'log_info') as mock_log_info, \
             patch.object(agent, 'log_error') as mock_log_error:
            
            # Test successful processing logs
            await agent.process(
                session=sample_manga_session,
                input_data={"test": "logging"},
                db=db_session
            )
            
            assert mock_log_info.call_count >= 2  # Start and completion logs
            mock_log_error.assert_not_called()
    
    async def test_error_logging(self, sample_manga_session, db_session):
        """Test error logging."""
        agent = TestAgent(fail_processing=True)
        
        with patch.object(agent, 'log_error') as mock_log_error:
            with pytest.raises(Exception):
                await agent.process(
                    session=sample_manga_session,
                    input_data={"test": "error_logging"},
                    db=db_session
                )
            
            mock_log_error.assert_called()
            
            # Verify error details are logged
            call_args = mock_log_error.call_args
            assert "failed" in str(call_args).lower()
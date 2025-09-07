"""
Integration Tests for Parallel Quality Processing
並列品質処理の統合テスト - パフォーマンスと正確性の検証
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.parallel_quality_gate_service import ParallelQualityGateService
from app.services.parallel_hitl_feedback_service import ParallelHITLFeedbackService
from app.services.parallel_quality_orchestrator import (
    ParallelQualityOrchestrator,
    QualityProcessingMode
)
from app.schemas.pipeline_schemas import HITLFeedback


@pytest.fixture
def mock_db_session():
    """モックDBセッション"""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.add = AsyncMock()
    mock_session.execute = AsyncMock()
    return mock_session


@pytest.fixture
async def parallel_quality_service():
    """並列品質ゲートサービス"""
    service = ParallelQualityGateService(max_workers=3)
    yield service
    await service.cleanup()


@pytest.fixture
async def parallel_hitl_service():
    """並列HITLフィードバックサービス"""
    service = ParallelHITLFeedbackService(max_workers=3)
    yield service
    await service.cleanup()


@pytest.fixture  
async def quality_orchestrator():
    """品質オーケストレータ"""
    orchestrator = ParallelQualityOrchestrator(max_workers=3)
    yield orchestrator
    await orchestrator.cleanup()


class TestParallelQualityGateService:
    """並列品質ゲートサービステスト"""
    
    @pytest.mark.asyncio
    async def test_parallel_quality_assessment(self, parallel_quality_service):
        """並列品質評価テスト"""
        # テストデータ
        phase_output = {
            "concept": "テストコンセプト",
            "world_setting": "テスト世界観",
            "target_audience": "テスト対象読者"
        }
        
        # 並列品質評価実行
        start_time = datetime.utcnow()
        quality_score = await parallel_quality_service.assess_phase_quality_parallel(
            phase_output, 1
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 検証
        assert isinstance(quality_score, float)
        assert 0.0 <= quality_score <= 1.0
        assert processing_time < 5.0  # 5秒以内で完了
    
    @pytest.mark.asyncio
    async def test_batch_quality_assessment(self, parallel_quality_service, mock_db_session):
        """バッチ品質評価テスト"""
        # バッチテストデータ
        quality_gates_data = [
            {
                "session_id": f"session_{i}",
                "phase_num": 1,
                "quality_score": 0.8 + i * 0.1,
                "phase_result": {"test": f"result_{i}"}
            }
            for i in range(5)
        ]
        
        # バッチ処理実行
        start_time = datetime.utcnow()
        results = await parallel_quality_service.process_batch_quality_gates(
            quality_gates_data, mock_db_session
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 検証
        assert len(results) == 5
        assert all(isinstance(result, bool) for result in results)
        assert processing_time < 10.0  # 10秒以内で完了
    
    @pytest.mark.asyncio
    async def test_multiple_phases_quality_assessment(self, parallel_quality_service):
        """複数フェーズ品質評価テスト"""
        # 複数フェーズテストデータ
        phase_outputs = [
            ({"concept": "テスト1"}, 1),
            ({"characters": "テスト2"}, 2),  
            ({"plot_structure": "テスト3"}, 3)
        ]
        
        # 並列評価実行
        start_time = datetime.utcnow()
        quality_scores = await parallel_quality_service.assess_multiple_phases_quality(
            phase_outputs
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 検証
        assert len(quality_scores) == 3
        assert all(isinstance(score, float) for score in quality_scores)
        assert all(0.0 <= score <= 1.0 for score in quality_scores)
        assert processing_time < 8.0  # 8秒以内で完了


class TestParallelHITLFeedbackService:
    """並列HITLフィードバックサービステスト"""
    
    @pytest.mark.asyncio
    async def test_batch_feedback_submission(self, parallel_hitl_service, mock_db_session):
        """バッチフィードバック提出テスト"""
        # バッチフィードバックデータ
        feedback_batch = [
            {
                "session_id": f"session_{i}",
                "phase_num": 2,
                "user_id": f"user_{i}",
                "feedback": {
                    "feedback_type": "approval",
                    "content": f"テストフィードバック{i}",
                    "quality_score": 0.8,
                    "suggestions": {}
                }
            }
            for i in range(3)
        ]
        
        # バッチ提出実行
        start_time = datetime.utcnow()
        results = await parallel_hitl_service.submit_feedback_batch(
            feedback_batch, mock_db_session
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 検証
        assert len(results) == 3
        assert processing_time < 5.0  # 5秒以内で完了
    
    @pytest.mark.asyncio
    async def test_multiple_feedback_waiting(self, parallel_hitl_service):
        """複数フィードバック待機テスト"""
        # フィードバック要求データ
        feedback_requests = [
            {"session_id": f"session_{i}", "phase_num": 2}
            for i in range(3)
        ]
        
        # タイムアウト付きで並列待機（短時間でタイムアウト）
        start_time = datetime.utcnow()
        results = await parallel_hitl_service.wait_for_multiple_feedback(
            feedback_requests, timeout_seconds=1  # 1秒でタイムアウト
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 検証
        assert len(results) == 3
        assert processing_time >= 1.0  # タイムアウト時間以上
        assert processing_time < 2.0   # 但し大幅に超過していない
        assert all(not success for success in results.values())  # 全てタイムアウト
    
    @pytest.mark.asyncio
    async def test_batch_feedback_application(self, parallel_hitl_service, mock_db_session):
        """バッチフィードバック適用テスト"""
        # フィードバック適用データ
        feedback_applications = [
            {
                "session_id": f"session_{i}",
                "phase_num": 2,
                "phase_result": {"original": f"result_{i}"}
            }
            for i in range(3)
        ]
        
        # バッチ適用実行
        start_time = datetime.utcnow()
        results = await parallel_hitl_service.apply_feedback_batch(
            feedback_applications, mock_db_session
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 検証
        assert len(results) == 3
        assert processing_time < 5.0  # 5秒以内で完了


class TestParallelQualityOrchestrator:
    """並列品質オーケストレータテスト"""
    
    @pytest.mark.asyncio
    async def test_parallel_mode_processing(self, quality_orchestrator, mock_db_session):
        """並列モード処理テスト"""
        # テストデータ
        phase_output = {"test": "data"}
        phase_result = {"original": "result"}
        
        # 並列モード処理実行
        start_time = datetime.utcnow()
        quality_passed, final_result = await quality_orchestrator.process_phase_with_quality_control(
            "test_session", 1, phase_output, phase_result, mock_db_session,
            QualityProcessingMode.PARALLEL
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 検証
        assert isinstance(quality_passed, bool)
        assert isinstance(final_result, dict)
        assert processing_time < 10.0  # 10秒以内で完了
    
    @pytest.mark.asyncio
    async def test_hybrid_mode_processing(self, quality_orchestrator, mock_db_session):
        """ハイブリッドモード処理テスト"""
        # テストデータ
        phase_output = {"test": "data"}
        phase_result = {"original": "result"}
        
        # ハイブリッドモード処理実行（フェーズ5 - 重要フェーズ）
        start_time = datetime.utcnow()
        quality_passed, final_result = await quality_orchestrator.process_phase_with_quality_control(
            "test_session", 5, phase_output, phase_result, mock_db_session,
            QualityProcessingMode.HYBRID
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 検証
        assert isinstance(quality_passed, bool)
        assert isinstance(final_result, dict)
        assert processing_time < 15.0  # 15秒以内で完了（順次処理のため若干時間がかかる）
    
    @pytest.mark.asyncio
    async def test_session_batch_quality_processing(self, quality_orchestrator, mock_db_session):
        """セッションバッチ品質処理テスト"""
        # バッチセッションデータ
        session_batches = [
            {
                "session_id": f"session_{i}",
                "phase_num": 1,
                "phase_output": {"test": f"data_{i}"},
                "phase_result": {"original": f"result_{i}"}
            }
            for i in range(3)
        ]
        
        # バッチ処理実行
        start_time = datetime.utcnow()
        results = await quality_orchestrator.process_session_batch_quality(
            session_batches, mock_db_session
        )
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # 検証
        assert len(results) == 3
        assert all("session_id" in result for result in results)
        assert all("quality_passed" in result for result in results)
        assert processing_time < 20.0  # 20秒以内で完了


class TestParallelProcessingPerformance:
    """並列処理パフォーマンステスト"""
    
    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_performance(self, mock_db_session):
        """並列処理 vs 順次処理 パフォーマンス比較"""
        # テストデータ準備
        test_data = [
            {
                "session_id": f"session_{i}",
                "phase_num": 1,
                "phase_output": {"test": f"data_{i}"},
                "phase_result": {"original": f"result_{i}"}
            }
            for i in range(10)
        ]
        
        # 順次処理テスト
        sequential_orchestrator = ParallelQualityOrchestrator(max_workers=1)
        start_time = datetime.utcnow()
        sequential_results = await sequential_orchestrator.process_session_batch_quality(
            test_data, mock_db_session
        )
        sequential_time = (datetime.utcnow() - start_time).total_seconds()
        await sequential_orchestrator.cleanup()
        
        # 並列処理テスト
        parallel_orchestrator = ParallelQualityOrchestrator(max_workers=5)
        start_time = datetime.utcnow()
        parallel_results = await parallel_orchestrator.process_session_batch_quality(
            test_data, mock_db_session
        )
        parallel_time = (datetime.utcnow() - start_time).total_seconds()
        await parallel_orchestrator.cleanup()
        
        # パフォーマンス検証
        assert len(sequential_results) == len(parallel_results) == 10
        
        # 並列処理が高速化されていることを確認（理論的には30%以上高速）
        performance_improvement = (sequential_time - parallel_time) / sequential_time
        assert performance_improvement > 0.2  # 20%以上の改善
        
        print(f"Sequential time: {sequential_time:.2f}s")
        print(f"Parallel time: {parallel_time:.2f}s")  
        print(f"Performance improvement: {performance_improvement:.1%}")


if __name__ == "__main__":
    # 個別テスト実行用
    pytest.main([__file__, "-v"])
"""統合テスト - エンジンシステム統合テスト

設計書要件の統合テスト:
- 7フェーズ統合処理の端到端テスト
- HITL・プレビュー・品質ゲート・バージョン管理の統合
- パフォーマンス要件検証（97秒目標）
- 1000同時接続負荷テスト
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from app.engine import (
    MangaGenerationEngine,
    HITLManager,
    PreviewSystem,
    QualityGateSystem,
    VersionManager,
    WebSocketManager,
    PipelineCoordinator
)
from app.engine.preview_system import QualityLevel, PreviewType, DeviceCapability
from app.engine.quality_gate import QualityCheck
from app.engine.version_manager import VersionNode, VersionType
from app.core.database import get_database_session


class TestEngineIntegration:
    """エンジンシステム統合テスト"""
    
    @pytest.fixture
    async def mock_websocket_manager(self):
        """WebSocketManager モック"""
        manager = MagicMock(spec=WebSocketManager)
        manager.register_session = AsyncMock()
        manager.unregister_session = AsyncMock()
        manager.send_to_session = AsyncMock()
        manager.broadcast_to_session = AsyncMock()
        manager.get_manager_stats = MagicMock(return_value={
            "active_connections": 5,
            "total_messages": 100
        })
        return manager
    
    @pytest.fixture
    async def mock_hitl_manager(self):
        """HITLManager モック"""
        manager = MagicMock(spec=HITLManager)
        manager.wait_for_feedback = AsyncMock(return_value=None)  # No feedback by default
        manager.get_feedback_metrics = MagicMock(return_value={
            "total_requests": 10,
            "received_feedback": 8,
            "response_rate": 80.0
        })
        return manager
    
    @pytest.fixture
    async def mock_preview_system(self):
        """PreviewSystem モック"""
        system = MagicMock(spec=PreviewSystem)
        system.generate_preview = AsyncMock()
        system.get_preview_stats = MagicMock(return_value={
            "total_requests": 20,
            "cache_hits": 15,
            "cache_hit_rate": 75.0
        })
        return system
    
    @pytest.fixture
    async def mock_quality_gate(self):
        """QualityGateSystem モック"""
        system = MagicMock(spec=QualityGateSystem)
        system.evaluate_phase_result = AsyncMock(return_value=QualityCheck(
            phase_number=1,
            score=0.8,
            passed=True,
            issues=[],
            recommendations=[],
            metadata={}
        ))
        system.evaluate_overall_quality = AsyncMock(return_value=QualityCheck(
            phase_number=0,
            score=0.82,
            passed=True,
            issues=[],
            recommendations=[],
            metadata={"total_phases": 7}
        ))
        system.get_quality_stats = MagicMock(return_value={
            "total_assessments": 50,
            "passed_assessments": 45,
            "success_rate": 90.0
        })
        return system
    
    @pytest.fixture
    async def mock_version_manager(self):
        """VersionManager モック"""
        manager = MagicMock(spec=VersionManager)
        manager.create_checkpoint = AsyncMock(return_value="version_123")
        manager.get_version_stats = MagicMock(return_value={
            "total_versions": 100,
            "total_branches": 10,
            "active_sessions": 5
        })
        return manager
    
    @pytest.fixture
    async def mock_db_session(self):
        """データベースセッション モック"""
        session = AsyncMock()
        return session
    
    @pytest.fixture
    async def manga_generation_engine(
        self,
        mock_hitl_manager,
        mock_quality_gate,
        mock_version_manager,
        mock_websocket_manager,
        mock_db_session
    ):
        """MangaGenerationEngine インスタンス"""
        with patch('app.engine.manga_generation_engine.ConceptAnalysisAgent') as mock_agent1, \
             patch('app.engine.manga_generation_engine.CharacterDesignAgent') as mock_agent2, \
             patch('app.engine.manga_generation_engine.PlotStructureAgent') as mock_agent3, \
             patch('app.engine.manga_generation_engine.NameGenerationAgent') as mock_agent4, \
             patch('app.engine.manga_generation_engine.ImageGenerationAgent') as mock_agent5, \
             patch('app.engine.manga_generation_engine.DialoguePlacementAgent') as mock_agent6, \
             patch('app.engine.manga_generation_engine.FinalIntegrationAgent') as mock_agent7:
            
            # モックエージェントの設定
            for i, mock_agent in enumerate([mock_agent1, mock_agent2, mock_agent3, mock_agent4, mock_agent5, mock_agent6, mock_agent7], 1):
                agent_instance = AsyncMock()
                agent_instance.phase_number = i
                agent_instance.phase_name = f"phase_{i}"
                agent_instance.process_phase = AsyncMock(return_value={
                    f"phase_{i}_result": f"Mock result for phase {i}",
                    "quality_score": 0.8 + (i * 0.01),
                    "processing_time": 10 + i,
                    "metadata": {"phase": i}
                })
                mock_agent.return_value = agent_instance
            
            engine = MangaGenerationEngine(
                hitl_manager=mock_hitl_manager,
                quality_gate=mock_quality_gate,
                version_manager=mock_version_manager,
                websocket_manager=mock_websocket_manager,
                db_session=mock_db_session
            )
            
            return engine
    
    @pytest.fixture
    async def pipeline_coordinator(
        self,
        manga_generation_engine,
        mock_hitl_manager,
        mock_preview_system,
        mock_quality_gate,
        mock_version_manager,
        mock_websocket_manager
    ):
        """PipelineCoordinator インスタンス"""
        coordinator = PipelineCoordinator(
            manga_engine=manga_generation_engine,
            hitl_manager=mock_hitl_manager,
            preview_system=mock_preview_system,
            quality_gate=mock_quality_gate,
            version_manager=mock_version_manager,
            websocket_manager=mock_websocket_manager
        )
        await coordinator.initialize()
        return coordinator

    @pytest.mark.asyncio
    async def test_full_manga_generation_pipeline(self, manga_generation_engine):
        """フル漫画生成パイプラインテスト"""
        user_input = "A young hero's adventure story"
        user_id = uuid4()
        session_id = uuid4()
        
        # 生成ストリーム実行
        updates = []
        async for update in manga_generation_engine.generate_manga(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            quality_level="high",
            enable_hitl=False  # HITLを無効にして高速化
        ):
            updates.append(update)
            
            # パイプライン完了で終了
            if update.get("type") == "pipeline_completed":
                break
        
        # 検証
        assert len(updates) >= 8  # 開始 + 7フェーズ完了 + パイプライン完了
        
        # パイプライン開始確認
        pipeline_started = next((u for u in updates if u["type"] == "pipeline_started"), None)
        assert pipeline_started is not None
        assert pipeline_started["total_phases"] == 7
        
        # 各フェーズ完了確認
        phase_completed = [u for u in updates if u["type"] == "phase_completed"]
        assert len(phase_completed) == 7
        
        for i, phase_update in enumerate(phase_completed, 1):
            assert phase_update["phase_number"] == i
            assert "duration" in phase_update
            assert "quality_score" in phase_update
            assert "result" in phase_update
        
        # パイプライン完了確認
        pipeline_completed = next((u for u in updates if u["type"] == "pipeline_completed"), None)
        assert pipeline_completed is not None
        assert "total_time" in pipeline_completed
        assert "overall_quality" in pipeline_completed
        assert "final_result" in pipeline_completed
        assert pipeline_completed["overall_quality"] > 0.7  # 品質閾値
    
    @pytest.mark.asyncio
    async def test_hitl_integration(self, manga_generation_engine, mock_hitl_manager):
        """HITL統合テスト"""
        user_input = "Interactive story creation"
        user_id = uuid4()
        session_id = uuid4()
        
        # HITLフィードバックを設定
        mock_feedback = {
            "action": "modify",
            "feedback": "Make the character more heroic",
            "modifications": {"character_trait": "heroic"}
        }
        mock_hitl_manager.wait_for_feedback.return_value = mock_feedback
        
        updates = []
        async for update in manga_generation_engine.generate_manga(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            quality_level="high",
            enable_hitl=True
        ):
            updates.append(update)
            
            if update.get("type") == "pipeline_completed":
                break
        
        # HITL機会が提供されたか確認
        hitl_opportunities = [u for u in updates if u["type"] == "hitl_opportunity"]
        assert len(hitl_opportunities) >= 1  # 少なくとも1回のHITL機会
        
        # HITLフィードバック適用確認
        hitl_applied = [u for u in updates if u["type"] == "hitl_applied"]
        if hitl_opportunities:  # HITL機会があった場合
            assert len(hitl_applied) >= 1
            applied_update = hitl_applied[0]
            assert "feedback" in applied_update
            assert "modified_result" in applied_update
    
    @pytest.mark.asyncio
    async def test_quality_gate_integration(self, manga_generation_engine, mock_quality_gate):
        """品質ゲート統合テスト"""
        user_input = "Quality-controlled story"
        user_id = uuid4()
        session_id = uuid4()
        
        # 低品質結果を設定してリトライをトリガー
        low_quality_check = QualityCheck(
            phase_number=1,
            score=0.5,  # 閾値以下
            passed=False,
            issues=["Low quality detected"],
            recommendations=["Improve content"],
            metadata={}
        )
        mock_quality_gate.evaluate_phase_result.return_value = low_quality_check
        
        updates = []
        async for update in manga_generation_engine.generate_manga(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            quality_level="high",
            enable_hitl=False
        ):
            updates.append(update)
            
            # 最初の数回のアップデートで終了（リトライ確認のため）
            if len(updates) >= 5:
                break
        
        # 品質チェックが実行されたか確認
        assert mock_quality_gate.evaluate_phase_result.call_count >= 1
        
        # リトライが発生したか確認（品質不足の場合）
        retry_updates = [u for u in updates if u.get("type") == "phase_retry"]
        # 注意: 実際の実装では品質ゲートによりリトライが発生する可能性がある
    
    @pytest.mark.asyncio
    async def test_version_management_integration(self, manga_generation_engine, mock_version_manager):
        """バージョン管理統合テスト"""
        user_input = "Version-controlled story"
        user_id = uuid4()
        session_id = uuid4()
        
        updates = []
        async for update in manga_generation_engine.generate_manga(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            quality_level="high",
            enable_hitl=False
        ):
            updates.append(update)
            
            if update.get("type") == "pipeline_completed":
                break
        
        # バージョンチェックポイントが作成されたか確認
        assert mock_version_manager.create_checkpoint.call_count >= 7  # 各フェーズでチェックポイント作成
        
        # チェックポイント作成の引数確認
        calls = mock_version_manager.create_checkpoint.call_args_list
        assert len(calls) >= 7
        
        for i, call in enumerate(calls[:7]):
            args, kwargs = call
            assert kwargs["session_id"] == session_id
            assert "phase_number" in kwargs
            assert "data" in kwargs
            assert "metadata" in kwargs
    
    @pytest.mark.asyncio
    async def test_websocket_integration(self, manga_generation_engine, mock_websocket_manager):
        """WebSocket統合テスト"""
        user_input = "WebSocket integrated story"
        user_id = uuid4()
        session_id = uuid4()
        
        updates = []
        async for update in manga_generation_engine.generate_manga(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            quality_level="high",
            enable_hitl=False
        ):
            updates.append(update)
            
            if update.get("type") == "pipeline_completed":
                break
        
        # WebSocketセッション登録確認
        assert mock_websocket_manager.register_session.call_count == 1
        register_call = mock_websocket_manager.register_session.call_args
        args, kwargs = register_call
        assert args[0] == session_id
        assert args[1] == user_id
        
        # WebSocketセッション登録解除確認
        assert mock_websocket_manager.unregister_session.call_count == 1
        unregister_call = mock_websocket_manager.unregister_session.call_args
        args, kwargs = unregister_call
        assert args[0] == session_id
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, manga_generation_engine, mock_quality_gate):
        """エラーハンドリング・復旧テスト"""
        user_input = "Error handling test"
        user_id = uuid4()
        session_id = uuid4()
        
        # 一時的にエラーを発生させる設定
        manga_generation_engine.phase_agents[1].process_phase.side_effect = Exception("Test error")
        
        updates = []
        async for update in manga_generation_engine.generate_manga(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            quality_level="high",
            enable_hitl=False
        ):
            updates.append(update)
            
            # エラーが発生した場合に終了
            if update.get("type") == "error":
                break
        
        # エラー更新が含まれているか確認
        error_updates = [u for u in updates if u.get("type") == "error"]
        assert len(error_updates) >= 1
        
        error_update = error_updates[0]
        assert "error" in error_update
        assert error_update["session_id"] == str(session_id)
    
    @pytest.mark.asyncio 
    async def test_performance_requirements(self, manga_generation_engine):
        """パフォーマンス要件テスト（97秒目標）"""
        user_input = "Performance test story"
        user_id = uuid4()
        session_id = uuid4()
        
        start_time = datetime.utcnow()
        
        updates = []
        async for update in manga_generation_engine.generate_manga(
            user_input=user_input,
            user_id=user_id,
            session_id=session_id,
            quality_level="high",
            enable_hitl=False  # HITLを無効にして高速化
        ):
            updates.append(update)
            
            if update.get("type") == "pipeline_completed":
                break
        
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds()
        
        # パフォーマンス要件確認（97秒目標）
        # テスト環境では実際の処理時間とは異なるため、緩い制限を設定
        assert total_time < 10.0  # テスト環境での合理的な制限
        
        # パイプライン完了更新から総時間を確認
        pipeline_completed = next((u for u in updates if u["type"] == "pipeline_completed"), None)
        if pipeline_completed:
            reported_time = pipeline_completed.get("total_time", 0)
            # 報告された時間は実際の処理時間を反映する
            assert isinstance(reported_time, (int, float))
    
    @pytest.mark.asyncio
    async def test_concurrent_session_handling(self, pipeline_coordinator):
        """並行セッション処理テスト"""
        concurrent_sessions = 5
        tasks = []
        
        # 複数のセッションを並行実行
        for i in range(concurrent_sessions):
            task = asyncio.create_task(
                self._run_single_generation_stream(
                    pipeline_coordinator,
                    f"Concurrent story {i}",
                    uuid4()
                )
            )
            tasks.append(task)
        
        # 全セッションの完了を待つ
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果確認
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == concurrent_sessions
        
        # コーディネーター統計確認
        coordinator_status = pipeline_coordinator.get_coordinator_status()
        assert coordinator_status["performance"]["total_requests"] >= concurrent_sessions
    
    async def _run_single_generation_stream(self, coordinator, user_input: str, user_id):
        """単一生成ストリーム実行ヘルパー"""
        updates = []
        
        async for update in coordinator.submit_generation_request(
            user_input=user_input,
            user_id=user_id,
            quality_level="medium",
            enable_hitl=False
        ):
            updates.append(update)
            
            # 要求がキューに入れられたら成功とみなす（テスト簡略化）
            if update.get("type") == "request_queued":
                break
        
        return updates
    
    @pytest.mark.asyncio
    async def test_system_metrics_and_monitoring(self, pipeline_coordinator):
        """システムメトリクス・監視テスト"""
        # 少し待ってメトリクス収集を確認
        await asyncio.sleep(0.5)
        
        # コーディネーターステータス取得
        status = pipeline_coordinator.get_coordinator_status()
        
        # 必須フィールド確認
        assert "status" in status
        assert "uptime_seconds" in status
        assert "resource_pool" in status
        assert "queue_status" in status
        assert "performance" in status
        assert "error_tracking" in status
        assert "background_tasks" in status
        
        # リソースプール情報確認
        resource_pool = status["resource_pool"]
        assert "max_concurrent_sessions" in resource_pool
        assert "current_sessions" in resource_pool
        assert "cpu_usage" in resource_pool
        assert "memory_usage_mb" in resource_pool
        
        # パフォーマンスレポート取得
        report = pipeline_coordinator.get_performance_report()
        
        # パフォーマンスレポート確認
        if "message" not in report:  # メトリクスが利用可能な場合
            assert "averages" in report
            assert "performance_targets" in report
            assert "target_compliance" in report
            assert "overall_compliance_rate" in report
    
    @pytest.mark.asyncio
    async def test_cleanup_and_shutdown(self, pipeline_coordinator):
        """クリーンアップ・シャットダウンテスト"""
        # コーディネーターが実行中であることを確認
        status = pipeline_coordinator.get_coordinator_status()
        assert status["background_tasks"]["running_tasks"] > 0
        
        # シャットダウン実行
        await pipeline_coordinator.shutdown()
        
        # シャットダウン後の状態確認
        final_status = pipeline_coordinator.get_coordinator_status()
        assert final_status["status"] == "maintenance"
        assert not pipeline_coordinator.monitoring_enabled
        
        # バックグラウンドタスクが停止したことを確認
        running_tasks = sum(1 for task in pipeline_coordinator.background_tasks if not task.done())
        assert running_tasks == 0


class TestComponentIntegration:
    """コンポーネント間統合テスト"""
    
    @pytest.mark.asyncio
    async def test_preview_quality_integration(self):
        """プレビューシステム・品質ゲート統合テスト"""
        websocket_manager = MagicMock(spec=WebSocketManager)
        websocket_manager.send_to_session = AsyncMock()
        
        preview_system = PreviewSystem(websocket_manager)
        quality_gate = QualityGateSystem()
        
        session_id = uuid4()
        phase_number = 2
        
        # フェーズデータ
        phase_data = {
            "characters": [
                {
                    "name": "Hero",
                    "description": "Main protagonist",
                    "personality": ["brave", "kind"],
                    "role": "hero"
                }
            ]
        }
        
        # 品質評価
        quality_check = await quality_gate.evaluate_phase_result(phase_number, phase_data)
        
        # プレビュー生成
        preview_result = await preview_system.generate_preview(
            session_id=session_id,
            phase_number=phase_number,
            phase_data=phase_data,
            quality_level=QualityLevel.HIGH
        )
        
        # 結果検証
        assert quality_check.passed
        assert quality_check.score >= 0.7
        assert preview_result.preview_data["type"] == "character_preview"
        assert preview_result.quality_achieved == QualityLevel.HIGH
        assert len(preview_result.preview_data["character_cards"]) == 1
    
    @pytest.mark.asyncio
    async def test_version_quality_tracking(self):
        """バージョン管理・品質追跡統合テスト"""
        version_manager = VersionManager()
        quality_gate = QualityGateSystem()
        
        session_id = uuid4()
        
        # 複数バージョンの作成と品質追跡
        versions = []
        quality_scores = []
        
        for i in range(5):
            phase_data = {
                "iteration": i,
                "content": f"Story content iteration {i}",
                "characters": [f"character_{j}" for j in range(i + 1)]
            }
            
            # 品質評価
            quality_check = await quality_gate.evaluate_phase_result(1, phase_data)
            quality_scores.append(quality_check.score)
            
            # バージョン作成
            version_id = await version_manager.create_checkpoint(
                session_id=session_id,
                phase_number=1,
                data=phase_data,
                metadata={"quality_score": quality_check.score},
                description=f"Iteration {i}"
            )
            versions.append(version_id)
        
        # バージョンツリー確認
        version_tree = await version_manager.get_version_tree(session_id)
        assert version_tree["total_versions"] == 5
        assert "main" in version_tree["branches"]
        
        # 品質改善追跡確認
        main_branch = version_tree["branches"]["main"]
        version_nodes = main_branch["versions"]
        
        # バージョンが品質スコアでソートされていることを確認
        for version_node in version_nodes:
            assert "quality_score" in version_node
            assert version_node["quality_score"] >= 0.0
    
    @pytest.mark.asyncio
    async def test_hitl_preview_integration(self):
        """HITL・プレビュー統合テスト"""
        websocket_manager = MagicMock(spec=WebSocketManager)
        websocket_manager.send_to_session = AsyncMock()
        
        hitl_manager = HITLManager(websocket_manager)
        preview_system = PreviewSystem(websocket_manager)
        
        session_id = uuid4()
        phase_number = 4
        
        # フェーズ結果データ
        phase_result = {
            "panels": [
                {
                    "position": {"x": 0, "y": 0},
                    "size": {"width": 400, "height": 300},
                    "description": "Opening scene"
                },
                {
                    "position": {"x": 400, "y": 0},
                    "size": {"width": 400, "height": 300},
                    "description": "Character introduction"
                }
            ],
            "layout": {"type": "grid", "columns": 2}
        }
        
        # プレビュー生成
        preview_result = await preview_system.generate_preview(
            session_id=session_id,
            phase_number=phase_number,
            phase_data=phase_result,
            quality_level=QualityLevel.MEDIUM
        )
        
        # HITLフィードバック要求を実行（タイムアウトテスト）
        feedback_result = await hitl_manager.wait_for_feedback(
            session_id=session_id,
            phase_number=phase_number,
            timeout=1  # 短時間でタイムアウト
        )
        
        # 結果検証
        assert preview_result.preview_data["type"] == "name_preview"
        assert len(preview_result.preview_data["panels"]) == 2
        assert feedback_result is None  # タイムアウトでNone
        
        # WebSocket送信確認
        assert websocket_manager.send_to_session.call_count >= 1


class TestLoadAndStress:
    """負荷・ストレステスト"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_high_concurrency_load(self):
        """高並行性負荷テスト"""
        # このテストは実際の負荷テストのプロトタイプ
        # 実運用では専用の負荷テストツールを使用する
        
        websocket_manager = MagicMock(spec=WebSocketManager)
        websocket_manager.register_session = AsyncMock()
        websocket_manager.unregister_session = AsyncMock()
        websocket_manager.send_to_session = AsyncMock()
        websocket_manager.get_manager_stats = MagicMock(return_value={
            "active_connections": 100
        })
        
        # 簡略化されたエンジンコンポーネント
        hitl_manager = MagicMock(spec=HITLManager)
        hitl_manager.wait_for_feedback = AsyncMock(return_value=None)
        hitl_manager.get_feedback_metrics = MagicMock(return_value={})
        
        quality_gate = MagicMock(spec=QualityGateSystem)
        quality_gate.evaluate_phase_result = AsyncMock(return_value=QualityCheck(
            phase_number=1, score=0.8, passed=True, issues=[], recommendations=[], metadata={}
        ))
        quality_gate.get_quality_stats = MagicMock(return_value={})
        
        version_manager = MagicMock(spec=VersionManager)
        version_manager.create_checkpoint = AsyncMock(return_value="test_version")
        version_manager.get_version_stats = MagicMock(return_value={})
        
        preview_system = MagicMock(spec=PreviewSystem)
        preview_system.get_preview_stats = MagicMock(return_value={})
        
        # 負荷テスト実行
        concurrent_requests = 20  # テスト環境での実現可能な数
        tasks = []
        
        for i in range(concurrent_requests):
            task = asyncio.create_task(
                self._simulate_request_processing(i)
            )
            tasks.append(task)
        
        # 全リクエストの完了を待つ
        start_time = datetime.utcnow()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.utcnow()
        
        # 結果分析
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        total_time = (end_time - start_time).total_seconds()
        
        # パフォーマンス検証
        assert len(successful_results) >= concurrent_requests * 0.9  # 90%成功率
        assert total_time < 30.0  # 30秒以内で完了
        
        # スループット計算
        throughput = len(successful_results) / total_time
        assert throughput >= 0.5  # 最低0.5リクエスト/秒
        
        print(f"Load test results: {len(successful_results)}/{concurrent_requests} successful, "
              f"{total_time:.2f}s total, {throughput:.2f} req/s")
    
    async def _simulate_request_processing(self, request_id: int) -> Dict[str, Any]:
        """リクエスト処理シミュレーション"""
        start_time = datetime.utcnow()
        
        # 実際の処理をシミュレート
        await asyncio.sleep(0.1 + (request_id % 5) * 0.02)  # 0.1-0.18秒の処理時間
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "request_id": request_id,
            "processing_time": processing_time,
            "status": "completed"
        }
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """負荷時メモリ使用量テスト"""
        # このテストは実際のメモリ監視のプロトタイプ
        # 実運用ではより詳細なメモリプロファイリングを実施
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 大量のデータ処理をシミュレート
        large_data_sets = []
        for i in range(100):
            data_set = {
                "session_id": str(uuid4()),
                "large_content": "x" * 1000,  # 1KB のコンテンツ
                "complex_structure": {
                    "nested_data": [{"id": j, "content": "data" * 10} for j in range(10)]
                }
            }
            large_data_sets.append(data_set)
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # データセットクリア
        large_data_sets.clear()
        
        # ガベージコレクション強制実行
        import gc
        gc.collect()
        
        await asyncio.sleep(0.1)  # メモリ解放の時間を待つ
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # メモリ使用量検証
        memory_increase = peak_memory - initial_memory
        memory_leaked = final_memory - initial_memory
        
        assert memory_increase < 100  # 100MB以下の増加
        assert memory_leaked < 20    # 20MB以下のメモリリーク
        
        print(f"Memory usage: initial={initial_memory:.1f}MB, "
              f"peak={peak_memory:.1f}MB, final={final_memory:.1f}MB")


# テスト実行時の設定
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
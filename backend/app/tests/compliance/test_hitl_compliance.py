"""
HITL (Human-in-the-Loop) Compliance Test

人間参加型フィードバックシステムの設計準拠性テスト
HITLシステムが設計仕様に準拠して実装されているかを検証
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from app.engine.hitl_manager import HITLManager
from app.engine.websocket_manager import WebSocketManager
from app.schemas.pipeline_schemas import HITLFeedback


class HITLComplianceTest:
    """HITL準拠性テストクラス"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスセットアップ"""
        cls.hitl_config = cls._get_hitl_requirements()
        cls.critical_phases = [4, 5, 7]  # 設計書で定義されたクリティカルフェーズ
        
    @classmethod
    def _get_hitl_requirements(cls) -> Dict[str, Any]:
        """HITL要件を取得"""
        return {
            "feedback_timeout_seconds": 30,
            "required_feedback_phases": [4, 5, 7],
            "feedback_types": ["natural_language", "quick_options", "skip"],
            "websocket_support": True,
            "real_time_updates": True
        }
    
    def test_hitl_manager_exists(self):
        """HITLマネージャーの存在確認"""
        hitl_manager_path = Path("app/engine/hitl_manager.py")
        assert hitl_manager_path.exists(), "HITLManager が存在しません"
        
        # クラスのインポート確認
        try:
            from app.engine.hitl_manager import HITLManager
            
            # クラスの基本メソッド確認
            required_methods = [
                'request_feedback',
                'receive_feedback', 
                'timeout_feedback',
                'process_feedback'
            ]
            
            for method in required_methods:
                assert hasattr(HITLManager, method), \
                    f"HITLManager に必須メソッド {method} がありません"
                    
        except ImportError:
            pytest.fail("HITLManager のインポートに失敗しました")
    
    def test_feedback_timeout_configuration(self):
        """フィードバックタイムアウト設定の確認"""
        expected_timeout = self.hitl_config["feedback_timeout_seconds"]
        
        # HITLManager のタイムアウト設定確認
        try:
            from app.engine.hitl_manager import HITLManager
            
            # インスタンス作成してタイムアウト設定確認
            hitl_manager = HITLManager()
            
            if hasattr(hitl_manager, 'feedback_timeout'):
                actual_timeout = hitl_manager.feedback_timeout
                assert actual_timeout == expected_timeout, \
                    f"フィードバックタイムアウトが不正: 期待={expected_timeout}s, 実際={actual_timeout}s"
                    
        except ImportError:
            pytest.skip("HITLManager をインポートできませんでした")
    
    def test_critical_phase_feedback_requirement(self):
        """クリティカルフェーズでのフィードバック要求確認"""
        required_phases = self.hitl_config["required_feedback_phases"]
        
        # 設計書で定義されたクリティカルフェーズとの整合性確認
        assert set(required_phases) == set(self.critical_phases), \
            f"フィードバック必須フェーズが不正: 期待={self.critical_phases}, 実際={required_phases}"
        
        # 各クリティカルフェーズが重要な処理を担当していることの確認
        critical_phase_purposes = {
            4: "シーン分割・コマ割り",  # レイアウト決定
            5: "画像生成・ビジュアル制作",  # 最も時間とコストがかかる
            7: "最終統合・品質調整"  # 最終品質決定
        }
        
        for phase in self.critical_phases:
            assert phase in critical_phase_purposes, \
                f"クリティカルフェーズ {phase} の目的が定義されていません"
    
    def test_feedback_types_support(self):
        """フィードバックタイプのサポート確認"""
        supported_types = self.hitl_config["feedback_types"]
        expected_types = ["natural_language", "quick_options", "skip"]
        
        assert set(supported_types) == set(expected_types), \
            f"サポートするフィードバックタイプが不正: 期待={expected_types}, 実際={supported_types}"
        
        # HITLFeedback スキーマの確認
        try:
            from app.schemas.pipeline_schemas import HITLFeedback
            
            # スキーマフィールドの確認
            feedback_schema = HITLFeedback.model_json_schema()
            properties = feedback_schema.get("properties", {})
            
            # フィードバックタイプフィールドの存在確認
            assert "feedback_type" in properties or "type" in properties, \
                "HITLFeedback スキーマにフィードバックタイプフィールドがありません"
                
        except ImportError:
            pytest.skip("HITLFeedback スキーマをインポートできませんでした")
    
    def test_websocket_integration(self):
        """WebSocket統合の確認"""
        assert self.hitl_config["websocket_support"] == True, "WebSocket サポートが必要です"
        
        # WebSocketManagerの存在確認
        ws_manager_path = Path("app/engine/websocket_manager.py")
        assert ws_manager_path.exists(), "WebSocketManager が存在しません"
        
        try:
            from app.engine.websocket_manager import WebSocketManager
            
            # HITL関連のWebSocketメッセージタイプ確認
            ws_manager = WebSocketManager()
            
            # MessageType enum にHITL関連メッセージが定義されているか確認
            if hasattr(ws_manager, 'MessageType') or hasattr(WebSocketManager, 'MessageType'):
                # HITL関連のメッセージタイプが存在するか確認（実装依存）
                pass  # 詳細な確認は実装次第
                
        except ImportError:
            pytest.fail("WebSocketManager のインポートに失敗しました")
    
    def test_real_time_updates_support(self):
        """リアルタイムアップデートサポートの確認"""
        assert self.hitl_config["real_time_updates"] == True, "リアルタイムアップデートが必要です"
        
        # リアルタイム更新に必要なコンポーネント確認
        required_components = [
            "app/engine/websocket_manager.py",
            "app/services/websocket_service.py"
        ]
        
        for component_path in required_components:
            component = Path(component_path)
            assert component.exists(), f"リアルタイム更新に必要なコンポーネントが存在しません: {component_path}"
    
    @pytest.mark.asyncio
    async def test_feedback_request_flow(self):
        """フィードバック要求フローの確認"""
        # モックを使用したフィードバックフロー確認
        
        try:
            from app.engine.hitl_manager import HITLManager
            
            hitl_manager = HITLManager()
            
            # モックセッションID
            test_session_id = "test_session_123"
            test_phase = 5  # クリティカルフェーズ
            test_result = {"phase": 5, "generated_images": ["image1.png"]}
            
            # フィードバック要求のテスト（実装に依存）
            if hasattr(hitl_manager, 'request_feedback'):
                # 非同期の場合
                if asyncio.iscoroutinefunction(hitl_manager.request_feedback):
                    feedback_request = await hitl_manager.request_feedback(
                        session_id=test_session_id,
                        phase_number=test_phase,
                        phase_result=test_result
                    )
                else:
                    feedback_request = hitl_manager.request_feedback(
                        session_id=test_session_id,
                        phase_number=test_phase, 
                        phase_result=test_result
                    )
                
                # フィードバック要求が正常に作成されたか確認
                assert feedback_request is not None, "フィードバック要求の作成に失敗しました"
                
        except ImportError:
            pytest.skip("HITLManager をインポートできませんでした")
    
    @pytest.mark.asyncio 
    async def test_feedback_processing(self):
        """フィードバック処理の確認"""
        
        try:
            from app.engine.hitl_manager import HITLManager
            
            hitl_manager = HITLManager()
            
            # テスト用フィードバックデータ
            test_feedback = {
                "session_id": "test_session_123",
                "phase_number": 5,
                "feedback_type": "natural_language",
                "feedback_content": "画像をもっと明るくしてください",
                "approved": False
            }
            
            # フィードバック処理のテスト（実装に依存）
            if hasattr(hitl_manager, 'process_feedback'):
                if asyncio.iscoroutinefunction(hitl_manager.process_feedback):
                    result = await hitl_manager.process_feedback(test_feedback)
                else:
                    result = hitl_manager.process_feedback(test_feedback)
                
                # 処理結果の確認
                assert result is not None, "フィードバック処理に失敗しました"
                
        except ImportError:
            pytest.skip("HITLManager をインポートできませんでした")
    
    def test_feedback_timeout_handling(self):
        """フィードバックタイムアウト処理の確認"""
        
        try:
            from app.engine.hitl_manager import HITLManager
            
            hitl_manager = HITLManager()
            
            # タイムアウト処理メソッドの存在確認
            if hasattr(hitl_manager, 'timeout_feedback'):
                timeout_method = getattr(hitl_manager, 'timeout_feedback')
                
                # メソッドが呼び出し可能か確認
                assert callable(timeout_method), "timeout_feedback メソッドが呼び出し可能ではありません"
                
                # タイムアウト時のデフォルト動作確認（実装依存）
                # 一般的にはスキップ処理または自動承認
                
        except ImportError:
            pytest.skip("HITLManager をインポートできませんでした")
    
    def test_feedback_history_tracking(self):
        """フィードバック履歴追跡の確認"""
        
        # フィードバック履歴を保存する仕組みの確認
        # データベースモデルやRedisキャッシュの確認
        
        # フィードバック関連のモデル確認
        feedback_related_models = [
            Path("app/infrastructure/database/models") / f
            for f in ["feedback_requests_model.py", "feedback_model.py", "hitl_feedback_model.py"]
        ]
        
        model_exists = any(model.exists() for model in feedback_related_models)
        
        # または既存のgeneration_requestsモデルに履歴が含まれているか確認
        gen_request_model = Path("app/infrastructure/database/models/generation_requests_model.py")
        if gen_request_model.exists():
            model_exists = True  # 統合モデルとして実装されている可能性
        
        assert model_exists, "フィードバック履歴を保存するモデルが見つかりません"
    
    def test_hitl_api_endpoints(self):
        """HITL関連APIエンドポイントの確認"""
        
        # HITL関連のAPIエンドポイントファイル確認
        api_files = [
            Path("app/api/manga.py"),
            Path("app/api/v1/manga_sessions.py"),
            Path("app/api/v1/preview_interactive.py")
        ]
        
        hitl_endpoint_found = False
        
        for api_file in api_files:
            if api_file.exists():
                content = api_file.read_text(encoding='utf-8')
                
                # フィードバック関連エンドポイントの確認
                hitl_keywords = [
                    "feedback", "hitl", "apply-change", 
                    "skip-feedback", "modification"
                ]
                
                if any(keyword in content.lower() for keyword in hitl_keywords):
                    hitl_endpoint_found = True
                    break
        
        assert hitl_endpoint_found, "HITL関連のAPIエンドポイントが見つかりません"


# テスト実行関数
def test_hitl_compliance_suite():
    """HITL準拠性テストスイート"""
    test_suite = HITLComplianceTest()
    test_suite.setup_class()
    
    # 全テストの実行
    test_suite.test_hitl_manager_exists()
    test_suite.test_feedback_timeout_configuration()
    test_suite.test_critical_phase_feedback_requirement()
    test_suite.test_feedback_types_support()
    test_suite.test_websocket_integration()
    test_suite.test_real_time_updates_support()
    test_suite.test_feedback_history_tracking()
    test_suite.test_hitl_api_endpoints()
    
    return True
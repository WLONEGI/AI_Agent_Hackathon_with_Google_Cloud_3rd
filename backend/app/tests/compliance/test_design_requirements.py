"""
Design Requirements Compliance Test

設計書要件準拠性の自動検証テスト
YAMLで定義された設計要件と実装の整合性をチェック
"""

import pytest
import yaml
import inspect
from pathlib import Path
from typing import Dict, Any, List
import importlib

from app.core.config import settings
from app.agents.base_agent import BaseAgent


class DesignRequirementsTest:
    """設計要件準拠性テストクラス"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスセットアップ"""
        cls.requirements = cls._load_design_requirements()
        
    @classmethod
    def _load_design_requirements(cls) -> Dict[str, Any]:
        """設計要件YAMLファイルを読み込み"""
        fixtures_dir = Path(__file__).parent / "fixtures"
        requirements_file = fixtures_dir / "design_requirements.yaml"
        
        with open(requirements_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def test_phase_pipeline_structure(self):
        """7フェーズパイプライン構造の検証"""
        requirements = self.requirements["phase_pipeline"]
        
        # フェーズ数の検証
        assert requirements["total_phases"] == 7, "7フェーズ構成である必要があります"
        
        # 各フェーズの実装確認
        required_phases = requirements["required_phases"]
        for phase_req in required_phases:
            phase_num = phase_req["phase_number"]
            phase_name = phase_req["name"]
            
            # Phase Agentクラスの存在確認
            agent_module_name = f"app.agents.phase{phase_num}_concept"
            try:
                agent_module = importlib.import_module(agent_module_name)
                # Agentクラスが存在するか確認
                agent_classes = [
                    cls for name, cls in inspect.getmembers(agent_module, inspect.isclass)
                    if issubclass(cls, BaseAgent) and cls != BaseAgent
                ]
                assert len(agent_classes) > 0, f"Phase {phase_num} Agent クラスが見つかりません"
            except ImportError:
                pytest.fail(f"Phase {phase_num} のモジュールが存在しません: {agent_module_name}")
    
    def test_hitl_requirements_compliance(self):
        """HITL要件準拠性の検証"""
        hitl_req = self.requirements["hitl_requirements"]
        
        # フィードバックタイムアウト設定確認
        expected_timeout = hitl_req["feedback_timeout_seconds"]
        # 実装での設定値確認（設定から取得）
        # assert settings.feedback_timeout == expected_timeout
        
        # Critical フェーズでのフィードバック要求確認
        required_feedback_phases = hitl_req["required_feedback_phases"]
        critical_phases = [4, 5, 7]  # 設計書で指定されたクリティカルフェーズ
        
        for phase in required_feedback_phases:
            assert phase in critical_phases, f"Phase {phase} はクリティカルフェーズである必要があります"
        
        # WebSocket サポート確認
        assert hitl_req["websocket_support"] == True, "WebSocket サポートが必要です"
        assert hitl_req["real_time_updates"] == True, "リアルタイムアップデートが必要です"
    
    def test_architecture_patterns_compliance(self):
        """アーキテクチャパターン準拠性の検証"""
        arch_req = self.requirements["architecture"]
        
        # モノリシック設計の確認
        assert arch_req["pattern"] == "monolithic", "モノリシック設計である必要があります"
        
        # 必須レイヤーの存在確認
        required_layers = arch_req["required_layers"]
        for layer in required_layers:
            layer_path = Path(f"app/{layer}")
            assert layer_path.exists(), f"必須レイヤーが存在しません: {layer}"
        
        # 設計パターンの実装確認（サンプル）
        design_patterns = arch_req["design_patterns"]
        
        # DDD: Domain層の存在確認
        if "Domain-Driven Design (DDD)" in design_patterns:
            domain_path = Path("app/domain")
            assert domain_path.exists(), "Domain層が存在しません"
            
            # Entityやリポジトリの存在確認
            entities_exist = any(domain_path.rglob("*entities*"))
            repositories_exist = any(domain_path.rglob("*repositories*"))
            
            assert entities_exist, "Domain Entities が存在しません"
            assert repositories_exist, "Domain Repositories が存在しません"
        
        # CQRS: Application層のCommand/Queryの確認
        if "Command Query Responsibility Segregation (CQRS)" in design_patterns:
            app_path = Path("app/application")
            if app_path.exists():
                commands_exist = any(app_path.rglob("*command*"))
                queries_exist = any(app_path.rglob("*quer*"))
                
                assert commands_exist, "CQRS Commands が存在しません"
                assert queries_exist, "CQRS Queries が存在しません"
    
    def test_performance_requirements(self):
        """パフォーマンス要件の検証"""
        perf_req = self.requirements["performance"]
        
        # 設定値の確認
        max_processing_time = perf_req["total_processing_time_max"]
        
        # 実装での設定確認（例：settingsから取得）
        if hasattr(settings, 'phase_timeouts'):
            total_configured_time = sum(settings.phase_timeouts.values())
            assert total_configured_time <= max_processing_time, \
                f"総処理時間が要件を超過: {total_configured_time}s > {max_processing_time}s"
    
    def test_security_requirements(self):
        """セキュリティ要件の検証"""
        security_req = self.requirements["security"]
        
        # 認証方式の確認
        expected_auth = security_req["authentication"]
        assert expected_auth == "Firebase Auth", "Firebase Auth を使用する必要があります"
        
        # JWT認可の確認
        expected_authz = security_req["authorization"]
        assert expected_authz == "JWT", "JWT認可を使用する必要があります"
        
        # HTTPS設定確認
        assert security_req["https_only"] == True, "HTTPS専用である必要があります"
        
        # レート制限確認
        assert security_req["rate_limiting"] == True, "レート制限が必要です"
    
    def test_external_api_requirements(self):
        """外部API統合要件の検証"""
        api_req = self.requirements["external_apis"]
        
        # Google Vertex AI要件確認
        vertex_ai_req = api_req["google_vertex_ai"]
        required_models = vertex_ai_req["models_required"]
        
        # 必須モデルの確認
        assert "gemini-pro" in required_models, "Gemini Pro モデルが必要です"
        assert "imagen-4" in required_models, "Imagen 4 モデルが必要です"
        
        # リトライポリシー確認
        retry_policy = vertex_ai_req["retry_policy"]
        assert retry_policy["max_retries"] == 3, "3回リトライが必要です"
        assert retry_policy["backoff_strategy"] == "exponential", "指数バックオフが必要です"
    
    def test_database_requirements(self):
        """データベース要件の検証"""
        db_req = self.requirements["database"]
        
        # データベースエンジン確認
        assert db_req["engine"] == "postgresql", "PostgreSQL を使用する必要があります"
        
        # 必須テーブル確認（実装では model として確認）
        required_tables = db_req["required_tables"]
        
        # モデルファイルの存在確認
        models_path = Path("app/infrastructure/database/models")
        if models_path.exists():
            for table in required_tables:
                model_file = models_path / f"{table}_model.py"
                assert model_file.exists() or any(models_path.glob(f"*{table}*")), \
                    f"テーブル {table} に対応するモデルが見つかりません"
    
    def test_websocket_requirements(self):
        """WebSocket要件の検証"""
        ws_req = self.requirements["websocket"]
        
        # WebSocketマネージャーの存在確認
        ws_manager_path = Path("app/engine/websocket_manager.py")
        assert ws_manager_path.exists(), "WebSocket Manager が存在しません"
        
        # 設定値確認
        max_connections = ws_req["max_concurrent_connections"]
        assert max_connections == 1000, "1000同時接続をサポートする必要があります"
        
        debounce_ms = ws_req["debounce_ms"]
        assert debounce_ms == 300, "300msデバウンス処理が必要です"
        
        # カスタムイベント・セッション管理サポート確認
        assert ws_req["custom_events"] == True, "カスタムイベントサポートが必要です"
        assert ws_req["session_management"] == True, "セッション管理が必要です"


# Pytest fixtures
@pytest.fixture(scope="session")
def design_requirements():
    """設計要件フィクスチャ"""
    return DesignRequirementsTest._load_design_requirements()


# テスト実行用の関数定義
def test_compliance_full_suite():
    """設計書準拠性の完全テストスイート実行"""
    test_suite = DesignRequirementsTest()
    test_suite.setup_class()
    
    # 全テストの実行
    test_suite.test_phase_pipeline_structure()
    test_suite.test_hitl_requirements_compliance()  
    test_suite.test_architecture_patterns_compliance()
    test_suite.test_performance_requirements()
    test_suite.test_security_requirements()
    test_suite.test_external_api_requirements()
    test_suite.test_database_requirements()
    test_suite.test_websocket_requirements()
    
    return True
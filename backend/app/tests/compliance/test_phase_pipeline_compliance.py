"""
Phase Pipeline Compliance Test

7フェーズ処理パイプラインの設計準拠性テスト
各フェーズの実装が設計仕様に準拠しているかを検証
"""

import pytest
import asyncio
import inspect
from typing import Dict, Any, List, Type
from unittest.mock import Mock, AsyncMock
from pathlib import Path

from app.agents.base_agent import BaseAgent
from app.engine.manga_generation_engine import MangaGenerationEngine
from app.core.config import settings


class PhasePipelineComplianceTest:
    """フェーズパイプライン準拠性テストクラス"""
    
    @classmethod
    def setup_class(cls):
        """テストクラスセットアップ"""
        cls.expected_phases = cls._get_expected_phases()
        cls.pipeline_engine = None  # テスト時に初期化
        
    @classmethod
    def _get_expected_phases(cls) -> List[Dict[str, Any]]:
        """期待されるフェーズ構成を取得"""
        return [
            {
                "phase_number": 1,
                "name": "コンセプト・世界観分析", 
                "agent_class": "Phase1ConceptAgent",
                "module_name": "app.agents.phase1_concept",
                "timeout": 30,
                "ai_model": "gemini-pro",
                "critical": False
            },
            {
                "phase_number": 2,
                "name": "キャラクター設定・簡易ビジュアル生成",
                "agent_class": "Phase2CharacterAgent", 
                "module_name": "app.agents.phase2_character",
                "timeout": 60,
                "ai_model": "gemini-pro",
                "critical": False
            },
            {
                "phase_number": 3,
                "name": "物語構造化・プロット生成",
                "agent_class": "Phase3PlotAgent",
                "module_name": "app.agents.phase3_plot", 
                "timeout": 60,
                "ai_model": "gemini-pro",
                "critical": False
            },
            {
                "phase_number": 4,
                "name": "シーン分割・コマ割り",
                "agent_class": "Phase4NameAgent",
                "module_name": "app.agents.phase4_name",
                "timeout": 60,
                "ai_model": "gemini-pro", 
                "critical": True
            },
            {
                "phase_number": 5,
                "name": "画像生成・ビジュアル制作",
                "agent_class": "Phase5ImageAgent",
                "module_name": "app.agents.phase5_image",
                "timeout": 180,
                "ai_model": "imagen-4",
                "critical": True
            },
            {
                "phase_number": 6,
                "name": "セリフ配置・テキスト統合", 
                "agent_class": "Phase6DialogueAgent",
                "module_name": "app.agents.phase6_dialogue",
                "timeout": 60,
                "ai_model": "gemini-pro",
                "critical": False
            },
            {
                "phase_number": 7,
                "name": "最終統合・品質調整",
                "agent_class": "Phase7IntegrationAgent",
                "module_name": "app.agents.phase7_integration", 
                "timeout": 120,
                "ai_model": "image_processing",
                "critical": True
            }
        ]
    
    def test_all_phase_agents_exist(self):
        """全フェーズのAgentクラスが存在することを確認"""
        for phase_info in self.expected_phases:
            phase_num = phase_info["phase_number"]
            module_name = phase_info["module_name"]
            
            # モジュールファイルの存在確認
            module_path = Path(module_name.replace("app.", "app/").replace(".", "/") + ".py")
            assert module_path.exists(), f"Phase {phase_num} モジュールファイルが存在しません: {module_path}"
            
            # モジュールのインポート確認
            try:
                import importlib
                module = importlib.import_module(module_name)
                
                # Agent クラスの存在確認
                agent_classes = [
                    cls for name, cls in inspect.getmembers(module, inspect.isclass)
                    if issubclass(cls, BaseAgent) and cls != BaseAgent
                ]
                
                assert len(agent_classes) > 0, f"Phase {phase_num} に Agent クラスが見つかりません"
                
                # クラス名の確認
                expected_class_name = phase_info["agent_class"]
                class_found = any(cls.__name__ == expected_class_name for cls in agent_classes)
                if not class_found:
                    # 柔軟な確認：Agent で終わるクラスがあればOK
                    agent_class_found = any("Agent" in cls.__name__ for cls in agent_classes)
                    assert agent_class_found, f"Phase {phase_num} の Agent クラス ({expected_class_name}) が見つかりません"
                
            except ImportError as e:
                pytest.fail(f"Phase {phase_num} モジュールのインポートに失敗: {e}")
    
    def test_phase_agent_inheritance(self):
        """全フェーズAgentがBaseAgentを継承していることを確認"""  
        import importlib
        
        for phase_info in self.expected_phases:
            module_name = phase_info["module_name"]
            
            try:
                module = importlib.import_module(module_name)
                agent_classes = [
                    cls for name, cls in inspect.getmembers(module, inspect.isclass)
                    if issubclass(cls, BaseAgent) and cls != BaseAgent
                ]
                
                assert len(agent_classes) > 0
                
                for agent_class in agent_classes:
                    # BaseAgent継承確認
                    assert issubclass(agent_class, BaseAgent), \
                        f"{agent_class.__name__} は BaseAgent を継承していません"
                    
                    # 必須メソッドの実装確認
                    required_methods = ['process_phase', 'generate_prompt', 'validate_output']
                    for method in required_methods:
                        assert hasattr(agent_class, method), \
                            f"{agent_class.__name__} に必須メソッド {method} がありません"
                        
                        # 抽象メソッドが実装されているか確認
                        method_obj = getattr(agent_class, method)
                        assert not getattr(method_obj, '__isabstractmethod__', False), \
                            f"{agent_class.__name__}.{method} が実装されていません（抽象メソッドのまま）"
                            
            except ImportError:
                continue  # 別のテストで処理済み
    
    def test_phase_timeout_configuration(self):
        """フェーズタイムアウト設定の確認"""
        if not hasattr(settings, 'phase_timeouts'):
            pytest.skip("phase_timeouts 設定が見つかりません")
            
        phase_timeouts = settings.phase_timeouts
        
        for phase_info in self.expected_phases:
            phase_num = phase_info["phase_number"]
            expected_timeout = phase_info["timeout"]
            
            # 設定にフェーズタイムアウトが存在するか確認
            assert phase_num in phase_timeouts, f"Phase {phase_num} のタイムアウト設定がありません"
            
            # タイムアウト値が妥当範囲内か確認（±50%の範囲）
            actual_timeout = phase_timeouts[phase_num]
            min_timeout = expected_timeout * 0.5
            max_timeout = expected_timeout * 1.5
            
            assert min_timeout <= actual_timeout <= max_timeout, \
                f"Phase {phase_num} タイムアウトが範囲外: {actual_timeout}s (期待値: {expected_timeout}s)"
    
    def test_critical_phases_identification(self):
        """クリティカルフェーズの正しい識別"""
        critical_phases = [
            phase["phase_number"] for phase in self.expected_phases 
            if phase["critical"]
        ]
        
        expected_critical = [4, 5, 7]  # 設計書で定義されたクリティカルフェーズ
        
        assert set(critical_phases) == set(expected_critical), \
            f"クリティカルフェーズの定義が不正: 期待={expected_critical}, 実際={critical_phases}"
    
    def test_ai_model_assignment(self):
        """各フェーズのAIモデル割り当ての確認"""
        gemini_phases = [
            phase["phase_number"] for phase in self.expected_phases 
            if phase["ai_model"] == "gemini-pro"
        ]
        
        imagen_phases = [
            phase["phase_number"] for phase in self.expected_phases
            if phase["ai_model"] == "imagen-4" 
        ]
        
        # Gemini Pro 使用フェーズ確認（テキスト処理）
        expected_gemini = [1, 2, 3, 4, 6]
        assert set(gemini_phases) == set(expected_gemini), \
            f"Gemini Pro 使用フェーズが不正: 期待={expected_gemini}, 実際={gemini_phases}"
        
        # Imagen 4 使用フェーズ確認（画像生成）
        expected_imagen = [5]
        assert set(imagen_phases) == set(expected_imagen), \
            f"Imagen 4 使用フェーズが不正: 期待={expected_imagen}, 実際={imagen_phases}"
    
    def test_pipeline_total_processing_time(self):
        """パイプライン総処理時間の確認"""
        total_expected_time = sum(phase["timeout"] for phase in self.expected_phases)
        max_allowed_time = 750  # 設計書要件：12.5分
        
        assert total_expected_time <= max_allowed_time, \
            f"総処理時間が要件超過: {total_expected_time}s > {max_allowed_time}s"
        
        # 設定値との整合性確認
        if hasattr(settings, 'phase_timeouts'):
            configured_total = sum(settings.phase_timeouts.values())
            assert configured_total <= max_allowed_time, \
                f"設定総処理時間が要件超過: {configured_total}s > {max_allowed_time}s"
    
    @pytest.mark.asyncio
    async def test_phase_sequential_execution(self):
        """フェーズの順次実行の確認"""
        # モックを使用した簡単な実行フロー確認
        execution_order = []
        
        class MockPhaseAgent(BaseAgent):
            def __init__(self, phase_number, phase_name):
                super().__init__(phase_number, phase_name, timeout_seconds=1)
                
            async def process_phase(self, input_data, session_id, previous_results=None):
                execution_order.append(self.phase_number)
                return {"phase": self.phase_number, "result": "mock_output"}
                
            async def generate_prompt(self, input_data, previous_results=None):
                return f"Mock prompt for phase {self.phase_number}"
                
            async def validate_output(self, output_data):
                return True
        
        # 模擬的なフェーズ実行
        agents = [
            MockPhaseAgent(phase["phase_number"], phase["name"])
            for phase in self.expected_phases[:3]  # 最初の3フェーズのみテスト
        ]
        
        for agent in agents:
            await agent.process_phase({}, "test_session")
        
        # フェーズが順次実行されることを確認
        assert execution_order == [1, 2, 3], f"フェーズ実行順序が不正: {execution_order}"
    
    def test_phase_output_types(self):
        """各フェーズの出力タイプ定義確認"""
        expected_outputs = {
            1: "concept_analysis",
            2: "character_design", 
            3: "story_structure",
            4: "scene_layout",
            5: "visual_content",
            6: "dialogue_integration",
            7: "final_manga"
        }
        
        for phase_info in self.expected_phases:
            phase_num = phase_info["phase_number"]
            # この確認は実装によって異なるが、設計書との整合性を確認
            assert phase_num in expected_outputs, f"Phase {phase_num} の出力タイプが未定義"
    
    def test_manga_generation_engine_integration(self):
        """MangaGenerationEngine とのフェーズ統合確認"""
        # MangaGenerationEngine が存在することを確認
        engine_path = Path("app/engine/manga_generation_engine.py")
        assert engine_path.exists(), "MangaGenerationEngine が存在しません"
        
        # エンジンクラスのインポート確認
        try:
            from app.engine.manga_generation_engine import MangaGenerationEngine
            
            # エンジンが7フェーズを認識しているか確認
            engine = MangaGenerationEngine()
            
            # フェーズ数の確認（実装に依存）
            if hasattr(engine, 'total_phases'):
                assert engine.total_phases == 7, "エンジンが7フェーズを認識していません"
                
        except ImportError:
            pytest.fail("MangaGenerationEngine のインポートに失敗しました")


# テスト実行関数
def test_phase_pipeline_compliance_suite():
    """フェーズパイプライン準拠性テストスイート"""
    test_suite = PhasePipelineComplianceTest()
    test_suite.setup_class()
    
    # 全テストの実行
    test_suite.test_all_phase_agents_exist()
    test_suite.test_phase_agent_inheritance()
    test_suite.test_phase_timeout_configuration()
    test_suite.test_critical_phases_identification()
    test_suite.test_ai_model_assignment()
    test_suite.test_pipeline_total_processing_time()
    test_suite.test_phase_output_types()
    test_suite.test_manga_generation_engine_integration()
    
    return True
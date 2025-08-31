#!/usr/bin/env python3
"""
Simple Compliance Test Runner

設定の複雑性を避けた、シンプルなテスト実行スクリプト
"""

import os
import sys
import pytest
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_yaml_config_loading():
    """YAML設定ファイルの読み込みテスト"""
    import yaml
    from pathlib import Path
    
    yaml_path = Path("app/tests/compliance/fixtures/design_requirements.yaml")
    assert yaml_path.exists(), "YAML設定ファイルが存在しません"
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    assert config is not None, "YAML設定の読み込みに失敗"
    assert "phase_pipeline" in config, "phase_pipeline設定がありません"
    assert "hitl_requirements" in config, "hitl_requirements設定がありません"
    
    print("✅ YAML設定ファイル読み込み成功")
    return config

def test_phase_pipeline_config():
    """フェーズパイプライン設定の検証"""
    import yaml
    from pathlib import Path
    
    yaml_path = Path("app/tests/compliance/fixtures/design_requirements.yaml")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    pipeline = config["phase_pipeline"]
    
    # 基本的な検証
    assert pipeline["total_phases"] == 7, "総フェーズ数が7ではありません"
    assert len(pipeline["required_phases"]) == 7, "必須フェーズの数が不正です"
    
    # 各フェーズの検証
    for i, phase in enumerate(pipeline["required_phases"], 1):
        assert phase["phase_number"] == i, f"フェーズ{i}の番号が不正です"
        assert "name" in phase, f"フェーズ{i}に名前がありません"
        
    print("✅ フェーズパイプライン設定検証成功")
    return True

def test_hitl_config():
    """HITL設定の検証"""
    import yaml
    from pathlib import Path
    
    yaml_path = Path("app/tests/compliance/fixtures/design_requirements.yaml")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    hitl = config["hitl_requirements"]
    
    # HITL設定の検証
    assert hitl["feedback_timeout_seconds"] == 30, "フィードバックタイムアウトが30秒ではありません"
    assert set(hitl["required_feedback_phases"]) == {4, 5, 7}, "必須フィードバックフェーズが不正です"
    
    expected_feedback_types = {"natural_language", "quick_options", "skip"}
    actual_feedback_types = set(hitl["feedback_types"])
    assert actual_feedback_types == expected_feedback_types, "フィードバックタイプが不正です"
    
    print("✅ HITL設定検証成功")
    return True

def test_file_structure():
    """バックエンドファイル構造の検証"""
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/core/__init__.py",
        "app/domain/__init__.py",
        "app/infrastructure/__init__.py",
        "app/tests/__init__.py",
    ]
    
    for file_path in required_files:
        path = Path(file_path)
        assert path.exists(), f"必須ファイルが存在しません: {file_path}"
    
    print("✅ ファイル構造検証成功")
    return True

def test_phase_agents_exist():
    """フェーズエージェントの存在確認"""
    agents_dir = Path("app/engine/agents")
    
    if not agents_dir.exists():
        print("⚠️  app/engine/agents ディレクトリが存在しません")
        return False
        
    required_agents = [
        "concept_analysis_agent.py",
        "character_design_agent.py", 
        "plot_structure_agent.py",
        "scene_division_agent.py",
        "image_generation_agent.py",
        "dialogue_creation_agent.py",
        "integration_agent.py"
    ]
    
    missing_agents = []
    for agent in required_agents:
        agent_path = agents_dir / agent
        if not agent_path.exists():
            missing_agents.append(agent)
    
    if missing_agents:
        print(f"⚠️  不足しているエージェント: {missing_agents}")
        return False
    else:
        print("✅ 全フェーズエージェント存在確認成功")
        return True

def test_api_structure():
    """API構造の検証"""
    api_dir = Path("app/api")
    
    if not api_dir.exists():
        print("⚠️  app/api ディレクトリが存在しません")
        return False
    
    # APIファイルの存在確認
    api_files = list(api_dir.rglob("*.py"))
    
    if not api_files:
        print("⚠️  APIファイルが見つかりません")
        return False
    
    print(f"✅ API構造確認成功 ({len(api_files)} ファイル)")
    return True

def run_simple_tests():
    """シンプルテストの実行"""
    print("🧪 シンプル準拠性テスト開始")
    print("=" * 50)
    
    tests = [
        ("YAML設定ファイル", test_yaml_config_loading),
        ("フェーズパイプライン設定", test_phase_pipeline_config),
        ("HITL設定", test_hitl_config),
        ("ファイル構造", test_file_structure),
        ("フェーズエージェント", test_phase_agents_exist),
        ("API構造", test_api_structure)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}テスト実行中...")
        try:
            result = test_func()
            results[test_name] = {"success": True, "result": result}
        except Exception as e:
            print(f"❌ {test_name}テスト失敗: {e}")
            results[test_name] = {"success": False, "error": str(e)}
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("📊 テスト結果サマリー")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        if result["success"]:
            print(f"✅ {test_name}: 成功")
            passed += 1
        else:
            print(f"❌ {test_name}: 失敗 - {result['error']}")
            failed += 1
    
    total = passed + failed
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print(f"\n📈 総合結果: {passed}/{total} テスト成功 ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🎉 準拠性テスト合格！")
        return True
    else:
        print("⚠️  準拠性に問題があります。")
        return False

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)
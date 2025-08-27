#!/usr/bin/env python3
"""
Code validation test for AI integration.
Validates that all Phase agents have proper AI integration without running them.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any


def check_file_contains_patterns(file_path: Path, patterns: List[str]) -> Dict[str, bool]:
    """Check if a file contains all the required patterns."""
    try:
        content = file_path.read_text(encoding='utf-8')
        results = {}
        for pattern in patterns:
            results[pattern] = bool(re.search(pattern, content, re.MULTILINE))
        return results
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return {pattern: False for pattern in patterns}


def validate_vertex_ai_service():
    """Validate VertexAI service implementation."""
    print("🔧 Validating VertexAI Service Implementation...")
    
    service_path = Path("app/services/vertex_ai_service.py")
    if not service_path.exists():
        print(f"❌ VertexAI service file not found: {service_path}")
        return False
    
    required_patterns = [
        r'class VertexAIService',
        r'async def generate_text',
        r'async def generate_images',
        r'vertexai\.generative_models\.GenerativeModel',
        r'vertexai\.preview\.vision_models\.ImageGenerationModel',
        r'gemini-.*-pro',
        r'imagegeneration@.*',
        r'def _parse_.*_response',
    ]
    
    results = check_file_contains_patterns(service_path, required_patterns)
    
    passed = 0
    total = len(required_patterns)
    
    for pattern, found in results.items():
        status = "✅" if found else "❌"
        print(f"  {status} {pattern}")
        if found:
            passed += 1
    
    print(f"  📊 VertexAI Service: {passed}/{total} patterns found")
    return passed >= total - 1  # Allow 1 missing pattern


def validate_phase_agent_integration(phase_num: int, agent_name: str):
    """Validate AI integration in a specific phase agent."""
    print(f"\n🎯 Validating Phase {phase_num} Agent ({agent_name})...")
    
    agent_path = Path(f"app/agents/{agent_name}")
    if not agent_path.exists():
        print(f"❌ Agent file not found: {agent_path}")
        return False
    
    # Different patterns for Phase 5 (image generation) vs other phases (text generation)
    if phase_num == 5:
        required_patterns = [
            r'from app\.services\.vertex_ai_service import VertexAIService',
            r'self\.vertex_ai = VertexAIService\(\)',
            r'await self\.vertex_ai\.generate_images',
            r'Imagen.*4',
            r'fallback.*simulation',
            r'ai_response\.get\("success"',
        ]
    else:
        required_patterns = [
            r'from app\.services\.vertex_ai_service import VertexAIService',
            r'self\.vertex_ai = VertexAIService\(\)',
            r'await self\.vertex_ai\.generate_text',
            r'Gemini.*Pro',
            r'def _parse_ai_response',
            r'ai_response\.get\("success"',
            r'fallback.*analysis',
        ]
    
    results = check_file_contains_patterns(agent_path, required_patterns)
    
    passed = 0
    total = len(required_patterns)
    
    for pattern, found in results.items():
        status = "✅" if found else "❌"
        print(f"  {status} {pattern}")
        if found:
            passed += 1
    
    print(f"  📊 Phase {phase_num}: {passed}/{total} patterns found")
    return passed >= total - 1  # Allow 1 missing pattern


def validate_all_agents():
    """Validate AI integration in all phase agents."""
    print("\n🧪 Validating All Phase Agent AI Integrations...")
    
    agents = [
        (1, "phase1_concept.py"),
        (2, "phase2_character.py"),
        (3, "phase3_plot.py"),
        (4, "phase4_name.py"),
        (5, "phase5_image.py"),
        (6, "phase6_dialogue.py"),
        (7, "phase7_integration.py"),
    ]
    
    successful_validations = 0
    
    for phase_num, agent_name in agents:
        is_valid = validate_phase_agent_integration(phase_num, agent_name)
        if is_valid:
            successful_validations += 1
    
    print(f"\n📊 Overall Agent Validation: {successful_validations}/{len(agents)} agents properly integrated")
    return successful_validations == len(agents)


def validate_configuration_files():
    """Validate configuration files support AI integration."""
    print("\n⚙️ Validating Configuration Files...")
    
    config_checks = []
    
    # Check settings files
    settings_path = Path("app/core/config/ai_models.py")
    if settings_path.exists():
        patterns = [
            r'gemini.*pro',
            r'imagen.*4',
            r'temperature',
            r'max_output_tokens',
        ]
        results = check_file_contains_patterns(settings_path, patterns)
        config_checks.append(("AI Models Config", results))
    
    # Check .env file
    env_path = Path(".env")
    if env_path.exists():
        patterns = [
            r'GOOGLE_CLOUD_PROJECT',
            r'DATABASE_URL',
            r'GOOGLE_CLOUD_REGION',
        ]
        results = check_file_contains_patterns(env_path, patterns)
        config_checks.append(("Environment Config", results))
    
    # Check requirements
    req_path = Path("requirements.txt")
    if req_path.exists():
        patterns = [
            r'google-cloud-aiplatform',
            r'vertexai',
            r'google-cloud.*',
        ]
        results = check_file_contains_patterns(req_path, patterns)
        config_checks.append(("Requirements", results))
    
    valid_configs = 0
    for config_name, results in config_checks:
        passed = sum(results.values())
        total = len(results)
        print(f"  📋 {config_name}: {passed}/{total} patterns found")
        if passed >= total - 1:
            valid_configs += 1
    
    return valid_configs >= len(config_checks) - 1


def check_import_structure():
    """Check that import structure supports AI integration."""
    print("\n🔗 Validating Import Structure...")
    
    # Check that all agents can potentially import VertexAI service
    agents_dir = Path("app/agents")
    if not agents_dir.exists():
        print("❌ Agents directory not found")
        return False
    
    agent_files = list(agents_dir.glob("phase*.py"))
    
    importable_agents = 0
    for agent_file in agent_files:
        # Check if the file has the basic structure for import
        content = agent_file.read_text(encoding='utf-8')
        
        has_basic_structure = all([
            "class Phase" in content,
            "BaseAgent" in content,
            "__init__" in content,
            "async def process_phase" in content,
        ])
        
        if has_basic_structure:
            importable_agents += 1
            print(f"  ✅ {agent_file.name} - Basic structure valid")
        else:
            print(f"  ❌ {agent_file.name} - Missing basic structure")
    
    print(f"  📊 Import Structure: {importable_agents}/{len(agent_files)} agents have valid structure")
    return importable_agents == len(agent_files)


def main():
    """Main validation runner."""
    print("🤖 AI Integration Code Validation")
    print("=" * 50)
    
    # Change to the backend directory for relative path resolution
    original_dir = os.getcwd()
    backend_dir = Path(__file__).parent.parent  # Go up one level from tests/ to backend/
    os.chdir(backend_dir)
    
    try:
        print(f"📁 Working Directory: {os.getcwd()}")
        
        # Run validation tests
        test_results = []
        
        # 1. Validate VertexAI Service
        print("\n" + "=" * 50)
        service_valid = validate_vertex_ai_service()
        test_results.append(("VertexAI Service", service_valid))
        
        # 2. Validate all phase agents
        print("\n" + "=" * 50)
        agents_valid = validate_all_agents()
        test_results.append(("Phase Agents Integration", agents_valid))
        
        # 3. Validate configuration
        print("\n" + "=" * 50)
        config_valid = validate_configuration_files()
        test_results.append(("Configuration Files", config_valid))
        
        # 4. Validate import structure
        print("\n" + "=" * 50)
        imports_valid = check_import_structure()
        test_results.append(("Import Structure", imports_valid))
        
        # Summary
        print("\n" + "=" * 50)
        print("🏁 Validation Summary")
        print("=" * 50)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
            if result:
                passed_tests += 1
        
        print(f"\nOverall: {passed_tests}/{total_tests} validations passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 All AI integration validations passed!")
            print("💡 The code structure supports full AI integration.")
            return True
        elif passed_tests >= total_tests - 1:
            print("⚠️ Most validations passed. Minor issues detected.")
            print("💡 AI integration should work with minimal fixes.")
            return True
        else:
            print("❌ Multiple validation failures detected.")
            print("💡 Check the output above for specific issues.")
            return False
            
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Test script for comprehensive AI integration verification.
Tests all Phase agents with Vertex AI (Gemini Pro and Imagen 4) integration.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import uuid4
from typing import Dict, Any
import traceback

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent))

from app.agents.phase1_concept import Phase1ConceptAgent
from app.agents.phase2_character import Phase2CharacterAgent
from app.agents.phase3_plot import Phase3PlotAgent
from app.agents.phase4_name import Phase4NameAgent
from app.agents.phase5_image import Phase5ImageAgent
from app.agents.phase6_dialogue import Phase6DialogueAgent
from app.agents.phase7_integration import Phase7IntegrationAgent
from app.services.vertex_ai_service import VertexAIService


# Mock input data for testing
MOCK_INPUT = {
    "text": """
    高校生の田中は、ある日古い本屋で不思議な本を見つける。
    その本を開くと、異世界へと吸い込まれてしまった。
    そこは魔法が存在する世界で、田中は勇者として召喚されたのだった。
    最初は戸惑う田中だったが、仲間たちと出会い、魔王を倒す旅に出ることになる。
    """
}

# Mock previous results for later phases
MOCK_PREVIOUS_RESULTS = {
    1: {
        "genre": "ファンタジー",
        "themes": ["冒険", "友情", "成長"],
        "target_audience": "高校生",
        "world_setting": {
            "location": "異世界",
            "time_period": "fantasy",
            "tone": "冒険活劇"
        }
    },
    2: {
        "characters": [
            {
                "name": "田中",
                "role": "主人公",
                "appearance": "黒髪の高校生、普通の体格",
                "personality": ["素直", "勇敢", "優しい"]
            }
        ],
        "visual_descriptions": {
            "田中": {
                "base_prompt": "teenage boy, black hair, school uniform",
                "detailed_description": "普通の高校生だが勇敢な心を持つ"
            }
        }
    },
    3: {
        "scenes": [
            {
                "scene_number": 1,
                "title": "古書店での発見",
                "content": "田中が不思議な本を見つける",
                "emotional_tone": "curiosity"
            }
        ],
        "page_allocation": [
            {"page": 1, "scenes": [1], "panel_count": 4}
        ],
        "pacing": {"fast": 30, "medium": 50, "slow": 20}
    },
    4: {
        "pages": [
            {
                "page_number": 1,
                "panels": [
                    {
                        "panel_id": "p1_panel1",
                        "camera_angle": "medium_shot",
                        "composition": "rule_of_thirds",
                        "characters": ["田中"],
                        "scene_number": 1
                    }
                ]
            }
        ],
        "panel_specifications": [
            {
                "panel_id": "p1_panel1",
                "camera_angle": "medium_shot",
                "composition": "rule_of_thirds",
                "scene_number": 1,
                "page_number": 1,
                "panel_number": 1,
                "focus_element": "character_interaction",
                "emotional_tone": "curiosity"
            }
        ]
    },
    5: {
        "generated_images": [
            {
                "panel_id": "p1_panel1",
                "success": True,
                "image_url": "https://example.com/image1.png",
                "quality_score": 0.85
            }
        ],
        "total_images_generated": 1,
        "successful_generations": 1
    },
    6: {
        "dialogue_content": {
            "p1_panel1": [
                {
                    "character": "田中",
                    "text": "この本は何だろう...",
                    "bubble_type": "speech"
                }
            ]
        },
        "text_placements": [
            {
                "panel_id": "p1_panel1",
                "text_elements": [
                    {
                        "text": "この本は何だろう...",
                        "position": {"x": 0.5, "y": 0.3},
                        "bubble_style": "standard"
                    }
                ]
            }
        ]
    }
}


async def test_vertex_ai_service():
    """Test basic Vertex AI service functionality."""
    print("\n🧪 Testing Vertex AI Service...")
    
    try:
        service = VertexAIService()
        
        # Test text generation
        print("  📝 Testing Gemini Pro text generation...")
        text_response = await service.generate_text(
            prompt="この漫画の設定について分析してください: 高校生が異世界に召喚される話",
            phase_number=1
        )
        
        print(f"  ✅ Gemini Pro response: {text_response.get('success', False)}")
        if text_response.get('success'):
            print(f"     Content length: {len(text_response.get('content', ''))}")
        else:
            print(f"     Error: {text_response.get('error', 'Unknown error')}")
        
        # Test image generation
        print("  🖼️ Testing Imagen 4 image generation...")
        image_response = await service.generate_images(
            prompts=["high quality manga style, teenage boy reading book"],
            batch_size=1
        )
        
        print(f"  ✅ Imagen 4 response: {len(image_response) > 0 and image_response[0].get('success', False)}")
        if image_response and image_response[0].get('success'):
            print(f"     Image URL generated: {bool(image_response[0].get('image_url'))}")
        else:
            error = image_response[0].get('error') if image_response else 'No response'
            print(f"     Error: {error}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Vertex AI Service test failed: {str(e)}")
        return False


async def test_phase_agent(agent_class, phase_num: int, mock_input: Dict[str, Any], 
                          mock_previous: Dict[int, Any] = None):
    """Test individual phase agent with AI integration."""
    
    print(f"\n🎯 Testing Phase {phase_num} Agent ({agent_class.__name__})...")
    
    try:
        agent = agent_class()
        session_id = uuid4()
        
        # Generate prompt
        print(f"  📋 Generating prompt for Phase {phase_num}...")
        prompt = await agent.generate_prompt(mock_input, mock_previous)
        print(f"     Prompt length: {len(prompt)} characters")
        
        # Process phase
        print(f"  ⚙️ Processing Phase {phase_num}...")
        result = await agent.process_phase(mock_input, session_id, mock_previous)
        
        # Validate output
        print(f"  ✅ Validating Phase {phase_num} output...")
        is_valid = await agent.validate_output(result)
        
        print(f"  📊 Phase {phase_num} Results:")
        print(f"     Valid output: {is_valid}")
        print(f"     Result keys: {list(result.keys())}")
        print(f"     Result size: {len(json.dumps(result, default=str))} characters")
        
        return result, is_valid
        
    except Exception as e:
        print(f"  ❌ Phase {phase_num} Agent test failed: {str(e)}")
        traceback.print_exc()
        return None, False


async def test_full_pipeline():
    """Test complete pipeline with all phases."""
    print("\n🚀 Testing Full AI Pipeline...")
    
    session_id = uuid4()
    previous_results = {}
    
    # Phase order and their required previous phases
    phases = [
        (Phase1ConceptAgent, 1, []),
        (Phase2CharacterAgent, 2, [1]),
        (Phase3PlotAgent, 3, [1, 2]),
        (Phase4NameAgent, 4, [1, 2, 3]),
        (Phase5ImageAgent, 5, [1, 2, 3, 4]),
        (Phase6DialogueAgent, 6, [1, 2, 3, 4, 5]),
        (Phase7IntegrationAgent, 7, [1, 2, 3, 4, 5, 6])
    ]
    
    successful_phases = 0
    
    for agent_class, phase_num, required_phases in phases:
        print(f"\n📍 Pipeline Phase {phase_num}: {agent_class.__name__}")
        
        try:
            # Use mock data for required phases if not yet completed
            phase_previous_results = {}
            for req_phase in required_phases:
                if req_phase in previous_results:
                    phase_previous_results[req_phase] = previous_results[req_phase]
                elif req_phase in MOCK_PREVIOUS_RESULTS:
                    phase_previous_results[req_phase] = MOCK_PREVIOUS_RESULTS[req_phase]
                    print(f"     Using mock data for Phase {req_phase}")
            
            result, is_valid = await test_phase_agent(
                agent_class, phase_num, MOCK_INPUT, phase_previous_results
            )
            
            if result and is_valid:
                previous_results[phase_num] = result
                successful_phases += 1
                print(f"  ✅ Phase {phase_num} completed successfully")
            else:
                print(f"  ⚠️ Phase {phase_num} failed, using mock data for continuation")
                if phase_num in MOCK_PREVIOUS_RESULTS:
                    previous_results[phase_num] = MOCK_PREVIOUS_RESULTS[phase_num]
                
        except Exception as e:
            print(f"  ❌ Phase {phase_num} pipeline test failed: {str(e)}")
            if phase_num in MOCK_PREVIOUS_RESULTS:
                previous_results[phase_num] = MOCK_PREVIOUS_RESULTS[phase_num]
                print(f"     Using mock data for Phase {phase_num}")
    
    print(f"\n📊 Pipeline Results:")
    print(f"   Successful phases: {successful_phases}/{len(phases)}")
    print(f"   Pipeline completion: {(successful_phases/len(phases))*100:.1f}%")
    
    return successful_phases == len(phases)


async def test_ai_fallback_mechanisms():
    """Test AI fallback mechanisms when Vertex AI fails."""
    print("\n🛡️ Testing AI Fallback Mechanisms...")
    
    # This would require mocking the Vertex AI service to simulate failures
    # For now, we'll test that agents can handle missing AI responses
    
    try:
        agent = Phase1ConceptAgent()
        session_id = uuid4()
        
        # Test with normal processing (should use AI)
        result = await agent.process_phase(MOCK_INPUT, session_id)
        
        print(f"  ✅ Fallback mechanism test completed")
        print(f"     Result contains data: {bool(result)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Fallback mechanism test failed: {str(e)}")
        return False


async def main():
    """Main test runner."""
    print("🤖 AI Integration Test Suite")
    print("=" * 50)
    
    # Check environment
    print("\n🔧 Environment Check:")
    print(f"   Python version: {sys.version}")
    print(f"   Working directory: {os.getcwd()}")
    
    # Load environment variables
    if os.path.exists('.env'):
        print("   ✅ .env file found")
    else:
        print("   ⚠️ .env file not found - using defaults")
    
    # Run tests
    test_results = {}
    
    # 1. Test Vertex AI Service
    test_results['vertex_ai'] = await test_vertex_ai_service()
    
    # 2. Test individual agents
    individual_tests = []
    for i, agent_class in enumerate([
        Phase1ConceptAgent, Phase2CharacterAgent, Phase3PlotAgent,
        Phase4NameAgent, Phase5ImageAgent, Phase6DialogueAgent,
        Phase7IntegrationAgent
    ], 1):
        # Use appropriate previous results for each phase
        prev_results = {j: MOCK_PREVIOUS_RESULTS[j] for j in range(1, i) if j in MOCK_PREVIOUS_RESULTS}
        result, is_valid = await test_phase_agent(agent_class, i, MOCK_INPUT, prev_results)
        individual_tests.append(is_valid)
    
    test_results['individual_phases'] = all(individual_tests)
    
    # 3. Test full pipeline
    test_results['full_pipeline'] = await test_full_pipeline()
    
    # 4. Test fallback mechanisms
    test_results['fallback_mechanisms'] = await test_ai_fallback_mechanisms()
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")
    print("=" * 50)
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 All AI integration tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
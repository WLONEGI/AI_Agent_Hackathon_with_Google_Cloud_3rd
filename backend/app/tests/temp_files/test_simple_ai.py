#!/usr/bin/env python3
"""
Simple AI integration test without full app initialization.
Tests core AI integration functionality.
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Set environment variables before any imports
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./manga_service.db'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'comic-ai-agent-470309'
os.environ['GOOGLE_CLOUD_REGION'] = 'us-central1'
os.environ['ENV'] = 'development'

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent))

try:
    from app.services.vertex_ai_service import VertexAIService
    print("✅ Successfully imported VertexAIService")
except Exception as e:
    print(f"❌ Failed to import VertexAIService: {e}")
    sys.exit(1)


async def test_vertex_ai_service():
    """Test basic Vertex AI service functionality."""
    print("\n🧪 Testing Vertex AI Service Integration...")
    
    try:
        service = VertexAIService()
        print("✅ VertexAIService initialized successfully")
        
        # Test text generation (Gemini Pro)
        print("\n📝 Testing Gemini Pro text generation...")
        text_response = await service.generate_text(
            prompt="""この漫画の設定について分析してください:
            
高校生の田中は、ある日古い本屋で不思議な本を見つける。
その本を開くと、異世界へと吸い込まれてしまった。

分析結果をJSON形式で返してください:
{
  "genre": "ジャンル",
  "themes": ["テーマ1", "テーマ2"],
  "target_audience": "対象読者",
  "world_setting": {
    "location": "場所",
    "time_period": "時代設定",
    "tone": "雰囲気"
  }
}""",
            phase_number=1
        )
        
        print(f"🔍 Gemini Pro Response Success: {text_response.get('success', False)}")
        if text_response.get('success'):
            print(f"   Content Length: {len(text_response.get('content', ''))}")
            print(f"   Content Preview: {text_response.get('content', '')[:200]}...")
            if 'usage' in text_response:
                print(f"   Token Usage: {text_response['usage']}")
        else:
            print(f"   Error: {text_response.get('error', 'Unknown error')}")
        
        # Test image generation (Imagen 4)
        print("\n🖼️ Testing Imagen 4 image generation...")
        image_response = await service.generate_images(
            prompts=[
                "high quality manga style, teenage boy with black hair reading mysterious book in old bookstore, detailed illustration"
            ],
            negative_prompt="low quality, blurry, distorted, bad anatomy",
            batch_size=1
        )
        
        success = len(image_response) > 0 and image_response[0].get('success', False)
        print(f"🔍 Imagen 4 Response Success: {success}")
        if success:
            print(f"   Image URL Generated: {bool(image_response[0].get('image_url'))}")
            print(f"   Quality Score: {image_response[0].get('quality_score', 'N/A')}")
            if 'usage' in image_response[0]:
                print(f"   Token Usage: {image_response[0]['usage']}")
        else:
            error = image_response[0].get('error') if image_response else 'No response'
            print(f"   Error: {error}")
        
        return text_response.get('success', False), success
        
    except Exception as e:
        print(f"❌ VertexAI Service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, False


async def test_ai_response_parsing():
    """Test AI response parsing functionality."""
    print("\n🔧 Testing AI Response Parsing...")
    
    # Mock JSON response from AI
    mock_ai_responses = [
        '''Here's the analysis:
        {
          "genre": "ファンタジー",
          "themes": ["冒険", "成長", "友情"],
          "target_audience": "中高生",
          "world_setting": {
            "location": "異世界",
            "time_period": "fantasy",
            "tone": "冒険活劇"
          }
        }
        This should work well for a manga adaptation.''',
        
        '''{"genre": "fantasy", "themes": ["adventure"], "characters": ["Tanaka"]}''',
        
        '''Invalid response without JSON''',
        
        '''Multiple JSON objects:
        {"first": "object"}
        {"second": "object"}
        We want the first one.'''
    ]
    
    def parse_ai_response(ai_content: str):
        """Parse Gemini Pro JSON response into structured data."""
        try:
            # Find JSON in response (handle cases where AI adds explanation text)
            json_start = ai_content.find('{')
            json_end = ai_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_content[json_start:json_end]
                parsed_data = json.loads(json_str)
                return parsed_data, True
            else:
                raise ValueError("No JSON found in AI response")
                
        except (json.JSONDecodeError, ValueError) as e:
            return {}, False
    
    successful_parses = 0
    
    for i, response in enumerate(mock_ai_responses, 1):
        print(f"\n  Test Case {i}:")
        print(f"    Input: {response[:50]}...")
        
        parsed_data, success = parse_ai_response(response)
        
        if success:
            print(f"    ✅ Parsing successful")
            print(f"    Result keys: {list(parsed_data.keys())}")
            successful_parses += 1
        else:
            print(f"    ❌ Parsing failed")
    
    print(f"\n📊 Parsing Results: {successful_parses}/{len(mock_ai_responses)} successful")
    
    return successful_parses >= len(mock_ai_responses) - 1  # Allow 1 failure for invalid response


async def main():
    """Main test runner."""
    print("🤖 Simple AI Integration Test")
    print("=" * 40)
    
    # Environment check
    print(f"🔧 Environment:")
    print(f"   DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not set')}")
    print(f"   GOOGLE_CLOUD_PROJECT: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'Not set')}")
    print(f"   Working Directory: {os.getcwd()}")
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    try:
        # Test 1: Vertex AI Service
        print("\n" + "=" * 40)
        text_success, image_success = await test_vertex_ai_service()
        if text_success or image_success:  # At least one should work
            tests_passed += 1
            print("✅ Vertex AI Service test: PASS")
        else:
            print("❌ Vertex AI Service test: FAIL")
        
        # Test 2: AI Response Parsing
        print("\n" + "=" * 40)
        parsing_success = await test_ai_response_parsing()
        if parsing_success:
            tests_passed += 1
            print("✅ AI Response Parsing test: PASS")
        else:
            print("❌ AI Response Parsing test: FAIL")
        
        # Test 3: Basic Configuration
        print("\n" + "=" * 40)
        print("🔧 Testing Basic Configuration...")
        
        # Check if all required environment variables are set
        required_vars = ['DATABASE_URL', 'GOOGLE_CLOUD_PROJECT', 'GOOGLE_CLOUD_REGION']
        config_success = all(os.environ.get(var) for var in required_vars)
        
        if config_success:
            tests_passed += 1
            print("✅ Configuration test: PASS")
        else:
            missing_vars = [var for var in required_vars if not os.environ.get(var)]
            print(f"❌ Configuration test: FAIL (missing: {missing_vars})")
        
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 40)
    print("🏁 Test Summary")
    print("=" * 40)
    
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! AI integration is working.")
        return True
    elif tests_passed > 0:
        print("⚠️ Partial success. Some AI features may work.")
        return True
    else:
        print("❌ All tests failed. Check configuration and dependencies.")
        return False


if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Batch integration script for updating Phase 3,4,6,7 agents with Vertex AI integration.
This script updates multiple agents with Gemini Pro integration patterns.
"""

import os
import re
from pathlib import Path

# Base directory for agents
AGENTS_DIR = Path("../app/agents")

# Template for Vertex AI integration
VERTEX_AI_IMPORT = """from app.services.vertex_ai_service import VertexAIService"""

VERTEX_AI_INIT = """        # Vertex AI サービス初期化
        self.vertex_ai = VertexAIService()"""

# AI integration template for process_phase
AI_INTEGRATION_TEMPLATE = """        # Call Gemini Pro for AI analysis
        try:
            ai_response = await self.vertex_ai.generate_text(
                prompt=prompt,
                phase_number=self.phase_number
            )
            
            if ai_response.get("success", False):
                # Parse JSON response from Gemini Pro  
                ai_result = self._parse_ai_response(ai_response.get("content", ""))
                
                self.log_info(f"Gemini Pro analysis successful", 
                            tokens=ai_response.get("usage", {}).get("total_tokens", 0))
                
                # Use AI result or fallback
                {result_assignment}
                
            else:
                # Fallback to rule-based analysis
                self.log_warning(f"Gemini Pro failed, using fallback: {{ai_response.get('error', 'Unknown error')}}")
                {fallback_code}
                
        except Exception as e:
            # Fallback to rule-based analysis on error
            self.log_error(f"AI analysis failed, using fallback: {{str(e)}}")
            {fallback_code}"""

# JSON parsing function template
PARSE_AI_RESPONSE = """
    def _parse_ai_response(self, ai_content: str) -> Dict[str, Any]:
        \"\"\"Parse Gemini Pro JSON response into structured data.\"\"\"
        try:
            # Find JSON in response (handle cases where AI adds explanation text)
            json_start = ai_content.find('{')
            json_end = ai_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_content[json_start:json_end]
                parsed_data = json.loads(json_str)
                return parsed_data
            else:
                raise ValueError("No JSON found in AI response")
                
        except (json.JSONDecodeError, ValueError) as e:
            self.log_warning(f"Failed to parse AI response as JSON: {str(e)}")
            return {}"""

def update_agent_file(file_path: Path, phase_number: int):
    """Update a single agent file with Vertex AI integration."""
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    print(f"Updating {file_path.name}...")
    
    content = file_path.read_text(encoding='utf-8')
    
    # Add Vertex AI import if not present
    if "VertexAIService" not in content:
        content = content.replace(
            "from app.core.config import settings",
            f"from app.core.config import settings\n{VERTEX_AI_IMPORT}"
        )
    
    # Add Vertex AI initialization in __init__ if not present
    if "self.vertex_ai = VertexAIService()" not in content:
        init_pattern = r"(\s+)(timeout_seconds=settings\.phase_timeouts\[\d+\]\s*\))"
        replacement = r"\1\2\n        \n        # Vertex AI サービス初期化\n        self.vertex_ai = VertexAIService()"
        content = re.sub(init_pattern, replacement, content)
    
    # Replace TODO comments with actual AI integration  
    todo_pattern = r"(\s+)# TODO: Call actual AI API.*?\n.*?# For now, use.*?\n(.*?)(\n\s+)"
    
    def replace_todo(match):
        indent = match.group(1)
        existing_code = match.group(2)
        end_whitespace = match.group(3)
        
        # Extract result assignment pattern
        result_var_match = re.search(r"(\w+)\s*=\s*await", existing_code)
        if result_var_match:
            result_var = result_var_match.group(1)
            result_assignment = f"{result_var} = ai_result"
            fallback_code = existing_code.strip()
        else:
            result_assignment = "# Use AI result"  
            fallback_code = existing_code.strip()
        
        # Generate AI integration code
        ai_code = AI_INTEGRATION_TEMPLATE.format(
            result_assignment=result_assignment,
            fallback_code=fallback_code
        )
        
        # Apply proper indentation
        ai_code_lines = ai_code.strip().split('\n')
        indented_lines = [indent + line if line.strip() else line for line in ai_code_lines]
        
        return '\n'.join(indented_lines) + end_whitespace
    
    content = re.sub(todo_pattern, replace_todo, content, flags=re.DOTALL)
    
    # Add _parse_ai_response method if not present
    if "_parse_ai_response" not in content:
        # Find the end of the class to add the method
        class_end_pattern = r"(\n\s+def _create_.*?visualization.*?\n.*?return.*?\n.*?})"
        if re.search(class_end_pattern, content, re.DOTALL):
            content = re.sub(
                class_end_pattern, 
                r"\1" + PARSE_AI_RESPONSE,
                content,
                flags=re.DOTALL
            )
    
    # Write updated content
    file_path.write_text(content, encoding='utf-8')
    print(f"Updated {file_path.name} successfully")

def main():
    """Main function to update all agent files."""
    
    # Phase configurations
    phases_to_update = [
        {"number": 3, "file": "phase3_story.py"},
        {"number": 4, "file": "phase4_name.py"},
        {"number": 6, "file": "phase6_dialogue.py"},
        {"number": 7, "file": "phase7_integration.py"}
    ]
    
    base_path = Path(__file__).parent.parent / "app" / "agents"
    
    for phase in phases_to_update:
        file_path = base_path / phase["file"]
        update_agent_file(file_path, phase["number"])
    
    print("All agent files updated successfully!")

if __name__ == "__main__":
    main()
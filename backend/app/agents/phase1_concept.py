"""Phase 1: Concept and World Analysis Agent."""

from typing import Dict, Any, Optional, List
from uuid import UUID
import json
import re

from app.agents.base_agent import BaseAgent
from app.core.config import settings
from app.services.vertex_ai_service import VertexAIService


class Phase1ConceptAgent(BaseAgent):
    """Agent for analyzing concepts and world settings from text."""
    
    def __init__(self):
        super().__init__(
            phase_number=1,
            phase_name="コンセプト・世界観分析",
            timeout_seconds=settings.phase_timeouts[1]
        )
        
        # Vertex AI サービス初期化
        self.vertex_ai = VertexAIService()
        
        self.genre_keywords = {
            "fantasy": ["魔法", "エルフ", "ドラゴン", "勇者", "魔王", "冒険", "ファンタジー"],
            "romance": ["恋", "愛", "告白", "デート", "結婚", "恋愛", "ロマンス"],
            "action": ["戦闘", "バトル", "格闘", "戦い", "決闘", "アクション"],
            "mystery": ["事件", "謎", "探偵", "推理", "犯人", "ミステリー"],
            "slice_of_life": ["日常", "学校", "生活", "友達", "家族", "青春"],
            "sci_fi": ["宇宙", "ロボット", "未来", "科学", "SF", "テクノロジー"],
            "horror": ["怖い", "恐怖", "幽霊", "呪い", "ホラー", "怪談"]
        }
    
    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: UUID,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze text to extract concepts and world settings.
        
        Args:
            input_data: Contains 'text' key with input story text
            session_id: Current session ID
            previous_results: Not used in phase 1
            
        Returns:
            Analysis results with themes, genre, world settings
        """
        text = input_data.get("text", "")
        
        if not text:
            raise ValueError("Input text is required for concept analysis")
        
        # Generate prompt for AI analysis
        prompt = await self.generate_prompt(input_data, previous_results)
        
        # Call Gemini Pro for AI analysis
        try:
            ai_response = await self.vertex_ai.generate_text(
                prompt=prompt,
                phase_number=self.phase_number
            )
            
            if ai_response.get("success", False):
                # Parse JSON response from Gemini Pro
                analysis_result = self._parse_ai_response(ai_response.get("content", ""))
                self.log_info(f"Gemini Pro analysis successful", 
                            tokens=ai_response.get("usage", {}).get("total_tokens", 0))
            else:
                # Fallback to rule-based analysis
                self.log_warning(f"Gemini Pro failed, using fallback: {ai_response.get('error', 'Unknown error')}")
                analysis_result = await self._analyze_text(text)
                
        except Exception as e:
            # Fallback to rule-based analysis on error
            self.log_error(f"AI analysis failed, using fallback: {str(e)}")
            analysis_result = await self._analyze_text(text)
        
        # Extract key information
        result = {
            "original_text": text[:1000],  # Store first 1000 chars
            "text_length": len(text),
            "themes": analysis_result.get("themes", []),
            "genre": analysis_result.get("genre", "general"),
            "world_setting": analysis_result.get("world_setting", {}),
            "tone": analysis_result.get("tone", "neutral"),
            "key_elements": analysis_result.get("key_elements", []),
            "target_audience": analysis_result.get("target_audience", "general"),
            "narrative_style": analysis_result.get("narrative_style", "third_person"),
            "estimated_pages": self._estimate_pages(len(text))
        }
        
        return result
    
    async def generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate Gemini Pro prompt for concept analysis."""
        
        text = input_data.get("text", "")
        
        prompt = f"""あなたは漫画制作のための物語分析の専門家です。以下のテキストを分析し、漫画化に必要な要素をJSON形式で出力してください。

【入力テキスト】
{text[:2000]}

【出力形式】
必ず以下の形式のJSONでのみ回答してください。説明文は一切不要です：

{{
    "themes": ["テーマ1", "テーマ2", "テーマ3"],
    "genre": "選択したジャンル",
    "world_setting": {{
        "time_period": "時代設定",
        "location": "舞台",
        "atmosphere": "雰囲気"
    }},
    "tone": "トーン",
    "key_elements": ["重要要素1", "重要要素2", "重要要素3", "重要要素4", "重要要素5"],
    "target_audience": "対象読者",
    "narrative_style": "語り口"
}}

【選択肢】
- genre: fantasy, romance, action, mystery, slice_of_life, sci_fi, horror, general
- tone: light, dark, serious, comedic, dramatic
- target_audience: children, teens, young_adults, adults, general  
- narrative_style: first_person, third_person, omniscient
- time_period: present, past, future, fantasy
- atmosphere: bright, dark, serious, comedic, mysterious, peaceful

【重要】
- JSONのみを出力してください
- 説明文や追加のテキストは含めないでください
- 文字列は日本語で記述してください（キーワード選択肢は英語のまま）"""
        
        return prompt
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate phase 1 output."""
        
        required_keys = [
            "themes", "genre", "world_setting", "tone",
            "key_elements", "target_audience"
        ]
        
        # Check all required keys exist
        for key in required_keys:
            if key not in output_data:
                self.log_warning(f"Missing required key: {key}")
                return False
        
        # Validate themes
        if not output_data["themes"] or len(output_data["themes"]) < 1:
            self.log_warning("No themes extracted")
            return False
        
        # Validate genre
        valid_genres = ["fantasy", "romance", "action", "mystery", 
                       "slice_of_life", "sci_fi", "horror", "general"]
        if output_data["genre"] not in valid_genres:
            self.log_warning(f"Invalid genre: {output_data['genre']}")
            return False
        
        return True
    
    async def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text using rule-based approach (placeholder for AI).
        
        This is a temporary implementation until AI API is integrated.
        """
        
        # Detect genre based on keywords
        genre_scores = {}
        text_lower = text.lower()
        
        for genre, keywords in self.genre_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            genre_scores[genre] = score
        
        detected_genre = max(genre_scores, key=genre_scores.get) if max(genre_scores.values()) > 0 else "general"
        
        # Extract themes based on common patterns
        themes = []
        theme_patterns = {
            "友情": ["友", "仲間", "友達", "絆"],
            "成長": ["成長", "強く", "変わ", "進化"],
            "冒険": ["冒険", "旅", "探検", "挑戦"],
            "愛": ["愛", "恋", "好き", "大切"],
            "正義": ["正義", "悪", "守る", "戦う"]
        }
        
        for theme, patterns in theme_patterns.items():
            if any(pattern in text for pattern in patterns):
                themes.append(theme)
        
        if not themes:
            themes = ["一般"]
        
        # Detect tone
        if any(word in text_lower for word in ["楽しい", "明るい", "嬉しい", "幸せ"]):
            tone = "light"
        elif any(word in text_lower for word in ["暗い", "悲しい", "怖い", "恐ろしい"]):
            tone = "dark"
        elif any(word in text_lower for word in ["真剣", "シリアス", "重要", "深刻"]):
            tone = "serious"
        else:
            tone = "neutral"
        
        # Extract key elements (simple word frequency)
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
        word_freq = {}
        for word in words:
            if len(word) > 1:  # Skip single characters
                word_freq[word] = word_freq.get(word, 0) + 1
        
        key_elements = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        key_elements = [word for word, _ in key_elements]
        
        # Determine world setting
        world_setting = {
            "time_period": self._detect_time_period(text),
            "location": self._detect_location(text),
            "atmosphere": tone
        }
        
        return {
            "themes": themes[:5],
            "genre": detected_genre,
            "world_setting": world_setting,
            "tone": tone,
            "key_elements": key_elements,
            "target_audience": self._detect_audience(text),
            "narrative_style": "third_person"  # Default for now
        }
    
    def _detect_time_period(self, text: str) -> str:
        """Detect time period from text."""
        
        if any(word in text for word in ["未来", "宇宙", "ロボット", "AI"]):
            return "future"
        elif any(word in text for word in ["昔", "江戸", "侍", "城"]):
            return "past"
        elif any(word in text for word in ["魔法", "ドラゴン", "エルフ"]):
            return "fantasy"
        else:
            return "present"
    
    def _detect_location(self, text: str) -> str:
        """Detect primary location from text."""
        
        locations = {
            "学校": ["学校", "教室", "校庭", "部活"],
            "都市": ["都市", "街", "ビル", "駅"],
            "自然": ["森", "山", "海", "川"],
            "異世界": ["異世界", "魔法", "城", "王国"],
            "宇宙": ["宇宙", "惑星", "宇宙船", "星"]
        }
        
        for location, keywords in locations.items():
            if any(keyword in text for keyword in keywords):
                return location
        
        return "一般"
    
    def _detect_audience(self, text: str) -> str:
        """Detect target audience from text content."""
        
        # Simple heuristics for audience detection
        if any(word in text for word in ["子供", "小学", "友達と遊"]):
            return "children"
        elif any(word in text for word in ["高校", "青春", "恋愛", "部活"]):
            return "teens"
        elif any(word in text for word in ["大学", "就職", "仕事", "結婚"]):
            return "young_adults"
        elif any(word in text for word in ["会社", "家族", "社会", "政治"]):
            return "adults"
        else:
            return "general"
    
    def _estimate_pages(self, text_length: int) -> int:
        """Estimate manga pages based on text length."""
        
        # Rough estimation: 200-300 characters per page
        chars_per_page = 250
        estimated = text_length // chars_per_page
        
        # Clamp between 4 and 50 pages
        return max(4, min(50, estimated))
    
    async def generate_preview(
        self,
        output_data: Dict[str, Any],
        quality_level: str = "high"
    ) -> Dict[str, Any]:
        """Generate preview for phase 1 results."""
        
        preview = {
            "phase": self.phase_number,
            "title": "コンセプト・世界観分析",
            "summary": {
                "ジャンル": output_data.get("genre", "未定"),
                "テーマ": output_data.get("themes", [])[:3],
                "世界観": output_data.get("world_setting", {}),
                "トーン": output_data.get("tone", "中立"),
                "対象読者": output_data.get("target_audience", "一般")
            },
            "details": {
                "重要要素": output_data.get("key_elements", []),
                "推定ページ数": output_data.get("estimated_pages", 8),
                "語り口": output_data.get("narrative_style", "三人称")
            },
            "visualization": {
                "type": "concept_map",
                "data": self._create_concept_visualization(output_data)
            }
        }
        
        return preview
    
    def _create_concept_visualization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create visualization data for concept map."""
        
        return {
            "nodes": [
                {"id": "center", "label": data.get("genre", ""), "type": "genre"},
                *[{"id": f"theme_{i}", "label": theme, "type": "theme"} 
                  for i, theme in enumerate(data.get("themes", []))],
                *[{"id": f"element_{i}", "label": elem, "type": "element"} 
                  for i, elem in enumerate(data.get("key_elements", [])[:3])]
            ],
            "edges": [
                *[{"from": "center", "to": f"theme_{i}"} 
                  for i in range(len(data.get("themes", [])))],
                *[{"from": "center", "to": f"element_{i}"} 
                  for i in range(min(3, len(data.get("key_elements", []))))]
            ]
        }
    
    def _parse_ai_response(self, ai_content: str) -> Dict[str, Any]:
        """Parse Gemini Pro JSON response into structured data."""
        try:
            # Find JSON in response (handle cases where AI adds explanation text)
            json_start = ai_content.find('{')
            json_end = ai_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_content[json_start:json_end]
                parsed_data = json.loads(json_str)
                
                # Validate and normalize the parsed data
                return self._normalize_ai_data(parsed_data)
            else:
                raise ValueError("No JSON found in AI response")
                
        except (json.JSONDecodeError, ValueError) as e:
            self.log_warning(f"Failed to parse AI response as JSON: {str(e)}")
            # Try to extract information from raw text as fallback
            return self._extract_from_raw_text(ai_content)
    
    def _normalize_ai_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize AI response data to expected format."""
        
        # Ensure required fields exist with defaults
        normalized = {
            "themes": data.get("themes", []),
            "genre": data.get("genre", "general"),
            "world_setting": data.get("world_setting", {}),
            "tone": data.get("tone", "neutral"),
            "key_elements": data.get("key_elements", []),
            "target_audience": data.get("target_audience", "general"),
            "narrative_style": data.get("narrative_style", "third_person")
        }
        
        # Validate genre
        valid_genres = ["fantasy", "romance", "action", "mystery", 
                       "slice_of_life", "sci_fi", "horror", "general"]
        if normalized["genre"] not in valid_genres:
            self.log_warning(f"Invalid genre from AI: {normalized['genre']}, defaulting to 'general'")
            normalized["genre"] = "general"
        
        # Validate tone
        valid_tones = ["light", "dark", "serious", "comedic", "dramatic", "neutral"]
        if normalized["tone"] not in valid_tones:
            normalized["tone"] = "neutral"
        
        # Validate target audience
        valid_audiences = ["children", "teens", "young_adults", "adults", "general"]
        if normalized["target_audience"] not in valid_audiences:
            normalized["target_audience"] = "general"
        
        # Ensure world_setting has required structure
        if not isinstance(normalized["world_setting"], dict):
            normalized["world_setting"] = {}
        
        world_setting_defaults = {
            "time_period": "present",
            "location": "一般",
            "atmosphere": normalized["tone"]
        }
        
        for key, default_value in world_setting_defaults.items():
            if key not in normalized["world_setting"]:
                normalized["world_setting"][key] = default_value
        
        # Limit list lengths
        normalized["themes"] = normalized["themes"][:5]
        normalized["key_elements"] = normalized["key_elements"][:10]
        
        return normalized
    
    def _extract_from_raw_text(self, text: str) -> Dict[str, Any]:
        """Extract information from raw AI text as fallback."""
        
        # Try to find key information in the text
        extracted = {
            "themes": [],
            "genre": "general",
            "world_setting": {
                "time_period": "present",
                "location": "一般",
                "atmosphere": "neutral"
            },
            "tone": "neutral",
            "key_elements": [],
            "target_audience": "general",
            "narrative_style": "third_person"
        }
        
        # Simple pattern matching to extract information
        lines = text.lower().split('\n')
        
        for line in lines:
            # Look for genre indicators
            for genre in ["fantasy", "romance", "action", "mystery", "slice_of_life", "sci_fi", "horror"]:
                if genre in line or genre.replace('_', ' ') in line:
                    extracted["genre"] = genre
                    break
            
            # Look for tone indicators
            if any(word in line for word in ["light", "bright", "cheerful"]):
                extracted["tone"] = "light"
            elif any(word in line for word in ["dark", "serious", "grim"]):
                extracted["tone"] = "dark"
            elif any(word in line for word in ["comedic", "funny", "humorous"]):
                extracted["tone"] = "comedic"
        
        return extracted
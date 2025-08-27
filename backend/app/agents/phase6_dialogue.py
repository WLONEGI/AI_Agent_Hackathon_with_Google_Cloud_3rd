"""Phase 6: Dialogue and Text Placement Agent."""

from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
import asyncio
import json
import math

from app.agents.base_agent import BaseAgent
from app.core.config import settings
from app.services.vertex_ai_service import VertexAIService


class Phase6DialogueAgent(BaseAgent):
    """Agent for dialogue generation and text placement in manga panels."""
    
    def __init__(self):
        super().__init__(
            phase_number=6,
            phase_name="セリフ配置",
            timeout_seconds=settings.phase_timeouts[6]
        )
        
        # Dialogue types and their characteristics
        self.dialogue_types = {
            "speech": {
                "bubble_style": "standard_speech",
                "tail_style": "pointed",
                "text_size": "normal",
                "font_weight": "normal"
            },
            "thought": {
                "bubble_style": "cloud_thought",
                "tail_style": "bubbles",
                "text_size": "italic",
                "font_weight": "normal"
            },
            "shout": {
                "bubble_style": "jagged_excitement",
                "tail_style": "lightning",
                "text_size": "large",
                "font_weight": "bold"
            },
            "whisper": {
                "bubble_style": "dotted_soft",
                "tail_style": "small_curved",
                "text_size": "small",
                "font_weight": "light"
            },
            "narration": {
                "bubble_style": "rectangular_box",
                "tail_style": "none",
                "text_size": "normal",
                "font_weight": "normal"
            }
        }
        
        # Text placement rules based on panel composition
        self.placement_rules = {
            "close_up": {
                "preferred_positions": ["top", "bottom"],
                "avoid_positions": ["center"],
                "max_text_coverage": 0.3
            },
            "medium_shot": {
                "preferred_positions": ["top", "sides", "bottom"],
                "avoid_positions": [],
                "max_text_coverage": 0.4
            },
            "wide_shot": {
                "preferred_positions": ["anywhere"],
                "avoid_positions": [],
                "max_text_coverage": 0.5
            },
            "action_scene": {
                "preferred_positions": ["edges"],
                "avoid_positions": ["center", "movement_path"],
                "max_text_coverage": 0.25
            }
        }
        
        # Japanese text formatting rules
        self.japanese_text_rules = {
            "reading_direction": "right_to_left",
            "vertical_text": True,
            "character_spacing": "normal",
            "line_spacing": 1.2,
            "punctuation_handling": "japanese_rules"
        }
        
        # Vertex AI サービス初期化
        self.vertex_ai = VertexAIService()
    
    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: UUID,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Generate dialogue and place text in manga panels."""
        
        if not previous_results or not all(i in previous_results for i in [1, 2, 3, 4, 5]):
            raise ValueError("Phases 1-5 results required for dialogue placement")
        
        # Extract previous phase results
        phase1_result = previous_results[1]
        phase2_result = previous_results[2]
        phase3_result = previous_results[3]
        phase4_result = previous_results[4]
        phase5_result = previous_results[5]
        
        # Call Gemini Pro for AI analysis
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
                dialogue_content = ai_result if ai_result else await self._generate_dialogue_content(phase1_result, phase2_result, phase3_result, phase4_result)
                
            else:
                # Fallback to rule-based analysis
                self.log_warning(f"Gemini Pro failed, using fallback: {ai_response.get('error', 'Unknown error')}")
                dialogue_content = await self._generate_dialogue_content(phase1_result, phase2_result, phase3_result, phase4_result)
                
        except Exception as e:
            # Fallback to rule-based analysis on error
            self.log_error(f"AI analysis failed, using fallback: {str(e)}")
            dialogue_content = await self._generate_dialogue_content(phase1_result, phase2_result, phase3_result, phase4_result)
        
        # Create text placement specifications
        text_placements = await self._create_text_placements(
            dialogue_content, phase4_result, phase5_result
        )
        
        # Generate typography specifications
        typography_specs = await self._generate_typography_specifications(
            text_placements, phase1_result.get("genre", "general")
        )
        
        # Optimize readability
        readability_optimization = await self._optimize_readability(
            text_placements, typography_specs, phase4_result
        )
        
        # Generate bubble and balloon designs
        bubble_designs = await self._generate_bubble_designs(
            text_placements, dialogue_content
        )
        
        # Create dialogue flow analysis
        dialogue_flow = await self._analyze_dialogue_flow(
            dialogue_content, text_placements, phase3_result
        )
        
        result = {
            "dialogue_content": dialogue_content,
            "text_placements": text_placements,
            "typography_specifications": typography_specs,
            "bubble_designs": bubble_designs,
            "dialogue_flow": dialogue_flow,
            "readability_analysis": readability_optimization,
            "total_dialogue_elements": len(text_placements),
            "characters_speaking": len(set(
                placement.get("speaker") for placement in text_placements 
                if placement.get("speaker")
            )),
            "dialogue_density_score": self._calculate_dialogue_density(
                text_placements, phase4_result
            ),
            "readability_score": self._calculate_readability_score(
                text_placements, readability_optimization
            ),
            "text_image_integration_score": self._calculate_integration_score(
                text_placements, phase5_result
            )
        }
        
        return result
    
    async def generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate Gemini Pro prompt for dialogue generation."""
        
        phase1_result = previous_results[1] if previous_results else {}
        phase2_result = previous_results[2] if previous_results else {}
        phase3_result = previous_results[3] if previous_results else {}
        phase4_result = previous_results[4] if previous_results else {}
        
        genre = phase1_result.get("genre", "general")
        themes = phase1_result.get("themes", [])
        characters = phase2_result.get("characters", [])
        scene_breakdown = phase3_result.get("scene_breakdown", [])
        panel_specifications = phase4_result.get("panel_specifications", [])
        
        character_summary = "\n".join([
            f"- {char.get('name')}: {char.get('personality', [])} / {char.get('goals', '目標不明')}"
            for char in characters[:4]
        ]) if characters else "キャラクター情報なし"
        
        total_panels = len(panel_specifications)
        
        prompt = f"""あなたは漫画制作におけるセリフ・テキスト配置の専門家です。
以下の設定に基づいて、{total_panels}のパネルにセリフとテキストを配置してください。

【基本設定】
ジャンル: {genre}
テーマ: {', '.join(themes)}
総パネル数: {total_panels}

【キャラクター】
{character_summary}

【シーン情報】
{len(scene_breakdown)}シーンの物語構成

【セリフ生成要件】
1. キャラクターの個性を反映した自然な会話
2. 物語進行に必要な情報の効果的な配置
3. 感情表現とトーンの適切な使い分け
4. 読みやすさを重視したテキスト量の調整
5. パネル構図との調和

【テキスト配置要件】
1. 画像の重要部分を遮らない配置
2. 読み順を明確にするレイアウト
3. セリフの種類に応じた吹き出しスタイル
4. 日本語の縦書き・右から左への読み順対応

【出力形式】JSON
{{
    "dialogue_content": [
        {{
            "panel_id": "p1_panel1",
            "dialogue_elements": [
                {{
                    "speaker": "character_name",
                    "text": "セリフ内容",
                    "dialogue_type": "speech/thought/shout/whisper/narration",
                    "emotion": "emotion_type",
                    "importance": "high/medium/low",
                    "text_length": 15
                }}
            ],
            "narration": {{
                "text": "ナレーション内容",
                "position": "top/bottom",
                "style": "descriptive/informative"
            }}
        }}
    ],
    "text_placement_guidelines": {{
        "reading_flow": "right_to_left_top_to_bottom",
        "bubble_priority": "speech > thought > narration",
        "space_utilization": "balanced"
    }}
}}"""
        
        return prompt
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate Phase 6 output."""
        
        required_keys = [
            "dialogue_content", "text_placements", "typography_specifications",
            "bubble_designs", "total_dialogue_elements"
        ]
        
        for key in required_keys:
            if key not in output_data:
                self.log_warning(f"Missing required key: {key}")
                return False
        
        dialogue_content = output_data.get("dialogue_content", [])
        text_placements = output_data.get("text_placements", [])
        
        # Must have dialogue content
        if len(dialogue_content) < 1:
            self.log_warning("No dialogue content generated")
            return False
        
        # Check dialogue completeness
        for dialogue in dialogue_content:
            if not dialogue.get("panel_id"):
                self.log_warning("Dialogue missing panel_id")
                return False
        
        # Check text placement completeness
        for placement in text_placements:
            required_placement_fields = ["panel_id", "text_content", "position", "bubble_style"]
            if not all(field in placement for field in required_placement_fields):
                self.log_warning(f"Incomplete text placement data: {placement.get('panel_id', 'unknown')}")
                return False
        
        return True
    
    async def _generate_dialogue_content(
        self,
        phase1_result: Dict[str, Any],
        phase2_result: Dict[str, Any],
        phase3_result: Dict[str, Any],
        phase4_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate dialogue content for each panel."""
        
        # Extract necessary data
        genre = phase1_result.get("genre", "general")
        themes = phase1_result.get("themes", [])
        characters = phase2_result.get("characters", [])
        scene_breakdown = phase3_result.get("scene_breakdown", [])
        panel_specifications = phase4_result.get("panel_specifications", [])
        
        dialogue_content = []
        
        # Generate dialogue for each panel
        for panel_spec in panel_specifications:
            panel_id = panel_spec.get("panel_id", "")
            scene_number = panel_spec.get("scene_number", 1)
            emotional_tone = panel_spec.get("emotional_tone", "neutral")
            
            # Find corresponding scene
            scene = next(
                (s for s in scene_breakdown if s.get("scene_number") == scene_number),
                {}
            )
            
            # Get characters in this panel
            panel_characters = panel_spec.get("characters", [])
            
            # Generate dialogue elements
            dialogue_elements = await self._generate_panel_dialogue_elements(
                panel_characters, characters, scene, emotional_tone, genre
            )
            
            # Generate narration if needed
            narration = await self._generate_panel_narration(
                scene, panel_spec, dialogue_elements
            )
            
            panel_dialogue = {
                "panel_id": panel_id,
                "scene_number": scene_number,
                "dialogue_elements": dialogue_elements,
                "narration": narration,
                "total_text_elements": len(dialogue_elements) + (1 if narration else 0),
                "estimated_reading_time": self._estimate_panel_reading_time(
                    dialogue_elements, narration
                )
            }
            
            dialogue_content.append(panel_dialogue)
        
        return dialogue_content
    
    async def _generate_panel_dialogue_elements(
        self,
        panel_characters: List[Dict[str, Any]],
        all_characters: List[Dict[str, Any]],
        scene: Dict[str, Any],
        emotional_tone: str,
        genre: str
    ) -> List[Dict[str, Any]]:
        """Generate dialogue elements for a specific panel."""
        
        dialogue_elements = []
        
        if not panel_characters:
            return dialogue_elements
        
        # Determine dialogue based on scene purpose and emotional tone
        scene_purpose = scene.get("purpose", "")
        scene_pacing = scene.get("pacing", "medium")
        
        # Generate dialogue for each character
        for i, panel_char in enumerate(panel_characters):
            char_name = panel_char.get("name", "")
            
            # Find full character data
            full_char = next((c for c in all_characters if c.get("name") == char_name), {})
            
            # Generate appropriate dialogue
            dialogue_text = await self._generate_character_dialogue(
                full_char, scene, emotional_tone, genre, i == 0
            )
            
            if dialogue_text:
                # Determine dialogue type based on emotional tone and content
                dialogue_type = self._determine_dialogue_type(
                    dialogue_text, emotional_tone, scene_pacing
                )
                
                dialogue_element = {
                    "speaker": char_name,
                    "text": dialogue_text,
                    "dialogue_type": dialogue_type,
                    "emotion": emotional_tone,
                    "importance": self._determine_dialogue_importance(
                        dialogue_text, scene_purpose, i == 0
                    ),
                    "text_length": len(dialogue_text),
                    "estimated_syllables": self._estimate_syllables(dialogue_text),
                    "speech_pattern": self._get_character_speech_pattern(full_char)
                }
                
                dialogue_elements.append(dialogue_element)
        
        return dialogue_elements
    
    async def _generate_character_dialogue(
        self,
        character: Dict[str, Any],
        scene: Dict[str, Any],
        emotional_tone: str,
        genre: str,
        is_primary_speaker: bool
    ) -> str:
        """Generate dialogue for a specific character."""
        
        # Character personality influences dialogue
        personality = character.get("personality", [])
        char_name = character.get("name", "キャラクター")
        
        # Scene context influences content
        scene_purpose = scene.get("purpose", "")
        
        # Generate dialogue based on context
        if "introduction" in scene_purpose:
            if is_primary_speaker:
                dialogue = self._generate_introduction_dialogue(char_name, personality)
            else:
                dialogue = self._generate_response_dialogue(emotional_tone)
        elif "conflict" in scene_purpose:
            dialogue = self._generate_conflict_dialogue(char_name, personality, emotional_tone)
        elif "resolution" in scene_purpose:
            dialogue = self._generate_resolution_dialogue(emotional_tone, personality)
        else:
            dialogue = self._generate_general_dialogue(char_name, personality, emotional_tone)
        
        # Apply genre-specific modifications
        dialogue = self._apply_genre_dialogue_style(dialogue, genre, personality)
        
        # Ensure appropriate length
        dialogue = self._adjust_dialogue_length(dialogue, emotional_tone)
        
        return dialogue
    
    def _generate_introduction_dialogue(self, char_name: str, personality: List[str]) -> str:
        """Generate introduction dialogue."""
        
        intro_templates = {
            "friendly": [
                "よろしくお願いします！",
                "初めまして、{}です。",
                "こんにちは！"
            ],
            "serious": [
                "私は{}です。",
                "{}と申します。",
                "お初にお目にかかります。"
            ],
            "casual": [
                "{}だよ！",
                "よろしく〜",
                "はじめまして！"
            ]
        }
        
        # Determine style based on personality
        if any(trait in ["明るい", "友達想い", "元気"] for trait in personality):
            style = "friendly"
        elif any(trait in ["真剣", "冷静", "完璧主義"] for trait in personality):
            style = "serious"
        else:
            style = "casual"
        
        templates = intro_templates.get(style, intro_templates["casual"])
        template = templates[0]  # Use first template for simplicity
        
        if "{}" in template:
            return template.format(char_name)
        else:
            return template
    
    def _generate_response_dialogue(self, emotional_tone: str) -> str:
        """Generate response dialogue."""
        
        response_templates = {
            "curiosity": ["そうなんですね", "興味深いです", "へえ〜"],
            "engagement": ["なるほど", "そうですね", "分かります"],
            "concern": ["大丈夫ですか？", "心配です", "どうしたんですか？"],
            "tension": ["え？", "まさか...", "そんな..."],
            "relief": ["良かった", "安心しました", "ほっとしました"]
        }
        
        templates = response_templates.get(emotional_tone, ["そうですね"])
        return templates[0]
    
    def _generate_conflict_dialogue(
        self, char_name: str, personality: List[str], emotional_tone: str
    ) -> str:
        """Generate conflict dialogue."""
        
        if emotional_tone in ["tension", "anxiety"]:
            if "勇敢" in personality:
                return "負けるわけにはいかない！"
            elif "冷静" in personality:
                return "落ち着いて考えましょう。"
            else:
                return "どうしよう..."
        else:
            if "正義感が強い" in personality:
                return "これは間違っています！"
            else:
                return "困りましたね..."
    
    def _generate_resolution_dialogue(self, emotional_tone: str, personality: List[str]) -> str:
        """Generate resolution dialogue."""
        
        if emotional_tone in ["relief", "satisfaction"]:
            if "明るい" in personality:
                return "やったね！"
            else:
                return "良かった..."
        else:
            return "終わりましたね。"
    
    def _generate_general_dialogue(
        self, char_name: str, personality: List[str], emotional_tone: str
    ) -> str:
        """Generate general dialogue."""
        
        general_templates = {
            "curious": "それは...",
            "neutral": "そうですね。",
            "positive": "いいですね！",
            "negative": "うーん..."
        }
        
        # Map emotional tone to general category
        if emotional_tone in ["curiosity", "engagement"]:
            return general_templates["curious"]
        elif emotional_tone in ["satisfaction", "relief"]:
            return general_templates["positive"]
        elif emotional_tone in ["tension", "anxiety"]:
            return general_templates["negative"]
        else:
            return general_templates["neutral"]
    
    def _apply_genre_dialogue_style(
        self, dialogue: str, genre: str, personality: List[str]
    ) -> str:
        """Apply genre-specific dialogue styling."""
        
        if genre == "action":
            # Make action dialogue more dynamic
            if "！" not in dialogue and len(dialogue) < 10:
                dialogue = dialogue.rstrip("。") + "！"
        elif genre == "romance":
            # Make romance dialogue softer
            if dialogue.endswith("！"):
                dialogue = dialogue.rstrip("！") + "..."
        elif genre == "mystery":
            # Add mystery atmosphere
            if len(dialogue) < 5:
                dialogue += "..."
        
        return dialogue
    
    def _adjust_dialogue_length(self, dialogue: str, emotional_tone: str) -> str:
        """Adjust dialogue length for readability."""
        
        # Maximum comfortable length for manga dialogue
        max_length = 25
        
        if len(dialogue) > max_length:
            # Truncate and add ellipsis
            dialogue = dialogue[:max_length-3] + "..."
        
        # Minimum length for some emotional tones
        if emotional_tone in ["tension", "climax"] and len(dialogue) < 5:
            dialogue += "！"
        
        return dialogue
    
    def _determine_dialogue_type(
        self, dialogue_text: str, emotional_tone: str, scene_pacing: str
    ) -> str:
        """Determine the type of dialogue bubble needed."""
        
        # Check for obvious indicators
        if dialogue_text.endswith("！") or dialogue_text.endswith("!"):
            if emotional_tone in ["tension", "climax"]:
                return "shout"
            else:
                return "speech"
        elif dialogue_text.endswith("..."):
            if "思" in dialogue_text or "考え" in dialogue_text:
                return "thought"
            else:
                return "whisper"
        elif "（" in dialogue_text or "）" in dialogue_text:
            return "thought"
        else:
            return "speech"
    
    def _determine_dialogue_importance(
        self, dialogue_text: str, scene_purpose: str, is_primary: bool
    ) -> str:
        """Determine the importance level of dialogue."""
        
        # Primary speakers in key scenes are high importance
        if is_primary and any(keyword in scene_purpose 
                              for keyword in ["climax", "resolution", "conflict"]):
            return "high"
        
        # Long or emotional dialogue is medium importance
        if len(dialogue_text) > 15 or dialogue_text.endswith("！"):
            return "medium"
        
        return "low"
    
    def _estimate_syllables(self, text: str) -> int:
        """Estimate syllable count for Japanese text."""
        
        # Simple approximation: most Japanese characters are one syllable
        # Remove punctuation and spaces
        clean_text = ''.join(c for c in text if c.isalnum())
        return len(clean_text)
    
    def _get_character_speech_pattern(self, character: Dict[str, Any]) -> str:
        """Get character-specific speech pattern."""
        
        personality = character.get("personality", [])
        age = character.get("age", 18)
        
        if age < 16:
            return "youthful"
        elif any(trait in ["冷静", "知的", "完璧主義"] for trait in personality):
            return "formal"
        elif any(trait in ["明るい", "元気", "カジュアル"] for trait in personality):
            return "casual"
        else:
            return "standard"
    
    async def _generate_panel_narration(
        self,
        scene: Dict[str, Any],
        panel_spec: Dict[str, Any],
        dialogue_elements: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Generate narration for panel if needed."""
        
        # Check if narration is needed
        scene_purpose = scene.get("purpose", "")
        camera_angle = panel_spec.get("camera_angle", "medium_shot")
        
        # Narration is useful for:
        # 1. Scene establishment (wide shots)
        # 2. Time/location changes
        # 3. Internal thoughts/feelings
        # 4. Action description
        
        needs_narration = (
            camera_angle in ["wide_shot", "bird_eye"] or
            "introduction" in scene_purpose or
            len(dialogue_elements) == 0
        )
        
        if not needs_narration:
            return None
        
        # Generate appropriate narration
        if "introduction" in scene_purpose:
            narration_text = self._generate_setting_narration(scene)
        elif camera_angle in ["wide_shot", "bird_eye"]:
            narration_text = self._generate_scene_description_narration(scene)
        elif len(dialogue_elements) == 0:
            narration_text = self._generate_action_narration(scene)
        else:
            return None
        
        if narration_text:
            return {
                "text": narration_text,
                "position": "top",  # Default position
                "style": "descriptive",
                "importance": "medium",
                "text_length": len(narration_text)
            }
        
        return None
    
    def _generate_setting_narration(self, scene: Dict[str, Any]) -> str:
        """Generate setting/location narration."""
        return "物語の舞台..."
    
    def _generate_scene_description_narration(self, scene: Dict[str, Any]) -> str:
        """Generate scene description narration."""
        scene_purpose = scene.get("purpose", "")
        if "conflict" in scene_purpose:
            return "緊迫した状況が続く..."
        else:
            return "静かな時が流れる..."
    
    def _generate_action_narration(self, scene: Dict[str, Any]) -> str:
        """Generate action description narration."""
        pacing = scene.get("pacing", "medium")
        if pacing == "fast":
            return "その時！"
        else:
            return "そして..."
    
    def _estimate_panel_reading_time(
        self,
        dialogue_elements: List[Dict[str, Any]],
        narration: Optional[Dict[str, Any]]
    ) -> float:
        """Estimate reading time for panel in seconds."""
        
        total_syllables = sum(elem.get("estimated_syllables", 0) for elem in dialogue_elements)
        
        if narration:
            total_syllables += self._estimate_syllables(narration.get("text", ""))
        
        # Average reading speed: 3-4 syllables per second for manga
        reading_speed = 3.5
        base_time = total_syllables / reading_speed
        
        # Add processing time for dialogue bubbles
        bubble_processing = len(dialogue_elements) * 0.5
        
        return round(base_time + bubble_processing, 1)
    
    async def _create_text_placements(
        self,
        dialogue_content: List[Dict[str, Any]],
        phase4_result: Dict[str, Any],
        phase5_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create text placement specifications for each dialogue element."""
        
        text_placements = []
        
        # Get panel and image information
        panel_specifications = phase4_result.get("panel_specifications", [])
        generated_images = phase5_result.get("generated_images", [])
        scene_image_mapping = phase5_result.get("scene_image_mapping", {})
        
        for panel_dialogue in dialogue_content:
            panel_id = panel_dialogue.get("panel_id", "")
            
            # Find panel specification
            panel_spec = next(
                (spec for spec in panel_specifications if spec.get("panel_id") == panel_id),
                {}
            )
            
            # Find generated image
            panel_image = next(
                (img for img in generated_images if img.panel_id == panel_id),
                None
            )
            
            # Create placements for dialogue elements
            dialogue_elements = panel_dialogue.get("dialogue_elements", [])
            for i, dialogue_elem in enumerate(dialogue_elements):
                placement = await self._create_dialogue_placement(
                    dialogue_elem, panel_spec, panel_image, i, len(dialogue_elements)
                )
                text_placements.append(placement)
            
            # Create placement for narration if exists
            narration = panel_dialogue.get("narration")
            if narration:
                narration_placement = await self._create_narration_placement(
                    narration, panel_spec, panel_image, len(dialogue_elements)
                )
                text_placements.append(narration_placement)
        
        return text_placements
    
    async def _create_dialogue_placement(
        self,
        dialogue_element: Dict[str, Any],
        panel_spec: Dict[str, Any],
        panel_image: Any,
        dialogue_index: int,
        total_dialogues: int
    ) -> Dict[str, Any]:
        """Create placement specification for dialogue element."""
        
        panel_id = panel_spec.get("panel_id", "")
        camera_angle = panel_spec.get("camera_angle", "medium_shot")
        panel_size = panel_spec.get("size", "medium")
        
        # Determine optimal position
        position = await self._determine_dialogue_position(
            camera_angle, panel_size, dialogue_index, total_dialogues
        )
        
        # Determine bubble style
        dialogue_type = dialogue_element.get("dialogue_type", "speech")
        bubble_style = self.dialogue_types[dialogue_type]["bubble_style"]
        
        # Calculate text area dimensions
        text_area = await self._calculate_text_area(
            dialogue_element.get("text", ""),
            bubble_style,
            panel_spec
        )
        
        placement = {
            "panel_id": panel_id,
            "element_type": "dialogue",
            "speaker": dialogue_element.get("speaker"),
            "text_content": dialogue_element.get("text"),
            "dialogue_type": dialogue_type,
            "position": position,
            "bubble_style": bubble_style,
            "text_area": text_area,
            "reading_order": dialogue_index + 1,
            "importance": dialogue_element.get("importance", "medium"),
            "speech_pattern": dialogue_element.get("speech_pattern", "standard"),
            "emotion": dialogue_element.get("emotion", "neutral"),
            "tail_direction": await self._determine_tail_direction(
                position, panel_spec.get("characters", []), dialogue_element.get("speaker")
            )
        }
        
        return placement
    
    async def _create_narration_placement(
        self,
        narration: Dict[str, Any],
        panel_spec: Dict[str, Any],
        panel_image: Any,
        existing_dialogues: int
    ) -> Dict[str, Any]:
        """Create placement specification for narration."""
        
        panel_id = panel_spec.get("panel_id", "")
        
        # Narration typically goes at top or bottom
        position = narration.get("position", "top")
        
        # Calculate text area for narration box
        text_area = await self._calculate_text_area(
            narration.get("text", ""),
            "rectangular_box",
            panel_spec
        )
        
        placement = {
            "panel_id": panel_id,
            "element_type": "narration",
            "speaker": None,
            "text_content": narration.get("text"),
            "dialogue_type": "narration",
            "position": position,
            "bubble_style": "rectangular_box",
            "text_area": text_area,
            "reading_order": existing_dialogues + 1,
            "importance": narration.get("importance", "medium"),
            "narration_style": narration.get("style", "descriptive")
        }
        
        return placement
    
    async def _determine_dialogue_position(
        self,
        camera_angle: str,
        panel_size: str,
        dialogue_index: int,
        total_dialogues: int
    ) -> Dict[str, float]:
        """Determine optimal position for dialogue bubble."""
        
        # Get placement rules for camera angle
        rules = self.placement_rules.get(camera_angle, self.placement_rules["medium_shot"])
        preferred_positions = rules["preferred_positions"]
        
        if total_dialogues == 1:
            # Single dialogue - use best position
            if "top" in preferred_positions:
                return {"x": 0.7, "y": 0.2, "anchor": "top_right"}
            elif "sides" in preferred_positions:
                return {"x": 0.1, "y": 0.3, "anchor": "left"}
            else:
                return {"x": 0.5, "y": 0.8, "anchor": "bottom"}
        
        else:
            # Multiple dialogues - distribute across preferred positions
            if dialogue_index == 0:
                # First dialogue gets priority position
                return {"x": 0.7, "y": 0.2, "anchor": "top_right"}
            elif dialogue_index == 1:
                # Second dialogue on opposite side/position
                return {"x": 0.3, "y": 0.7, "anchor": "bottom_left"}
            else:
                # Additional dialogues fill remaining space
                return {"x": 0.5, "y": 0.5, "anchor": "center"}
    
    async def _calculate_text_area(
        self,
        text: str,
        bubble_style: str,
        panel_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate text area dimensions and properties."""
        
        # Estimate text dimensions based on length and style
        text_length = len(text)
        estimated_lines = max(1, text_length // 12)  # ~12 chars per line
        
        # Base dimensions (relative to panel)
        if bubble_style == "rectangular_box":
            # Narration boxes are typically wider and shorter
            width_ratio = min(0.8, text_length * 0.03)
            height_ratio = max(0.1, estimated_lines * 0.05)
        else:
            # Speech bubbles are more circular/oval
            width_ratio = min(0.4, text_length * 0.025)
            height_ratio = max(0.15, estimated_lines * 0.08)
        
        # Adjust for panel size
        panel_size = panel_spec.get("size", "medium")
        size_multiplier = {"small": 0.8, "medium": 1.0, "large": 1.2, "splash": 1.5}.get(panel_size, 1.0)
        
        text_area = {
            "width_ratio": width_ratio * size_multiplier,
            "height_ratio": height_ratio * size_multiplier,
            "estimated_lines": estimated_lines,
            "font_size": self._calculate_font_size(text_length, panel_size),
            "padding": {"top": 8, "bottom": 8, "left": 12, "right": 12},
            "text_alignment": "center"
        }
        
        return text_area
    
    def _calculate_font_size(self, text_length: int, panel_size: str) -> int:
        """Calculate appropriate font size."""
        
        base_sizes = {"small": 10, "medium": 12, "large": 14, "splash": 16}
        base_size = base_sizes.get(panel_size, 12)
        
        # Adjust for text length
        if text_length > 20:
            base_size -= 1
        elif text_length < 10:
            base_size += 1
        
        return max(8, min(18, base_size))
    
    async def _determine_tail_direction(
        self,
        bubble_position: Dict[str, float],
        panel_characters: List[Dict[str, Any]],
        speaker: Optional[str]
    ) -> str:
        """Determine direction for speech bubble tail."""
        
        if not speaker or not panel_characters:
            return "down"
        
        # Find speaker in panel characters
        speaker_data = next(
            (char for char in panel_characters if char.get("name") == speaker),
            {}
        )
        
        # Simple tail direction based on bubble position
        bubble_x = bubble_position.get("x", 0.5)
        bubble_y = bubble_position.get("y", 0.5)
        
        if bubble_y < 0.3:  # Bubble at top
            return "down"
        elif bubble_y > 0.7:  # Bubble at bottom
            return "up"
        elif bubble_x < 0.3:  # Bubble at left
            return "right"
        elif bubble_x > 0.7:  # Bubble at right
            return "left"
        else:
            return "down"  # Default
    
    async def _generate_typography_specifications(
        self,
        text_placements: List[Dict[str, Any]],
        genre: str
    ) -> Dict[str, Any]:
        """Generate typography specifications for the manga."""
        
        # Genre-specific typography styles
        genre_typography = {
            "action": {
                "primary_font": "bold_manga_font",
                "emphasis_style": "heavy_bold",
                "line_weight": "thick"
            },
            "romance": {
                "primary_font": "elegant_manga_font",
                "emphasis_style": "italic",
                "line_weight": "medium"
            },
            "mystery": {
                "primary_font": "atmospheric_manga_font",
                "emphasis_style": "subtle_bold",
                "line_weight": "varied"
            },
            "slice_of_life": {
                "primary_font": "friendly_manga_font",
                "emphasis_style": "gentle_bold",
                "line_weight": "light"
            }
        }
        
        base_typography = genre_typography.get(genre, genre_typography["slice_of_life"])
        
        # Analyze text placements to determine specifications
        dialogue_specs = []
        narration_specs = []
        
        for placement in text_placements:
            if placement.get("element_type") == "dialogue":
                spec = self._create_dialogue_typography_spec(placement, base_typography)
                dialogue_specs.append(spec)
            else:
                spec = self._create_narration_typography_spec(placement, base_typography)
                narration_specs.append(spec)
        
        typography_specs = {
            "base_typography": base_typography,
            "dialogue_specifications": dialogue_specs,
            "narration_specifications": narration_specs,
            "japanese_text_rules": self.japanese_text_rules,
            "font_fallbacks": ["Noto Sans CJK JP", "Hiragino Kaku Gothic Pro", "MS Gothic"],
            "special_characters": {
                "emphasis_marks": ["！", "？", "…"],
                "pause_indicators": ["……", "..."],
                "emotional_indicators": ["♪", "♡", "★"]
            }
        }
        
        return typography_specs
    
    def _create_dialogue_typography_spec(
        self, placement: Dict[str, Any], base_typography: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create typography specification for dialogue."""
        
        dialogue_type = placement.get("dialogue_type", "speech")
        importance = placement.get("importance", "medium")
        emotion = placement.get("emotion", "neutral")
        
        # Base font settings
        font_spec = base_typography.copy()
        
        # Adjust based on dialogue type
        if dialogue_type == "shout":
            font_spec.update({
                "font_weight": "bold",
                "font_size_modifier": 1.2,
                "letter_spacing": "wide"
            })
        elif dialogue_type == "whisper":
            font_spec.update({
                "font_weight": "light",
                "font_size_modifier": 0.8,
                "letter_spacing": "tight"
            })
        elif dialogue_type == "thought":
            font_spec.update({
                "font_style": "italic",
                "font_size_modifier": 0.9,
                "opacity": 0.8
            })
        
        # Adjust based on importance
        if importance == "high":
            font_spec["font_size_modifier"] = font_spec.get("font_size_modifier", 1.0) * 1.1
        elif importance == "low":
            font_spec["font_size_modifier"] = font_spec.get("font_size_modifier", 1.0) * 0.9
        
        return {
            "panel_id": placement.get("panel_id"),
            "element_id": f"{placement.get('panel_id')}_{placement.get('speaker', 'unknown')}",
            "typography": font_spec,
            "text_effects": self._determine_text_effects(emotion, dialogue_type)
        }
    
    def _create_narration_typography_spec(
        self, placement: Dict[str, Any], base_typography: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create typography specification for narration."""
        
        narration_style = placement.get("narration_style", "descriptive")
        
        font_spec = base_typography.copy()
        font_spec.update({
            "font_weight": "normal",
            "font_size_modifier": 0.85,
            "line_height": 1.3,
            "text_alignment": "left"
        })
        
        return {
            "panel_id": placement.get("panel_id"),
            "element_id": f"{placement.get('panel_id')}_narration",
            "typography": font_spec,
            "box_style": "clean_rectangle"
        }
    
    def _determine_text_effects(self, emotion: str, dialogue_type: str) -> List[str]:
        """Determine text effects based on emotion and type."""
        
        effects = []
        
        if emotion in ["tension", "climax"] and dialogue_type == "shout":
            effects.append("bold_outline")
        
        if emotion in ["anxiety", "fear"]:
            effects.append("slight_tremor")
        
        if dialogue_type == "thought":
            effects.append("soft_glow")
        
        if emotion == "satisfaction":
            effects.append("warm_tone")
        
        return effects
    
    async def _optimize_readability(
        self,
        text_placements: List[Dict[str, Any]],
        typography_specs: Dict[str, Any],
        phase4_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize text placements for readability."""
        
        # Analyze potential readability issues
        readability_issues = []
        optimization_suggestions = []
        
        # Group placements by panel
        panel_groups = {}
        for placement in text_placements:
            panel_id = placement.get("panel_id", "")
            if panel_id not in panel_groups:
                panel_groups[panel_id] = []
            panel_groups[panel_id].append(placement)
        
        # Analyze each panel
        for panel_id, placements in panel_groups.items():
            panel_analysis = await self._analyze_panel_readability(panel_id, placements)
            readability_issues.extend(panel_analysis["issues"])
            optimization_suggestions.extend(panel_analysis["suggestions"])
        
        # Calculate overall readability score
        readability_score = self._calculate_panel_readability_score(readability_issues, text_placements)
        
        readability_optimization = {
            "overall_readability_score": readability_score,
            "identified_issues": readability_issues,
            "optimization_suggestions": optimization_suggestions,
            "reading_flow_analysis": await self._analyze_reading_flow(text_placements),
            "text_density_analysis": self._analyze_text_density(text_placements),
            "visual_interference_analysis": self._analyze_visual_interference(
                text_placements, phase4_result
            )
        }
        
        return readability_optimization
    
    async def _analyze_panel_readability(
        self, panel_id: str, placements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze readability for a single panel."""
        
        issues = []
        suggestions = []
        
        # Check text density
        total_text_length = sum(len(p.get("text_content", "")) for p in placements)
        if total_text_length > 100:
            issues.append(f"Panel {panel_id}: 文字密度が高すぎます")
            suggestions.append(f"Panel {panel_id}: テキスト量の削減を検討")
        
        # Check reading order clarity
        reading_orders = [p.get("reading_order", 0) for p in placements]
        if len(set(reading_orders)) != len(reading_orders):
            issues.append(f"Panel {panel_id}: 読み順が不明確です")
            suggestions.append(f"Panel {panel_id}: 読み順の明確化")
        
        # Check position conflicts
        positions = [(p.get("position", {}).get("x", 0), p.get("position", {}).get("y", 0)) for p in placements]
        for i, pos1 in enumerate(positions):
            for j, pos2 in enumerate(positions[i+1:], i+1):
                if abs(pos1[0] - pos2[0]) < 0.2 and abs(pos1[1] - pos2[1]) < 0.2:
                    issues.append(f"Panel {panel_id}: テキスト要素が重複する可能性")
                    suggestions.append(f"Panel {panel_id}: テキスト配置の調整")
                    break
        
        return {"issues": issues, "suggestions": suggestions}
    
    def _calculate_panel_readability_score(
        self, issues: List[str], text_placements: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall readability score."""
        
        if not text_placements:
            return 1.0
        
        # Start with perfect score
        score = 1.0
        
        # Deduct for each issue type
        issue_penalties = {
            "文字密度": 0.15,
            "読み順": 0.2,
            "重複": 0.1,
            "視覚的干渉": 0.1
        }
        
        for issue in issues:
            for issue_type, penalty in issue_penalties.items():
                if issue_type in issue:
                    score -= penalty
                    break
        
        return max(0.0, round(score, 2))
    
    async def _analyze_reading_flow(self, text_placements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze reading flow across panels."""
        
        # Group by panel and sort by reading order
        panel_flows = {}
        for placement in text_placements:
            panel_id = placement.get("panel_id", "")
            if panel_id not in panel_flows:
                panel_flows[panel_id] = []
            panel_flows[panel_id].append(placement)
        
        # Sort each panel by reading order
        for panel_id in panel_flows:
            panel_flows[panel_id].sort(key=lambda x: x.get("reading_order", 0))
        
        flow_analysis = {
            "panels_with_clear_flow": 0,
            "panels_with_issues": 0,
            "average_elements_per_panel": 0,
            "flow_recommendations": []
        }
        
        total_elements = 0
        for panel_id, placements in panel_flows.items():
            total_elements += len(placements)
            
            # Check if reading order is clear
            orders = [p.get("reading_order", 0) for p in placements]
            if orders == sorted(orders) and len(set(orders)) == len(orders):
                flow_analysis["panels_with_clear_flow"] += 1
            else:
                flow_analysis["panels_with_issues"] += 1
                flow_analysis["flow_recommendations"].append(
                    f"Panel {panel_id}: 読み順の明確化が必要"
                )
        
        if panel_flows:
            flow_analysis["average_elements_per_panel"] = round(
                total_elements / len(panel_flows), 1
            )
        
        return flow_analysis
    
    def _analyze_text_density(self, text_placements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze text density distribution."""
        
        panel_densities = {}
        
        for placement in text_placements:
            panel_id = placement.get("panel_id", "")
            text_length = len(placement.get("text_content", ""))
            
            if panel_id not in panel_densities:
                panel_densities[panel_id] = 0
            panel_densities[panel_id] += text_length
        
        densities = list(panel_densities.values())
        
        density_analysis = {
            "average_text_per_panel": sum(densities) / len(densities) if densities else 0,
            "max_text_panel": max(densities) if densities else 0,
            "min_text_panel": min(densities) if densities else 0,
            "density_variance": self._calculate_variance(densities),
            "high_density_panels": len([d for d in densities if d > 80]),
            "recommended_max_density": 60
        }
        
        return density_analysis
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return round(variance, 2)
    
    def _analyze_visual_interference(
        self, text_placements: List[Dict[str, Any]], phase4_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze potential visual interference between text and images."""
        
        # Get panel specifications
        panel_specifications = phase4_result.get("panel_specifications", [])
        
        interference_analysis = {
            "potential_conflicts": [],
            "safe_placements": 0,
            "risky_placements": 0,
            "recommendations": []
        }
        
        for placement in text_placements:
            panel_id = placement.get("panel_id", "")
            position = placement.get("position", {})
            
            # Find corresponding panel spec
            panel_spec = next(
                (spec for spec in panel_specifications if spec.get("panel_id") == panel_id),
                {}
            )
            
            # Check for potential conflicts
            camera_angle = panel_spec.get("camera_angle", "medium_shot")
            focus_element = panel_spec.get("focus_element", "")
            
            # Analyze interference risk
            risk_level = self._assess_interference_risk(position, camera_angle, focus_element)
            
            if risk_level == "high":
                interference_analysis["risky_placements"] += 1
                interference_analysis["potential_conflicts"].append(
                    f"Panel {panel_id}: テキストが主要な視覚要素と干渉する可能性"
                )
                interference_analysis["recommendations"].append(
                    f"Panel {panel_id}: テキスト位置の調整を推奨"
                )
            else:
                interference_analysis["safe_placements"] += 1
        
        return interference_analysis
    
    def _assess_interference_risk(
        self, position: Dict[str, float], camera_angle: str, focus_element: str
    ) -> str:
        """Assess interference risk between text and image elements."""
        
        pos_x = position.get("x", 0.5)
        pos_y = position.get("y", 0.5)
        
        # High risk areas based on camera angle
        if camera_angle in ["close_up", "extreme_close_up"]:
            # Face area is typically center
            if 0.3 <= pos_x <= 0.7 and 0.2 <= pos_y <= 0.8:
                return "high"
        elif "character" in focus_element and 0.2 <= pos_x <= 0.8 and 0.3 <= pos_y <= 0.7:
            return "medium"
        
        return "low"
    
    async def _generate_bubble_designs(
        self, text_placements: List[Dict[str, Any]], dialogue_content: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate bubble design specifications."""
        
        bubble_designs = []
        
        for placement in text_placements:
            if placement.get("element_type") == "dialogue":
                design = await self._create_bubble_design(placement)
                bubble_designs.append(design)
            elif placement.get("element_type") == "narration":
                design = await self._create_narration_box_design(placement)
                bubble_designs.append(design)
        
        return bubble_designs
    
    async def _create_bubble_design(self, placement: Dict[str, Any]) -> Dict[str, Any]:
        """Create bubble design specification."""
        
        bubble_style = placement.get("bubble_style", "standard_speech")
        dialogue_type = placement.get("dialogue_type", "speech")
        emotion = placement.get("emotion", "neutral")
        
        # Base bubble design
        design = {
            "panel_id": placement.get("panel_id"),
            "element_id": f"{placement.get('panel_id')}_{placement.get('speaker', 'unknown')}",
            "bubble_type": bubble_style,
            "shape": self._determine_bubble_shape(bubble_style),
            "border": self._determine_bubble_border(dialogue_type, emotion),
            "fill": self._determine_bubble_fill(dialogue_type),
            "tail": {
                "style": self.dialogue_types[dialogue_type]["tail_style"],
                "direction": placement.get("tail_direction", "down"),
                "length": "medium"
            },
            "effects": self._determine_bubble_effects(emotion, dialogue_type)
        }
        
        return design
    
    def _determine_bubble_shape(self, bubble_style: str) -> str:
        """Determine bubble shape based on style."""
        
        shape_mapping = {
            "standard_speech": "oval",
            "cloud_thought": "cloud",
            "jagged_excitement": "jagged",
            "dotted_soft": "oval",
            "rectangular_box": "rectangle"
        }
        
        return shape_mapping.get(bubble_style, "oval")
    
    def _determine_bubble_border(self, dialogue_type: str, emotion: str) -> Dict[str, Any]:
        """Determine bubble border properties."""
        
        if dialogue_type == "shout":
            return {"width": 3, "style": "solid", "color": "black"}
        elif dialogue_type == "whisper":
            return {"width": 1, "style": "dotted", "color": "gray"}
        elif dialogue_type == "thought":
            return {"width": 1, "style": "dashed", "color": "gray"}
        else:
            return {"width": 2, "style": "solid", "color": "black"}
    
    def _determine_bubble_fill(self, dialogue_type: str) -> Dict[str, Any]:
        """Determine bubble fill properties."""
        
        if dialogue_type == "thought":
            return {"color": "white", "opacity": 0.9}
        elif dialogue_type == "narration":
            return {"color": "lightgray", "opacity": 1.0}
        else:
            return {"color": "white", "opacity": 1.0}
    
    def _determine_bubble_effects(self, emotion: str, dialogue_type: str) -> List[str]:
        """Determine special effects for bubble."""
        
        effects = []
        
        if emotion in ["tension", "climax"] and dialogue_type == "shout":
            effects.append("vibration_effect")
        
        if emotion == "anxiety":
            effects.append("slight_tremor")
        
        if dialogue_type == "thought":
            effects.append("soft_shadow")
        
        return effects
    
    async def _create_narration_box_design(self, placement: Dict[str, Any]) -> Dict[str, Any]:
        """Create narration box design specification."""
        
        design = {
            "panel_id": placement.get("panel_id"),
            "element_id": f"{placement.get('panel_id')}_narration",
            "box_type": "narration_box",
            "shape": "rectangle",
            "border": {"width": 1, "style": "solid", "color": "black"},
            "fill": {"color": "white", "opacity": 1.0},
            "corner_radius": 0,
            "effects": ["clean_edges"]
        }
        
        return design
    
    async def _analyze_dialogue_flow(
        self,
        dialogue_content: List[Dict[str, Any]],
        text_placements: List[Dict[str, Any]],
        phase3_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze dialogue flow and narrative progression."""
        
        # Get scene information
        scene_breakdown = phase3_result.get("scene_breakdown", [])
        
        # Analyze dialogue distribution across scenes
        scene_dialogue_map = {}
        for dialogue in dialogue_content:
            scene_number = dialogue.get("scene_number", 0)
            if scene_number not in scene_dialogue_map:
                scene_dialogue_map[scene_number] = []
            scene_dialogue_map[scene_number].extend(dialogue.get("dialogue_elements", []))
        
        # Analyze character speaking patterns
        character_dialogue_count = {}
        for dialogue in dialogue_content:
            for element in dialogue.get("dialogue_elements", []):
                speaker = element.get("speaker", "unknown")
                character_dialogue_count[speaker] = character_dialogue_count.get(speaker, 0) + 1
        
        # Analyze dialogue types distribution
        dialogue_types_count = {}
        for dialogue in dialogue_content:
            for element in dialogue.get("dialogue_elements", []):
                dialogue_type = element.get("dialogue_type", "speech")
                dialogue_types_count[dialogue_type] = dialogue_types_count.get(dialogue_type, 0) + 1
        
        dialogue_flow = {
            "scene_dialogue_distribution": scene_dialogue_map,
            "character_speaking_balance": character_dialogue_count,
            "dialogue_types_distribution": dialogue_types_count,
            "total_dialogue_elements": sum(
                len(d.get("dialogue_elements", [])) for d in dialogue_content
            ),
            "average_dialogue_per_panel": self._calculate_average_dialogue_per_panel(dialogue_content),
            "narrative_progression_score": self._calculate_narrative_progression_score(
                scene_dialogue_map, scene_breakdown
            ),
            "character_voice_consistency": self._analyze_character_voice_consistency(dialogue_content),
            "dialogue_pacing_analysis": self._analyze_dialogue_pacing(dialogue_content, scene_breakdown)
        }
        
        return dialogue_flow
    
    def _calculate_average_dialogue_per_panel(self, dialogue_content: List[Dict[str, Any]]) -> float:
        """Calculate average dialogue elements per panel."""
        
        if not dialogue_content:
            return 0.0
        
        total_elements = sum(len(d.get("dialogue_elements", [])) for d in dialogue_content)
        return round(total_elements / len(dialogue_content), 1)
    
    def _calculate_narrative_progression_score(
        self, scene_dialogue_map: Dict[int, List], scene_breakdown: List[Dict[str, Any]]
    ) -> float:
        """Calculate how well dialogue supports narrative progression."""
        
        if not scene_dialogue_map or not scene_breakdown:
            return 0.5
        
        progression_score = 0.0
        total_scenes = len(scene_breakdown)
        
        for scene in scene_breakdown:
            scene_number = scene.get("scene_number", 0)
            scene_purpose = scene.get("purpose", "")
            scene_dialogues = scene_dialogue_map.get(scene_number, [])
            
            # Score based on dialogue presence in key scenes
            if scene_dialogues:
                if "climax" in scene_purpose or "conflict" in scene_purpose:
                    progression_score += 1.0  # High importance scenes should have dialogue
                elif "introduction" in scene_purpose:
                    progression_score += 0.8
                else:
                    progression_score += 0.6
            else:
                # Missing dialogue might be okay for some scene types
                if "climax" in scene_purpose:
                    progression_score += 0.2  # Penalty for missing dialogue in climax
                else:
                    progression_score += 0.4
        
        return round(progression_score / total_scenes, 2) if total_scenes > 0 else 0.5
    
    def _analyze_character_voice_consistency(
        self, dialogue_content: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze consistency of character voices."""
        
        character_speech_patterns = {}
        
        for dialogue in dialogue_content:
            for element in dialogue.get("dialogue_elements", []):
                speaker = element.get("speaker", "unknown")
                speech_pattern = element.get("speech_pattern", "standard")
                
                if speaker not in character_speech_patterns:
                    character_speech_patterns[speaker] = []
                character_speech_patterns[speaker].append(speech_pattern)
        
        # Calculate consistency for each character
        consistency_scores = {}
        for character, patterns in character_speech_patterns.items():
            if len(patterns) > 1:
                # Calculate consistency based on pattern uniformity
                most_common_pattern = max(set(patterns), key=patterns.count)
                consistency_ratio = patterns.count(most_common_pattern) / len(patterns)
                consistency_scores[character] = round(consistency_ratio, 2)
            else:
                consistency_scores[character] = 1.0  # Single instance is consistent
        
        overall_consistency = (
            sum(consistency_scores.values()) / len(consistency_scores) 
            if consistency_scores else 1.0
        )
        
        return {
            "character_consistency_scores": consistency_scores,
            "overall_voice_consistency": round(overall_consistency, 2),
            "characters_analyzed": len(character_speech_patterns),
            "consistency_issues": [
                f"{char}: 一貫性スコア {score:.2f}" 
                for char, score in consistency_scores.items() if score < 0.8
            ]
        }
    
    def _analyze_dialogue_pacing(
        self, dialogue_content: List[Dict[str, Any]], scene_breakdown: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze dialogue pacing alignment with scene pacing."""
        
        pacing_alignment = []
        
        for dialogue in dialogue_content:
            scene_number = dialogue.get("scene_number", 0)
            dialogue_elements = dialogue.get("dialogue_elements", [])
            
            # Find corresponding scene
            scene = next(
                (s for s in scene_breakdown if s.get("scene_number") == scene_number),
                {}
            )
            
            scene_pacing = scene.get("pacing", "medium")
            
            # Calculate dialogue density for this panel
            total_text_length = sum(len(elem.get("text", "")) for elem in dialogue_elements)
            dialogue_count = len(dialogue_elements)
            
            # Determine if dialogue pacing matches scene pacing
            if scene_pacing == "fast":
                # Fast scenes should have shorter, fewer dialogues
                appropriate = dialogue_count <= 2 and total_text_length <= 40
            elif scene_pacing == "slow":
                # Slow scenes can have longer, more dialogues
                appropriate = True  # More flexible
            else:
                # Medium pacing
                appropriate = dialogue_count <= 3 and total_text_length <= 80
            
            pacing_alignment.append({
                "scene_number": scene_number,
                "scene_pacing": scene_pacing,
                "dialogue_count": dialogue_count,
                "total_text_length": total_text_length,
                "appropriate_pacing": appropriate
            })
        
        # Calculate overall pacing alignment
        appropriate_count = sum(1 for p in pacing_alignment if p["appropriate_pacing"])
        pacing_score = appropriate_count / len(pacing_alignment) if pacing_alignment else 1.0
        
        return {
            "pacing_alignment_details": pacing_alignment,
            "pacing_alignment_score": round(pacing_score, 2),
            "pacing_recommendations": self._generate_pacing_recommendations(pacing_alignment)
        }
    
    def _generate_pacing_recommendations(self, pacing_alignment: List[Dict[str, Any]]) -> List[str]:
        """Generate pacing improvement recommendations."""
        
        recommendations = []
        
        for alignment in pacing_alignment:
            if not alignment["appropriate_pacing"]:
                scene_num = alignment["scene_number"]
                scene_pacing = alignment["scene_pacing"]
                dialogue_count = alignment["dialogue_count"]
                text_length = alignment["total_text_length"]
                
                if scene_pacing == "fast" and dialogue_count > 2:
                    recommendations.append(f"シーン{scene_num}: 高速ペースに合わせてセリフ数を削減")
                
                if text_length > 80:
                    recommendations.append(f"シーン{scene_num}: テキスト量を削減して読みやすさを向上")
        
        if not recommendations:
            recommendations.append("現在のセリフペーシングは適切です")
        
        return recommendations
    
    def _calculate_dialogue_density(
        self, text_placements: List[Dict[str, Any]], phase4_result: Dict[str, Any]
    ) -> float:
        """Calculate dialogue density score."""
        
        panel_specifications = phase4_result.get("panel_specifications", [])
        total_panels = len(panel_specifications)
        
        if total_panels == 0:
            return 0.0
        
        # Calculate average text elements per panel
        panels_with_text = set(p.get("panel_id") for p in text_placements)
        text_coverage = len(panels_with_text) / total_panels
        
        # Calculate average text length
        total_text_length = sum(len(p.get("text_content", "")) for p in text_placements)
        average_text_per_panel = total_text_length / total_panels if total_panels > 0 else 0
        
        # Normalize to 0-1 scale
        density_score = min(1.0, (text_coverage * 0.6) + (min(average_text_per_panel / 100, 1.0) * 0.4))
        
        return round(density_score, 2)
    
    def _calculate_readability_score(
        self, text_placements: List[Dict[str, Any]], readability_optimization: Dict[str, Any]
    ) -> float:
        """Calculate overall readability score."""
        
        base_score = readability_optimization.get("overall_readability_score", 0.8)
        
        # Adjust based on text density
        density_analysis = readability_optimization.get("text_density_analysis", {})
        avg_density = density_analysis.get("average_text_per_panel", 50)
        
        if avg_density > 80:
            base_score -= 0.1
        elif avg_density > 60:
            base_score -= 0.05
        
        # Adjust based on visual interference
        interference_analysis = readability_optimization.get("visual_interference_analysis", {})
        risky_placements = interference_analysis.get("risky_placements", 0)
        total_placements = len(text_placements)
        
        if total_placements > 0:
            risk_ratio = risky_placements / total_placements
            base_score -= risk_ratio * 0.15
        
        return round(max(0.0, min(1.0, base_score)), 2)
    
    def _calculate_integration_score(
        self, text_placements: List[Dict[str, Any]], phase5_result: Dict[str, Any]
    ) -> float:
        """Calculate text-image integration score."""
        
        generated_images = phase5_result.get("generated_images", [])
        successful_images = [img for img in generated_images if img.success]
        
        if not successful_images or not text_placements:
            return 0.5
        
        # Calculate coverage - how many images have associated text
        images_with_text = set()
        for placement in text_placements:
            panel_id = placement.get("panel_id", "")
            # Find corresponding image
            for img in successful_images:
                if img.panel_id == panel_id:
                    images_with_text.add(panel_id)
                    break
        
        coverage_score = len(images_with_text) / len(successful_images)
        
        # Assess placement quality based on panel specifications
        placement_quality_scores = []
        for placement in text_placements:
            # Simple quality assessment based on position
            position = placement.get("position", {})
            pos_x = position.get("x", 0.5)
            pos_y = position.get("y", 0.5)
            
            # Avoid center positions for better integration
            if 0.2 <= pos_x <= 0.8 and 0.3 <= pos_y <= 0.7:
                quality_score = 0.6  # Moderate quality - might interfere
            else:
                quality_score = 0.9  # Good quality - safer positions
            
            placement_quality_scores.append(quality_score)
        
        average_quality = (
            sum(placement_quality_scores) / len(placement_quality_scores) 
            if placement_quality_scores else 0.5
        )
        
        # Combine coverage and quality
        integration_score = (coverage_score * 0.6) + (average_quality * 0.4)
        
        return round(integration_score, 2)

    def _parse_ai_response(self, ai_content: str) -> Dict[str, Any]:
        """Parse Gemini Pro JSON response into structured data."""
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
            return {}
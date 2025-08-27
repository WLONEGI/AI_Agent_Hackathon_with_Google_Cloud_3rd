"""Phase 2: Character Design and Visual Generation Agent."""

from typing import Dict, Any, Optional, List
from uuid import UUID
import asyncio
import json

from app.agents.base_agent import BaseAgent
from app.core.config import settings
from app.services.vertex_ai_service import VertexAIService


class Phase2CharacterAgent(BaseAgent):
    """Agent for character design and simple visual generation."""
    
    def __init__(self):
        super().__init__(
            phase_number=2,
            phase_name="キャラクター設定・簡易ビジュアル生成",
            timeout_seconds=settings.phase_timeouts[2]
        )
        
        # Vertex AI サービス初期化
        self.vertex_ai = VertexAIService()
        
        self.character_archetypes = {
            "protagonist": ["主人公", "ヒーロー", "リーダー"],
            "sidekick": ["相棒", "親友", "サポーター"],
            "mentor": ["師匠", "先生", "ガイド"],
            "antagonist": ["敵", "ライバル", "対立者"],
            "love_interest": ["恋人", "想い人", "パートナー"]
        }
        
        self.visual_styles = {
            "shounen": {"eyes": "large", "proportions": "dynamic", "detail": "medium"},
            "shoujo": {"eyes": "sparkly", "proportions": "elegant", "detail": "high"},
            "seinen": {"eyes": "realistic", "proportions": "natural", "detail": "very_high"},
            "kodomo": {"eyes": "simple", "proportions": "chibi", "detail": "low"}
        }
    
    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: UUID,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Process character design based on concept analysis.
        
        Args:
            input_data: Contains original text
            session_id: Current session ID
            previous_results: Phase 1 results with themes and genre
            
        Returns:
            Character designs with visual descriptions
        """
        
        phase1_result = previous_results.get(1, {}) if previous_results else {}
        
        # Extract relevant information from Phase 1
        genre = phase1_result.get("genre", "general")
        themes = phase1_result.get("themes", [])
        world_setting = phase1_result.get("world_setting", {})
        target_audience = phase1_result.get("target_audience", "general")
        
        # Generate prompt for AI
        prompt = await self.generate_prompt(
            {
                "text": input_data.get("text", ""),
                "genre": genre,
                "themes": themes,
                "world_setting": world_setting
            },
            previous_results
        )
        
        # Call Gemini Pro for AI character design
        try:
            ai_response = await self.vertex_ai.generate_text(
                prompt=prompt,
                phase_number=self.phase_number
            )
            
            if ai_response.get("success", False):
                # Parse JSON response from Gemini Pro
                ai_result = self._parse_ai_response(ai_response.get("content", ""))
                characters = ai_result.get("characters", [])
                visual_descriptions = ai_result.get("visual_descriptions", {})
                
                self.log_info(f"Gemini Pro character design successful", 
                            tokens=ai_response.get("usage", {}).get("total_tokens", 0))
            else:
                # Fallback to rule-based generation
                self.log_warning(f"Gemini Pro failed, using fallback: {ai_response.get('error', 'Unknown error')}")
                characters = await self._generate_characters(
                    input_data.get("text", ""), genre, themes, target_audience
                )
                visual_descriptions = await self._generate_visual_descriptions(
                    characters, genre, target_audience, world_setting
                )
                
        except Exception as e:
            # Fallback to rule-based generation on error
            self.log_error(f"AI character design failed, using fallback: {str(e)}")
            characters = await self._generate_characters(
                input_data.get("text", ""), genre, themes, target_audience
            )
            visual_descriptions = await self._generate_visual_descriptions(
                characters, genre, target_audience, world_setting
            )
        
        # Generate visual descriptions if not provided by AI
        if not visual_descriptions:
            visual_descriptions = await self._generate_visual_descriptions(
                characters,
                genre,
                target_audience,
                world_setting
            )
        
        result = {
            "characters": characters,
            "visual_descriptions": visual_descriptions,
            "character_count": len(characters),
            "protagonist": characters[0] if characters else None,
            "relationships": self._analyze_relationships(characters),
            "style_guide": self._create_style_guide(genre, target_audience),
            "color_palette": self._generate_color_palette(genre, themes)
        }
        
        return result
    
    async def generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate Gemini Pro prompt for character design."""
        
        text = input_data.get("text", "")[:2000]
        genre = input_data.get("genre", "general")
        themes = input_data.get("themes", [])
        world_setting = input_data.get("world_setting", {})
        
        prompt = f"""あなたは漫画のキャラクターデザインの専門家です。
以下のストーリーから、主要キャラクターを設計してください。

ストーリー概要:
{text}

ジャンル: {genre}
テーマ: {', '.join(themes)}
世界観: {json.dumps(world_setting, ensure_ascii=False)}

以下の要素を含むキャラクター設計をJSON形式で出力してください：

1. characters (配列): 主要キャラクター3-5名
   - name: キャラクター名
   - role: 役割（protagonist, sidekick, mentor, antagonist, love_interest）
   - age: 年齢
   - gender: 性別
   - personality: 性格特性（3-5個）
   - background: 簡単な背景設定
   - motivation: 動機・目的

2. visual_traits (各キャラクター):
   - hair_color: 髪色
   - hair_style: 髪型
   - eye_color: 目の色
   - height: 身長（tall, medium, short）
   - build: 体型（slim, normal, muscular, etc）
   - distinctive_features: 特徴的な要素
   - clothing_style: 服装スタイル

3. relationships:
   - キャラクター間の関係性マップ

JSONフォーマットで回答してください。"""
        
        return prompt
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate phase 2 output."""
        
        required_keys = ["characters", "visual_descriptions", "character_count"]
        
        # Check required keys
        for key in required_keys:
            if key not in output_data:
                self.log_warning(f"Missing required key: {key}")
                return False
        
        # Validate characters
        if not output_data["characters"] or len(output_data["characters"]) < 1:
            self.log_warning("No characters generated")
            return False
        
        # Validate each character has required fields
        for char in output_data["characters"]:
            if not all(k in char for k in ["name", "role", "personality"]):
                self.log_warning(f"Character missing required fields: {char.get('name', 'unknown')}")
                return False
        
        return True
    
    async def _generate_characters(
        self,
        text: str,
        genre: str,
        themes: List[str],
        target_audience: str
    ) -> List[Dict[str, Any]]:
        """Generate characters based on text analysis (placeholder)."""
        
        # Simple rule-based character extraction
        characters = []
        
        # Always create a protagonist
        characters.append({
            "name": self._extract_protagonist_name(text) or "主人公",
            "role": "protagonist",
            "age": self._determine_age(target_audience),
            "gender": self._detect_gender(text, is_protagonist=True),
            "personality": self._generate_personality(genre, "protagonist"),
            "background": "物語の中心人物",
            "motivation": self._extract_motivation(text, themes)
        })
        
        # Add sidekick if detected
        if self._needs_sidekick(genre, themes):
            characters.append({
                "name": "相棒",
                "role": "sidekick",
                "age": self._determine_age(target_audience, offset=-2),
                "gender": self._detect_gender(text, is_protagonist=False),
                "personality": self._generate_personality(genre, "sidekick"),
                "background": "主人公を支える仲間",
                "motivation": "主人公をサポートする"
            })
        
        # Add antagonist if conflict detected
        if self._has_conflict(text, themes):
            characters.append({
                "name": "ライバル",
                "role": "antagonist",
                "age": self._determine_age(target_audience, offset=2),
                "gender": self._detect_gender(text, is_antagonist=True),
                "personality": self._generate_personality(genre, "antagonist"),
                "background": "主人公と対立する存在",
                "motivation": self._generate_antagonist_motivation(themes)
            })
        
        return characters
    
    async def _generate_visual_descriptions(
        self,
        characters: List[Dict[str, Any]],
        genre: str,
        target_audience: str,
        world_setting: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate visual descriptions for characters."""
        
        style = self._determine_visual_style(genre, target_audience)
        descriptions = []
        
        for char in characters:
            desc = {
                "character_name": char["name"],
                "visual_traits": {
                    "hair_color": self._generate_hair_color(char["role"], genre),
                    "hair_style": self._generate_hair_style(char["role"], char.get("gender", "neutral")),
                    "eye_color": self._generate_eye_color(char["role"]),
                    "height": self._determine_height(char["age"], char["role"]),
                    "build": self._determine_build(char["role"], genre),
                    "distinctive_features": self._generate_distinctive_features(char["role"]),
                    "clothing_style": self._generate_clothing_style(world_setting, char["role"])
                },
                "art_style": style,
                "expression": self._determine_default_expression(char["personality"])
            }
            descriptions.append(desc)
        
        return descriptions
    
    def _extract_protagonist_name(self, text: str) -> Optional[str]:
        """Extract protagonist name from text."""
        # Simplified extraction - in real implementation would use NLP
        # Look for patterns like 「名前」or proper nouns
        import re
        
        # Pattern for names in Japanese text
        name_pattern = r'「([^」]+)」'
        matches = re.findall(name_pattern, text[:500])
        
        if matches:
            # Return first match that looks like a name
            for match in matches:
                if len(match) <= 10:  # Names are typically short
                    return match
        
        return None
    
    def _determine_age(self, target_audience: str, offset: int = 0) -> int:
        """Determine character age based on target audience."""
        
        age_map = {
            "children": 10,
            "teens": 16,
            "young_adults": 22,
            "adults": 30,
            "general": 18
        }
        
        base_age = age_map.get(target_audience, 18)
        return max(8, min(60, base_age + offset))
    
    def _detect_gender(self, text: str, is_protagonist: bool = False, is_antagonist: bool = False) -> str:
        """Detect character gender from text clues."""
        
        # Simplified detection - real implementation would use NLP
        male_indicators = ["彼", "男", "少年", "青年"]
        female_indicators = ["彼女", "女", "少女", "女性"]
        
        male_count = sum(1 for word in male_indicators if word in text)
        female_count = sum(1 for word in female_indicators if word in text)
        
        if male_count > female_count:
            return "male"
        elif female_count > male_count:
            return "female"
        else:
            # Default based on role
            if is_protagonist:
                return "male"  # Default protagonist
            elif is_antagonist:
                return "male"  # Default antagonist
            else:
                return "neutral"
    
    def _generate_personality(self, genre: str, role: str) -> List[str]:
        """Generate personality traits based on genre and role."""
        
        personality_templates = {
            ("fantasy", "protagonist"): ["勇敢", "正義感が強い", "成長志向"],
            ("fantasy", "sidekick"): ["忠実", "明るい", "機転が利く"],
            ("fantasy", "antagonist"): ["野心的", "冷酷", "カリスマ性"],
            ("romance", "protagonist"): ["純粋", "優しい", "一途"],
            ("romance", "love_interest"): ["魅力的", "思いやり", "独立心"],
            ("action", "protagonist"): ["強い", "決断力", "リーダーシップ"],
            ("action", "antagonist"): ["狡猾", "執念深い", "戦略的"],
            ("mystery", "protagonist"): ["観察力", "論理的", "冷静"],
            ("slice_of_life", "protagonist"): ["普通", "共感的", "成長する"]
        }
        
        # Get template or use default
        template = personality_templates.get((genre, role), ["個性的", "魅力的", "複雑"])
        
        return template
    
    def _extract_motivation(self, text: str, themes: List[str]) -> str:
        """Extract character motivation from text and themes."""
        
        motivation_map = {
            "成長": "より強くなること",
            "友情": "仲間を守ること",
            "愛": "愛する人のため",
            "正義": "悪を倒すこと",
            "冒険": "未知の世界を探検すること",
            "復讐": "失ったものを取り戻すこと"
        }
        
        for theme in themes:
            if theme in motivation_map:
                return motivation_map[theme]
        
        return "目標を達成すること"
    
    def _needs_sidekick(self, genre: str, themes: List[str]) -> bool:
        """Determine if story needs a sidekick character."""
        
        sidekick_genres = ["fantasy", "action", "adventure"]
        sidekick_themes = ["友情", "仲間", "チーム"]
        
        return genre in sidekick_genres or any(t in themes for t in sidekick_themes)
    
    def _has_conflict(self, text: str, themes: List[str]) -> bool:
        """Detect if story has conflict requiring antagonist."""
        
        conflict_words = ["戦", "敵", "対立", "競争", "挑戦", "困難", "危機"]
        conflict_themes = ["戦闘", "対立", "競争", "挑戦"]
        
        text_has_conflict = any(word in text for word in conflict_words)
        theme_has_conflict = any(t in themes for t in conflict_themes)
        
        return text_has_conflict or theme_has_conflict
    
    def _generate_antagonist_motivation(self, themes: List[str]) -> str:
        """Generate antagonist motivation based on themes."""
        
        if "権力" in themes:
            return "世界を支配すること"
        elif "復讐" in themes:
            return "復讐を果たすこと"
        elif "競争" in themes:
            return "最強になること"
        else:
            return "主人公の目的を阻むこと"
    
    def _determine_visual_style(self, genre: str, target_audience: str) -> str:
        """Determine visual art style."""
        
        if target_audience == "children":
            return "kodomo"
        elif target_audience == "teens":
            return "shounen" if genre in ["action", "fantasy"] else "shoujo"
        elif target_audience == "young_adults":
            return "seinen"
        else:
            return "standard"
    
    def _generate_hair_color(self, role: str, genre: str) -> str:
        """Generate appropriate hair color."""
        
        colors = {
            "protagonist": ["黒", "茶", "金"],
            "sidekick": ["茶", "赤", "オレンジ"],
            "antagonist": ["黒", "白", "紫"],
            "mentor": ["白", "灰", "黒"],
            "love_interest": ["茶", "金", "ピンク"]
        }
        
        role_colors = colors.get(role, ["黒", "茶"])
        
        # Fantasy genres allow more variety
        if genre == "fantasy":
            role_colors.extend(["青", "緑", "紫"])
        
        import random
        return random.choice(role_colors)
    
    def _generate_hair_style(self, role: str, gender: str) -> str:
        """Generate hair style based on role and gender."""
        
        styles = {
            ("male", "protagonist"): "ショート・スパイキー",
            ("female", "protagonist"): "ミディアム・ストレート",
            ("male", "antagonist"): "ロング・ストレート",
            ("female", "antagonist"): "ロング・ウェーブ",
            ("neutral", "any"): "ショート・ナチュラル"
        }
        
        return styles.get((gender, role), styles.get((gender, "any"), "ミディアム"))
    
    def _generate_eye_color(self, role: str) -> str:
        """Generate eye color based on role."""
        
        colors = {
            "protagonist": ["茶", "青", "緑"],
            "antagonist": ["赤", "紫", "金"],
            "sidekick": ["茶", "黒"],
            "mentor": ["灰", "青"],
            "love_interest": ["茶", "青", "緑"]
        }
        
        import random
        return random.choice(colors.get(role, ["茶", "黒"]))
    
    def _determine_height(self, age: int, role: str) -> str:
        """Determine character height."""
        
        if age < 12:
            return "short"
        elif age < 16:
            return "medium" if role != "sidekick" else "short"
        else:
            if role == "mentor":
                return "tall"
            elif role == "protagonist":
                return "medium"
            else:
                return "medium"
    
    def _determine_build(self, role: str, genre: str) -> str:
        """Determine character build."""
        
        builds = {
            ("protagonist", "action"): "athletic",
            ("protagonist", "fantasy"): "lean",
            ("antagonist", "action"): "muscular",
            ("sidekick", "any"): "slim",
            ("mentor", "any"): "normal"
        }
        
        return builds.get((role, genre), builds.get((role, "any"), "normal"))
    
    def _generate_distinctive_features(self, role: str) -> List[str]:
        """Generate distinctive visual features."""
        
        features = {
            "protagonist": ["特徴的な髪型", "明るい瞳"],
            "antagonist": ["鋭い目つき", "不敵な笑み"],
            "sidekick": ["愛らしい表情", "特徴的なアクセサリー"],
            "mentor": ["威厳ある雰囲気", "経験を感じさせる傷跡"],
            "love_interest": ["美しい瞳", "優しい微笑み"]
        }
        
        return features.get(role, ["個性的な特徴"])
    
    def _generate_clothing_style(self, world_setting: Dict[str, Any], role: str) -> str:
        """Generate clothing style based on world and role."""
        
        time_period = world_setting.get("time_period", "present")
        
        clothing = {
            ("fantasy", "protagonist"): "冒険者の装備",
            ("fantasy", "antagonist"): "黒いローブ",
            ("present", "protagonist"): "カジュアルな現代服",
            ("present", "antagonist"): "フォーマルなスーツ",
            ("future", "protagonist"): "未来的なボディスーツ",
            ("past", "protagonist"): "時代衣装"
        }
        
        return clothing.get((time_period, role), "標準的な服装")
    
    def _determine_default_expression(self, personality: List[str]) -> str:
        """Determine default facial expression."""
        
        if "明るい" in personality:
            return "smile"
        elif "冷酷" in personality:
            return "serious"
        elif "優しい" in personality:
            return "gentle"
        else:
            return "neutral"
    
    def _analyze_relationships(self, characters: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Analyze relationships between characters."""
        
        relationships = {}
        
        for i, char in enumerate(characters):
            char_name = char["name"]
            char_relationships = []
            
            for j, other in enumerate(characters):
                if i != j:
                    relationship = self._determine_relationship(
                        char["role"], 
                        other["role"]
                    )
                    if relationship:
                        char_relationships.append(f"{other['name']}: {relationship}")
            
            relationships[char_name] = char_relationships
        
        return relationships
    
    def _determine_relationship(self, role1: str, role2: str) -> str:
        """Determine relationship between two roles."""
        
        relationship_map = {
            ("protagonist", "sidekick"): "親友",
            ("protagonist", "antagonist"): "宿敵",
            ("protagonist", "mentor"): "弟子",
            ("protagonist", "love_interest"): "恋愛関係",
            ("sidekick", "protagonist"): "親友",
            ("antagonist", "protagonist"): "敵対",
            ("mentor", "protagonist"): "師匠",
            ("love_interest", "protagonist"): "想い人"
        }
        
        return relationship_map.get((role1, role2), "")
    
    def _create_style_guide(self, genre: str, target_audience: str) -> Dict[str, str]:
        """Create visual style guide."""
        
        return {
            "art_style": self._determine_visual_style(genre, target_audience),
            "line_weight": "medium" if target_audience != "children" else "thick",
            "shading_style": "cel" if genre in ["action", "fantasy"] else "soft",
            "detail_level": "high" if target_audience in ["young_adults", "adults"] else "medium",
            "expression_style": "expressive" if genre == "comedy" else "realistic"
        }
    
    def _generate_color_palette(self, genre: str, themes: List[str]) -> Dict[str, List[str]]:
        """Generate color palette for the manga."""
        
        base_palettes = {
            "fantasy": {
                "primary": ["#4A90E2", "#7B68EE", "#9370DB"],
                "secondary": ["#FFD700", "#FFA500", "#FF6347"],
                "accent": ["#32CD32", "#20B2AA", "#FF1493"]
            },
            "romance": {
                "primary": ["#FFB6C1", "#FFC0CB", "#FF69B4"],
                "secondary": ["#E6E6FA", "#DDA0DD", "#DA70D6"],
                "accent": ["#F0E68C", "#FFE4B5", "#FFDEAD"]
            },
            "action": {
                "primary": ["#DC143C", "#FF4500", "#FF6347"],
                "secondary": ["#4B0082", "#483D8B", "#6A5ACD"],
                "accent": ["#FFD700", "#FFA500", "#FF8C00"]
            },
            "mystery": {
                "primary": ["#2F4F4F", "#708090", "#778899"],
                "secondary": ["#4682B4", "#5F9EA0", "#6495ED"],
                "accent": ["#B22222", "#8B0000", "#A52A2A"]
            }
        }
        
        # Get base palette or use default
        palette = base_palettes.get(genre, {
            "primary": ["#000000", "#333333", "#666666"],
            "secondary": ["#999999", "#CCCCCC", "#E0E0E0"],
            "accent": ["#FF0000", "#00FF00", "#0000FF"]
        })
        
        return palette
    
    async def generate_preview(
        self,
        output_data: Dict[str, Any],
        quality_level: str = "high"
    ) -> Dict[str, Any]:
        """Generate preview for phase 2 results."""
        
        characters = output_data.get("characters", [])
        visual_descs = output_data.get("visual_descriptions", [])
        
        preview = {
            "phase": self.phase_number,
            "title": "キャラクター設定",
            "character_cards": [
                {
                    "name": char.get("name"),
                    "role": char.get("role"),
                    "visual": desc.get("visual_traits") if i < len(visual_descs) else {},
                    "personality": char.get("personality", [])
                }
                for i, (char, desc) in enumerate(zip(characters, visual_descs))
            ],
            "relationships": output_data.get("relationships", {}),
            "style_guide": output_data.get("style_guide", {}),
            "color_palette": output_data.get("color_palette", {})
        }
        
        return preview
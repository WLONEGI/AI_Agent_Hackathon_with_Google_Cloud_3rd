"""Phase 1: Concept Analysis Agent - Restructured Version."""

import json
import re
from typing import Dict, Any, Optional
from datetime import datetime

from app.agents.base.agent import BaseAgent
from app.agents.base.validator import BaseValidator
from app.core.config import settings
from .validator import Phase1Validator
from .schemas import ConceptOutput, ConceptInput, GenreAnalysis, ThemeAnalysis, WorldSettings, GenreType, ToneType, NarrativeStyle, TargetAudience
from .prompts import ConceptAnalysisPrompts


class Phase1ConceptAgent(BaseAgent):
    """Phase 1 Agent: Concept and World Analysis."""
    
    def __init__(self):
        super().__init__(
            phase_number=1,
            phase_name="コンセプト・世界観分析",
            timeout_seconds=settings.phase_timeouts[1]
        )
        
        # Genre detection keywords
        self.genre_keywords = {
            GenreType.FANTASY: ["魔法", "エルフ", "ドラゴン", "勇者", "魔王", "冒険", "ファンタジー", "魔術", "精霊"],
            GenreType.ROMANCE: ["恋", "愛", "告白", "デート", "結婚", "恋愛", "ロマンス", "恋人", "初恋"],
            GenreType.ACTION: ["戦闘", "バトル", "格闘", "戦い", "決闘", "アクション", "武器", "戦争"],
            GenreType.MYSTERY: ["事件", "謎", "探偵", "推理", "犯人", "ミステリー", "捜査", "証拠"],
            GenreType.SLICE_OF_LIFE: ["日常", "学校", "生活", "友達", "家族", "青春", "普通", "平凡"],
            GenreType.SCI_FI: ["宇宙", "ロボット", "未来", "科学", "SF", "テクノロジー", "宇宙船", "人工知能"],
            GenreType.HORROR: ["怖い", "恐怖", "幽霊", "呪い", "ホラー", "怪談", "死", "悪霊"]
        }
        
        self.prompt_generator = ConceptAnalysisPrompts()
        
        self.logger.info("Phase 1 Concept Agent initialized with structured architecture")
    
    def _create_validator(self) -> BaseValidator:
        """Create Phase 1 specific validator."""
        return Phase1Validator()
    
    async def _generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate AI prompt for concept analysis."""
        
        # Get text from accumulated_context (where it's stored in PhaseInput)
        text = input_data.get("accumulated_context", {}).get("text", "") or input_data.get("text", "")
        user_preferences = input_data.get("user_preferences")
        
        if not text:
            raise ValueError("Input text is required for concept analysis")
        
        return self.prompt_generator.get_main_analysis_prompt(text, user_preferences)
    
    async def _process_ai_response(
        self,
        ai_response: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process AI response into structured output."""
        
        text = input_data.get("text", "")
        
        try:
            # Try to parse AI response as JSON
            ai_data = json.loads(ai_response)
            
            # Build structured output using schemas
            concept_output = await self._build_concept_output(ai_data, text)
            
            return concept_output.dict()
            
        except json.JSONDecodeError:
            # Fallback to rule-based analysis if AI response parsing fails
            self.logger.warning("AI response parsing failed, falling back to rule-based analysis")
            return await self._rule_based_analysis(text)
    
    async def _build_concept_output(
        self,
        ai_data: Dict[str, Any], 
        text: str
    ) -> ConceptOutput:
        """Build structured ConceptOutput from AI data."""
        
        # Process genre analysis
        genre_data = ai_data.get("genre_analysis", {})
        genre_analysis = GenreAnalysis(
            primary_genre=GenreType(genre_data.get("primary_genre", "general")),
            secondary_genres=[GenreType(g) for g in genre_data.get("secondary_genres", [])],
            confidence_score=genre_data.get("confidence_score", 0.5),
            genre_keywords=genre_data.get("genre_keywords", [])
        )
        
        # Process theme analysis
        theme_data = ai_data.get("theme_analysis", {})
        theme_analysis = ThemeAnalysis(
            main_themes=theme_data.get("main_themes", []),
            sub_themes=theme_data.get("sub_themes", []),
            moral_lessons=theme_data.get("moral_lessons", []),
            conflict_types=theme_data.get("conflict_types", [])
        )
        
        # Process world settings
        world_data = ai_data.get("world_setting", {})
        world_setting = WorldSettings(
            time_period=world_data.get("time_period", "modern"),
            location=world_data.get("location", "unknown"),
            technology_level=world_data.get("technology_level", "modern"),
            magic_system=world_data.get("magic_system"),
            special_rules=world_data.get("special_rules", []),
            cultural_elements=world_data.get("cultural_elements", [])
        )
        
        # Build complete output
        concept_output = ConceptOutput(
            original_text=text[:1000],  # Truncate to 1000 chars
            text_length=len(text),
            genre_analysis=genre_analysis,
            theme_analysis=theme_analysis,
            tone=ToneType(ai_data.get("tone", "neutral")),
            narrative_style=NarrativeStyle(ai_data.get("narrative_style", "third_person")),
            target_audience=TargetAudience(ai_data.get("target_audience", "general")),
            world_setting=world_setting,
            key_characters=ai_data.get("key_characters", []),
            key_events=ai_data.get("key_events", []),
            key_objects=ai_data.get("key_objects", []),
            estimated_pages=ai_data.get("estimated_pages", self._estimate_pages(len(text))),
            complexity_score=ai_data.get("complexity_score", 0.5),
            visual_richness=ai_data.get("visual_richness", 0.5),
            analysis_timestamp=datetime.utcnow().isoformat(),
            ai_model_used="simulated"  # In production, this would be the actual model name
        )
        
        return concept_output
    
    async def _rule_based_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback rule-based analysis when AI parsing fails."""
        
        # Genre detection
        genre_scores = {}
        detected_keywords = []
        
        for genre, keywords in self.genre_keywords.items():
            score = 0
            genre_keywords = []
            
            for keyword in keywords:
                count = text.count(keyword)
                if count > 0:
                    score += count
                    genre_keywords.append(keyword)
            
            if score > 0:
                genre_scores[genre] = score
                detected_keywords.extend(genre_keywords)
        
        # Determine primary genre
        primary_genre = GenreType.GENERAL
        if genre_scores:
            primary_genre = max(genre_scores.keys(), key=lambda k: genre_scores[k])
        
        # Build genre analysis
        genre_analysis = GenreAnalysis(
            primary_genre=primary_genre,
            secondary_genres=[],
            confidence_score=0.6 if genre_scores else 0.3,
            genre_keywords=detected_keywords[:10]  # Top 10 keywords
        )
        
        # Basic theme extraction (simplified)
        themes = []
        if "友情" in text or "友達" in text:
            themes.append("友情")
        if "成長" in text or "変化" in text:
            themes.append("成長")
        if "愛" in text or "恋" in text:
            themes.append("愛情")
        
        theme_analysis = ThemeAnalysis(
            main_themes=themes,
            sub_themes=[],
            moral_lessons=[],
            conflict_types=["internal", "external"]  # Default conflicts
        )
        
        # Basic world settings
        world_setting = WorldSettings(
            time_period="modern",
            location="unknown",
            technology_level="modern",
            magic_system=None,
            special_rules=[],
            cultural_elements=[]
        )
        
        # Determine tone (simplified)
        tone = ToneType.NEUTRAL
        if any(word in text for word in ["笑", "楽し", "面白", "嬉し"]):
            tone = ToneType.LIGHT
        elif any(word in text for word in ["悲し", "暗", "辛", "死"]):
            tone = ToneType.DARK
        
        # Build complete output
        concept_output = ConceptOutput(
            original_text=text[:1000],
            text_length=len(text),
            genre_analysis=genre_analysis,
            theme_analysis=theme_analysis,
            tone=tone,
            narrative_style=NarrativeStyle.THIRD_PERSON,
            target_audience=TargetAudience.GENERAL,
            world_setting=world_setting,
            key_characters=self._extract_character_names(text),
            key_events=self._extract_key_events(text),
            key_objects=self._extract_key_objects(text),
            estimated_pages=self._estimate_pages(len(text)),
            complexity_score=0.5,
            visual_richness=0.6,
            analysis_timestamp=datetime.utcnow().isoformat(),
            ai_model_used="rule_based_fallback"
        )
        
        return concept_output.dict()
    
    async def _generate_preview(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview data for Phase 1."""
        
        preview = {
            "phase_name": "概念分析",
            "summary": f"ジャンル: {output_data.get('genre_analysis', {}).get('primary_genre', '不明')}",
            "key_insights": [],
            "visual_elements": []
        }
        
        # Add key insights
        genre_analysis = output_data.get("genre_analysis", {})
        if genre_analysis.get("primary_genre"):
            preview["key_insights"].append(f"主要ジャンル: {genre_analysis['primary_genre']}")
        
        theme_analysis = output_data.get("theme_analysis", {})
        if theme_analysis.get("main_themes"):
            themes = ", ".join(theme_analysis["main_themes"][:3])
            preview["key_insights"].append(f"主要テーマ: {themes}")
        
        if output_data.get("estimated_pages"):
            preview["key_insights"].append(f"推定ページ数: {output_data['estimated_pages']}")
        
        # Add visual elements for preview
        world_setting = output_data.get("world_setting", {})
        if world_setting.get("time_period"):
            preview["visual_elements"].append(f"時代設定: {world_setting['time_period']}")
        
        if world_setting.get("location"):
            preview["visual_elements"].append(f"舞台: {world_setting['location']}")
        
        return preview
    
    def _estimate_pages(self, text_length: int) -> int:
        """Estimate manga pages needed based on text length."""
        
        # Rough estimation: 150-250 characters per page on average
        # Varies based on dialog vs narrative, action vs conversation
        
        if text_length < 500:
            return max(1, text_length // 200)
        elif text_length < 2000:
            return max(2, text_length // 180)
        elif text_length < 5000:
            return max(3, text_length // 160)
        else:
            return max(5, min(50, text_length // 140))  # Cap at 50 pages
    
    def _extract_character_names(self, text: str) -> list:
        """Extract potential character names from text."""
        
        # Simple name extraction using regex
        # Look for words that start with capital letters and might be names
        name_pattern = r'[A-Z][a-z]+|[あ-ん]{2,4}|[ア-ン]{2,4}'
        potential_names = re.findall(name_pattern, text)
        
        # Filter out common words that aren't names
        common_words = {"私", "僕", "君", "彼", "彼女", "先生", "お母さん", "お父さん"}
        names = [name for name in potential_names if name not in common_words]
        
        # Return unique names, limited to 10
        return list(set(names))[:10]
    
    def _extract_key_events(self, text: str) -> list:
        """Extract key events from text."""
        
        # Look for action verbs and event indicators
        event_keywords = ["戦った", "出会った", "発見した", "決断した", "旅立った", "到着した"]
        events = []
        
        sentences = text.split("。")
        for sentence in sentences:
            for keyword in event_keywords:
                if keyword in sentence:
                    events.append(sentence.strip()[:100])  # Truncate long sentences
                    break
        
        return events[:5]  # Return top 5 events
    
    def _extract_key_objects(self, text: str) -> list:
        """Extract key objects from text."""
        
        # Look for important objects
        object_keywords = ["剣", "魔法", "宝物", "手紙", "鍵", "地図", "本", "宝石"]
        objects = []
        
        for keyword in object_keywords:
            if keyword in text:
                objects.append(keyword)
        
        return objects[:5]  # Return top 5 objects
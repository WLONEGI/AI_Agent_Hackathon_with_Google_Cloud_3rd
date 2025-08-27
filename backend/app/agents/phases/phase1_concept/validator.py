"""Validator for Phase 1: Concept Analysis."""

from typing import Dict, Any
from app.agents.base.validator import BaseValidator, ValidationResult
from .schemas import ConceptOutput, GenreType, ToneType


class Phase1Validator(BaseValidator):
    """Validator for Phase 1 concept analysis output."""
    
    def __init__(self):
        super().__init__("Concept Analysis")
        
        # Phase 1 specific required fields
        self.required_fields.extend([
            "genre_analysis",
            "theme_analysis", 
            "world_setting",
            "estimated_pages"
        ])
        
        # Genre keywords for validation
        self.genre_keywords = {
            GenreType.FANTASY: ["魔法", "エルフ", "ドラゴン", "勇者", "魔王", "冒険", "ファンタジー"],
            GenreType.ROMANCE: ["恋", "愛", "告白", "デート", "結婚", "恋愛", "ロマンス"],
            GenreType.ACTION: ["戦闘", "バトル", "格闘", "戦い", "決闘", "アクション"],
            GenreType.MYSTERY: ["事件", "謎", "探偵", "推理", "犯人", "ミステリー"],
            GenreType.SLICE_OF_LIFE: ["日常", "学校", "生活", "友達", "家族", "青春"],
            GenreType.SCI_FI: ["宇宙", "ロボット", "未来", "科学", "SF", "テクノロジー"],
            GenreType.HORROR: ["怖い", "恐怖", "幽霊", "呪い", "ホラー", "怪談"]
        }
    
    async def _validate_phase_specific(
        self,
        output: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate Phase 1 specific requirements."""
        
        # Validate genre analysis
        await self._validate_genre_analysis(output, result)
        
        # Validate theme analysis
        await self._validate_theme_analysis(output, result)
        
        # Validate world settings
        await self._validate_world_settings(output, result)
        
        # Validate estimated pages
        await self._validate_estimated_pages(output, result)
        
        # Validate text analysis consistency
        await self._validate_text_consistency(output, result)
    
    async def _validate_genre_analysis(
        self,
        output: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate genre analysis."""
        if "genre_analysis" not in output:
            return
        
        genre_analysis = output["genre_analysis"]
        
        # Check if genre analysis has required fields
        required_genre_fields = ["primary_genre", "confidence_score"]
        for field in required_genre_fields:
            if field not in genre_analysis:
                result.add_error(
                    f"genre_analysis.{field}",
                    f"Genre analysis missing required field: {field}"
                )
        
        # Validate confidence score
        if "confidence_score" in genre_analysis:
            confidence = genre_analysis["confidence_score"]
            if not isinstance(confidence, (int, float)):
                result.add_error(
                    "genre_analysis.confidence_score",
                    "Confidence score must be a number"
                )
            elif not (0.0 <= confidence <= 1.0):
                result.add_error(
                    "genre_analysis.confidence_score",
                    "Confidence score must be between 0.0 and 1.0"
                )
        
        # Validate primary genre
        if "primary_genre" in genre_analysis:
            primary_genre = genre_analysis["primary_genre"]
            if primary_genre not in [g.value for g in GenreType]:
                result.add_warning(
                    "genre_analysis.primary_genre",
                    f"Unrecognized genre: {primary_genre}"
                )
        
        # Check if genre keywords are provided and relevant
        if "genre_keywords" in genre_analysis and "primary_genre" in genre_analysis:
            keywords = genre_analysis["genre_keywords"]
            primary_genre = genre_analysis["primary_genre"]
            
            if isinstance(keywords, list) and primary_genre in [g.value for g in GenreType]:
                expected_keywords = self.genre_keywords.get(GenreType(primary_genre), [])
                
                # Check if any provided keywords match expected keywords
                matching_keywords = any(
                    keyword in expected_keywords or any(exp in keyword for exp in expected_keywords)
                    for keyword in keywords
                )
                
                if not matching_keywords and len(keywords) > 0:
                    result.add_warning(
                        "genre_analysis.genre_keywords",
                        f"Provided keywords don't seem to match {primary_genre} genre"
                    )
    
    async def _validate_theme_analysis(
        self,
        output: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate theme analysis."""
        if "theme_analysis" not in output:
            return
        
        theme_analysis = output["theme_analysis"]
        
        # Check if main themes exist
        if "main_themes" in theme_analysis:
            main_themes = theme_analysis["main_themes"]
            if not isinstance(main_themes, list):
                result.add_error(
                    "theme_analysis.main_themes",
                    "Main themes must be a list"
                )
            elif len(main_themes) == 0:
                result.add_warning(
                    "theme_analysis.main_themes",
                    "No main themes identified"
                )
            elif len(main_themes) > 5:
                result.add_warning(
                    "theme_analysis.main_themes",
                    "Too many main themes (>5) may indicate unfocused analysis"
                )
        
        # Validate conflict types
        if "conflict_types" in theme_analysis:
            conflict_types = theme_analysis["conflict_types"]
            valid_conflicts = [
                "internal", "external", "character_vs_character",
                "character_vs_society", "character_vs_nature", "character_vs_fate"
            ]
            
            if isinstance(conflict_types, list):
                for conflict in conflict_types:
                    if conflict not in valid_conflicts:
                        result.add_warning(
                            "theme_analysis.conflict_types",
                            f"Unrecognized conflict type: {conflict}"
                        )
    
    async def _validate_world_settings(
        self,
        output: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate world settings."""
        if "world_setting" not in output:
            return
        
        world_setting = output["world_setting"]
        
        # Check basic world setting fields
        if "time_period" in world_setting:
            time_period = world_setting["time_period"]
            valid_periods = [
                "prehistoric", "ancient", "medieval", "renaissance",
                "industrial", "modern", "near_future", "far_future", "unknown"
            ]
            if time_period not in valid_periods:
                result.add_warning(
                    "world_setting.time_period",
                    f"Unrecognized time period: {time_period}"
                )
        
        # Validate consistency between genre and world settings
        if "genre_analysis" in output and "primary_genre" in output["genre_analysis"]:
            primary_genre = output["genre_analysis"]["primary_genre"]
            
            # Fantasy should have magic system or special rules
            if primary_genre == GenreType.FANTASY.value:
                has_magic = world_setting.get("magic_system") is not None
                has_special_rules = len(world_setting.get("special_rules", [])) > 0
                
                if not has_magic and not has_special_rules:
                    result.add_warning(
                        "world_setting",
                        "Fantasy genre usually requires magic system or special rules"
                    )
            
            # Sci-fi should have appropriate technology level
            if primary_genre == GenreType.SCI_FI.value:
                tech_level = world_setting.get("technology_level", "")
                if tech_level not in ["advanced", "futuristic", "far_future"]:
                    result.add_warning(
                        "world_setting.technology_level",
                        "Sci-fi genre usually requires advanced technology level"
                    )
    
    async def _validate_estimated_pages(
        self,
        output: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate estimated pages."""
        if "estimated_pages" not in output:
            return
        
        estimated_pages = output["estimated_pages"]
        
        if not isinstance(estimated_pages, int):
            result.add_error(
                "estimated_pages",
                "Estimated pages must be an integer"
            )
            return
        
        if estimated_pages < 1:
            result.add_error(
                "estimated_pages", 
                "Estimated pages must be at least 1"
            )
        elif estimated_pages > 200:
            result.add_warning(
                "estimated_pages",
                "Estimated pages seems very high (>200) for a single story"
            )
        
        # Cross-validate with text length
        if "text_length" in output:
            text_length = output["text_length"]
            
            # Rough estimation: 100-300 characters per page depending on complexity
            expected_pages_min = text_length // 300
            expected_pages_max = text_length // 100
            
            if estimated_pages < expected_pages_min * 0.5:
                result.add_warning(
                    "estimated_pages",
                    "Estimated pages seems too low for text length"
                )
            elif estimated_pages > expected_pages_max * 2:
                result.add_warning(
                    "estimated_pages",
                    "Estimated pages seems too high for text length"
                )
    
    async def _validate_text_consistency(
        self,
        output: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate consistency between text and analysis."""
        
        # Check if original text length matches reported length
        if "original_text" in output and "text_length" in output:
            original_text = output["original_text"]
            reported_length = output["text_length"]
            
            # Original text is truncated to 1000 chars, so we can only validate up to that
            if len(original_text) == 1000 and reported_length < 1000:
                result.add_error(
                    "text_length",
                    "Text length inconsistency: truncated text suggests longer content"
                )
        
        # Validate complexity and visual richness scores
        if "complexity_score" in output:
            complexity = output["complexity_score"]
            if not isinstance(complexity, (int, float)):
                result.add_error(
                    "complexity_score",
                    "Complexity score must be a number"
                )
            elif not (0.0 <= complexity <= 1.0):
                result.add_error(
                    "complexity_score",
                    "Complexity score must be between 0.0 and 1.0"
                )
        
        if "visual_richness" in output:
            visual_richness = output["visual_richness"]
            if not isinstance(visual_richness, (int, float)):
                result.add_error(
                    "visual_richness",
                    "Visual richness must be a number"
                )
            elif not (0.0 <= visual_richness <= 1.0):
                result.add_error(
                    "visual_richness", 
                    "Visual richness must be between 0.0 and 1.0"
                )
        
        # Check timestamp format
        if "analysis_timestamp" in output:
            timestamp = output["analysis_timestamp"]
            if not isinstance(timestamp, str):
                result.add_error(
                    "analysis_timestamp",
                    "Analysis timestamp must be a string"
                )
            else:
                # Basic timestamp format validation
                import re
                iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
                if not re.match(iso_pattern, timestamp):
                    result.add_warning(
                        "analysis_timestamp",
                        "Timestamp should be in ISO format"
                    )
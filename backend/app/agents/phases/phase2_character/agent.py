"""Phase 2 Agent: Character Design."""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.agents.base.agent import BaseAgent
from app.agents.base.validator import BaseValidator
from app.core.logging import LoggerMixin
from app.core.config import settings

from .schemas import (
    CharacterDesignInput,
    CharacterDesignOutput,
    CharacterProfile,
    CharacterRelationship,
    StyleGuide,
    CharacterArchetypeType,
    GenderType,
    AgeGroupType,
    VisualStyleType
)
from .validator import Phase2Validator
from .processors.character_analyzer import CharacterAnalyzer
from .processors.visual_generator import VisualGenerator


class Phase2CharacterAgent(BaseAgent):
    """Phase 2 Agent: Character Design and Visual Style Creation."""

    def __init__(self):
        super().__init__(
            phase_number=2,
            phase_name="キャラクターデザイン",
            timeout_seconds=settings.phase_timeouts.get(2, 120)
        )

        # Initialize processors
        self.character_analyzer = CharacterAnalyzer()
        self.visual_generator = VisualGenerator()

        # Genre to visual style mapping
        self.genre_style_mapping = {
            "fantasy": VisualStyleType.SHOUNEN,
            "romance": VisualStyleType.SHOUJO,
            "action": VisualStyleType.SHOUNEN,
            "mystery": VisualStyleType.SEINEN,
            "slice_of_life": VisualStyleType.SHOUJO,
            "sci_fi": VisualStyleType.SEINEN,
            "horror": VisualStyleType.SEINEN,
            "general": VisualStyleType.SHOUNEN
        }

        self.logger.info("Phase 2 Character Agent initialized with structured architecture")

    def _create_validator(self) -> BaseValidator:
        """Create Phase 2 specific validator."""
        return Phase2Validator()

    async def _generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate AI prompt for character design."""

        # Extract Phase 1 results
        if not previous_results or 1 not in previous_results:
            raise ValueError("Phase 1 results required for character design")

        phase1_result = previous_results[1]

        # Extract key information
        genre_analysis = phase1_result.get("genre_analysis", {})
        theme_analysis = phase1_result.get("theme_analysis", {})
        world_setting = phase1_result.get("world_setting", {})
        tone = phase1_result.get("tone", "neutral")
        target_audience = phase1_result.get("target_audience", "general")

        primary_genre = genre_analysis.get("primary_genre", "general")
        main_themes = theme_analysis.get("main_themes", [])

        # Build comprehensive prompt
        prompt = f"""# キャラクターデザイン指示書

## 基本設定
- 主要ジャンル: {primary_genre}
- メインテーマ: {', '.join(main_themes[:3]) if main_themes else '未指定'}
- ターゲット読者: {target_audience}
- 作品の雰囲気: {tone}

## 世界設定
- 時代設定: {world_setting.get('time_period', '現代')}
- 舞台: {world_setting.get('location', '不明')}
- 技術レベル: {world_setting.get('technology_level', '現代')}
- 特別な要素: {', '.join(world_setting.get('special_rules', [])) if world_setting.get('special_rules') else 'なし'}

## 指示内容
以下のJSON形式でキャラクターデザインを生成してください：

{{
    "characters": [
        {{
            "name": "キャラクター名",
            "archetype": "protagonist|sidekick|mentor|antagonist|love_interest|supporting",
            "gender": "male|female|non_binary|unknown",
            "age_group": "child|teenager|young_adult|adult|middle_aged|elderly",
            "age_specific": 数値,
            "appearance": {{
                "hair_color": "black|brown|blonde|red|blue|green|purple|pink|white|silver",
                "hair_style": "具体的な髪型の説明",
                "eye_color": "black|brown|blue|green|gray|hazel|amber|violet|red|gold",
                "height": "very_short|short|average|tall|very_tall",
                "build": "slim|average|athletic|muscular|heavy",
                "distinctive_features": ["特徴的な外見要素のリスト"],
                "clothing_style": "服装スタイルの説明",
                "default_expression": "普段の表情",
                "age_appearance": "見た目年齢の説明"
            }},
            "personality": {{
                "main_traits": [
                    {{
                        "trait": "性格特性",
                        "strength": 0.0-1.0の強度,
                        "description": "特性の詳細説明"
                    }}
                ],
                "motivation": "キャラクターの主な動機",
                "fears": ["恐れや不安のリスト"],
                "strengths": ["強みのリスト"],
                "weaknesses": ["弱点のリスト"],
                "speech_pattern": "話し方の特徴",
                "background_summary": "背景ストーリーの要約"
            }},
            "role_importance": 0.0-1.0,
            "screen_time_estimate": 0.0-1.0,
            "visual_style_preference": "shounen|shoujo|seinen|kodomo|josei",
            "design_complexity": 0.0-1.0
        }}
    ],
    "relationships": [
        {{
            "character1_name": "キャラクター1の名前",
            "character2_name": "キャラクター2の名前",
            "relationship_type": "関係性の種類",
            "relationship_strength": 0.0-1.0,
            "description": "関係性の説明"
        }}
    ],
    "style_guide": {{
        "overall_style": "shounen|shoujo|seinen|kodome|josei",
        "color_palette": {{
            "primary": "主要カラー",
            "secondary": "副次カラー",
            "accent": "アクセントカラー"
        }},
        "design_principles": ["デザイン原則のリスト"],
        "consistency_notes": ["一貫性維持のための注意点"],
        "reference_notes": ["参考資料や影響を受けた作品"]
    }},
    "total_characters": キャラクター総数,
    "main_characters_count": 主要キャラクター数,
    "design_complexity_score": 0.0-1.0,
    "visual_consistency_score": 0.0-1.0
}}

## 要求事項
1. ジャンル「{primary_genre}」に適した魅力的なキャラクターを3-8人デザインしてください
2. 主人公は必ず含めてください
3. ターゲット読者「{target_audience}」に適した年齢層を考慮してください
4. テーマ「{', '.join(main_themes[:2]) if main_themes else 'なし'}」を反映した人物設定にしてください
5. 視覚的な統一感のあるスタイルガイドを作成してください
6. キャラクター間の関係性を明確にしてください
7. 各キャラクターの外見は具体的で魅力的にデザインしてください
8. 性格は多面的で深みのある設定にしてください

上記JSON形式で回答してください。"""

        return prompt

    async def _process_ai_response(
        self,
        ai_response: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process AI response into structured output."""

        # Extract Phase 1 data for fallback
        previous_results = input_data.get("previous_results", {})
        phase1_result = previous_results.get(1, {}) if previous_results else {}

        try:
            # Try to parse AI response as JSON
            ai_data = json.loads(ai_response)

            # Build structured output using processors
            character_output = await self._build_character_output(ai_data, phase1_result)

            return character_output

        except json.JSONDecodeError:
            # Fallback to processor-based analysis if AI response parsing fails
            self.logger.warning("AI response parsing failed, falling back to processor-based analysis")
            return await self._processor_based_analysis(phase1_result)

    async def _build_character_output(
        self,
        ai_data: Dict[str, Any],
        phase1_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build structured character output from AI data."""
        # Force module reload 2025-09-16 - Cache clearing test - Reload trigger
        # Process character data with validation

        # Extract data from Phase 1
        genre_analysis = phase1_result.get("genre_analysis", {})
        theme_analysis = phase1_result.get("theme_analysis", {})
        target_audience = phase1_result.get("target_audience", "general")

        # Process characters
        characters_data = ai_data.get("characters", [])
        processed_characters = []

        for char_data in characters_data:
            # Validate and fix personality data
            personality_data = char_data.get("personality", {})

            # Check if personality has required fields
            if not personality_data.get("main_traits") or not personality_data.get("motivation"):
                self.logger.warning(f"Incomplete personality for {char_data.get('name', 'unknown')}, creating default personality")
                # Create default personality with required fields
                personality_data = {
                    "main_traits": [
                        {
                            "trait": "勇敢",
                            "strength": 0.8,
                            "description": "勇敢という特徴を持つ"
                        },
                        {
                            "trait": "親切",
                            "strength": 0.7,
                            "description": "親切という特徴を持つ"
                        }
                    ],
                    "motivation": "仲間を守りたい",
                    "fears": ["失敗への恐れ"],
                    "strengths": ["勇敢", "親切"],
                    "weaknesses": ["完璧主義"],
                    "behavioral_patterns": ["困っている人を見捨てられない"],
                    "speech_patterns": ["丁寧語を使う"],
                    "core_values": ["友情", "正義"],
                    "character_arc": "仲間との絆を深める"
                }

            # Build character profile
            character = {
                "name": char_data.get("name", "無名"),
                "archetype": char_data.get("archetype", CharacterArchetypeType.SUPPORTING.value),
                "gender": char_data.get("gender", GenderType.UNKNOWN.value),
                "age_group": char_data.get("age_group", AgeGroupType.YOUNG_ADULT.value),
                "age_specific": char_data.get("age_specific", 18),
                "appearance": char_data.get("appearance", {}),
                "personality": personality_data,
                "role_importance": char_data.get("role_importance", 0.5),
                "screen_time_estimate": char_data.get("screen_time_estimate", 0.3),
                "visual_style_preference": char_data.get("visual_style_preference", VisualStyleType.SHOUNEN.value),
                "design_complexity": char_data.get("design_complexity", 0.5)
            }
            processed_characters.append(character)

        # Process relationships
        relationships_data = ai_data.get("relationships", [])
        processed_relationships = []

        for rel_data in relationships_data:
            relationship = {
                "character1_name": rel_data.get("character1_name", ""),
                "character2_name": rel_data.get("character2_name", ""),
                "relationship_type": rel_data.get("relationship_type", "acquaintance"),
                "relationship_strength": rel_data.get("relationship_strength", 0.5),
                "description": rel_data.get("description", "")
            }
            processed_relationships.append(relationship)

        # Process style guide
        style_data = ai_data.get("style_guide", {})
        primary_genre = genre_analysis.get("primary_genre", "general")
        default_style = self.genre_style_mapping.get(primary_genre, VisualStyleType.SHOUNEN)

        style_guide = {
            "overall_style": style_data.get("overall_style", default_style.value),
            "color_palette": style_data.get("color_palette", {
                "primary": "#2E7D32",  # Green
                "secondary": "#1976D2",  # Blue
                "accent": "#F57C00"  # Orange
            }),
            "design_principles": style_data.get("design_principles", [
                "キャラクターの個性を重視",
                "視覚的な統一感の維持",
                "読者層に適した表現"
            ]),
            "consistency_notes": style_data.get("consistency_notes", [
                "髪型と服装の統一感を保つ",
                "表情の描き方を一貫させる",
                "体型比率を統一する"
            ]),
            "reference_notes": style_data.get("reference_notes", [])
        }

        # Character summaries for next phases
        character_summaries = []
        visual_references = []

        for char in processed_characters:
            summary = {
                "name": char["name"],
                "archetype": char["archetype"],
                "brief_description": f"{char['appearance'].get('hair_color', '茶')}髪の{char.get('age_group', '若い')}キャラクター"
            }
            character_summaries.append(summary)

            visual_ref = {
                "name": char["name"],
                "appearance": char["appearance"],
                "style_preference": char["visual_style_preference"],
                "complexity": char["design_complexity"]
            }
            visual_references.append(visual_ref)

        # Build final output
        character_output = {
            "characters": processed_characters,
            "relationships": processed_relationships,
            "style_guide": style_guide,
            "total_characters": len(processed_characters),
            "main_characters_count": len([c for c in processed_characters if c["role_importance"] >= 0.7]),
            "design_complexity_score": ai_data.get("design_complexity_score", 0.6),
            "visual_consistency_score": ai_data.get("visual_consistency_score", 0.8),
            "character_summaries": character_summaries,
            "visual_references": visual_references,
            "generation_timestamp": datetime.utcnow().isoformat(),
            "ai_model_used": "gpt-4o-mini",  # In production, this would be the actual model
            "processing_time": 2.5  # This would be calculated
        }

        return character_output

    async def _processor_based_analysis(self, phase1_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback processor-based analysis when AI parsing fails."""

        # Extract necessary data from Phase 1
        genre_analysis = phase1_result.get("genre_analysis", {})
        theme_analysis = phase1_result.get("theme_analysis", {})
        target_audience = phase1_result.get("target_audience", "general")
        original_text = phase1_result.get("original_text", "")

        primary_genre = genre_analysis.get("primary_genre", "general")
        main_themes = theme_analysis.get("main_themes", [])

        # Use character analyzer to generate characters
        characters = await self.character_analyzer.analyze_characters(
            text=original_text,
            genre=primary_genre,
            themes=main_themes,
            target_audience=target_audience
        )

        # Analyze relationships
        relationships = self.character_analyzer.analyze_relationships(characters)

        # Convert relationships to dict format
        relationships_dict = []
        for rel in relationships:
            relationships_dict.append({
                "character1_name": rel.character1_name,
                "character2_name": rel.character2_name,
                "relationship_type": rel.relationship_type,
                "relationship_strength": rel.relationship_strength,
                "description": rel.description
            })

        # Generate visual style guide
        visual_style = self.genre_style_mapping.get(primary_genre, VisualStyleType.SHOUNEN)
        style_guide = await self.visual_generator.generate_style_guide(
            characters=characters,
            genre=primary_genre,
            target_audience=target_audience,
            visual_style=visual_style
        )

        # Generate visual appearances for characters
        enhanced_characters = []
        for char in characters:
            enhanced_char = char.copy()
            appearance = await self.visual_generator.generate_character_appearance(
                character_info=char,
                visual_style=visual_style,
                style_guide=style_guide
            )
            enhanced_char["appearance"] = appearance
            enhanced_char["visual_style_preference"] = visual_style.value
            enhanced_char["design_complexity"] = 0.6

            # Validate and fix personality data if needed (same logic as AI-based method)
            personality_data = enhanced_char.get("personality", {})
            if not personality_data.get("main_traits") or not personality_data.get("motivation"):
                self.logger.warning(f"Incomplete personality for {enhanced_char.get('name', 'unknown')} in processor method, creating default personality")
                # Create default personality with required fields
                personality_data = {
                    "main_traits": [
                        {
                            "trait": "勇敢",
                            "strength": 0.8,
                            "description": "勇敢という特徴を持つ"
                        },
                        {
                            "trait": "親切",
                            "strength": 0.7,
                            "description": "親切という特徴を持つ"
                        }
                    ],
                    "motivation": "仲間を守りたい",
                    "fears": ["失敗への恐れ"],
                    "strengths": ["勇敢", "親切"],
                    "weaknesses": ["完璧主義"],
                    "behavioral_patterns": ["困っている人を見捨てられない"],
                    "speech_patterns": ["丁寧語を使う"],
                    "core_values": ["友情", "正義"],
                    "character_arc": "仲間との絆を深める"
                }
                enhanced_char["personality"] = personality_data

            enhanced_characters.append(enhanced_char)

        # Character summaries for next phases
        character_summaries = []
        visual_references = []

        for char in enhanced_characters:
            summary = {
                "name": char["name"],
                "archetype": char["archetype"],
                "brief_description": f"{char.get('gender', '不明')}の{char.get('age_group', '若い')}キャラクター"
            }
            character_summaries.append(summary)

            visual_ref = {
                "name": char["name"],
                "appearance": char.get("appearance", {}),
                "style_preference": char.get("visual_style_preference", visual_style.value),
                "complexity": char.get("design_complexity", 0.6)
            }
            visual_references.append(visual_ref)

        # Build output
        character_output = {
            "characters": enhanced_characters,
            "relationships": relationships_dict,
            "style_guide": style_guide,
            "total_characters": len(enhanced_characters),
            "main_characters_count": len([c for c in enhanced_characters if c.get("role_importance", 0.5) >= 0.7]),
            "design_complexity_score": 0.6,
            "visual_consistency_score": 0.8,
            "character_summaries": character_summaries,
            "visual_references": visual_references,
            "generation_timestamp": datetime.utcnow().isoformat(),
            "ai_model_used": "processor_based_fallback",
            "processing_time": 1.5
        }

        return character_output

    async def _generate_preview(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview data for Phase 2."""

        characters = output_data.get("characters", [])
        style_guide = output_data.get("style_guide", {})

        preview = {
            "phase_name": "キャラクターデザイン",
            "summary": f"キャラクター数: {len(characters)}人",
            "key_insights": [],
            "visual_elements": []
        }

        # Add key insights
        main_characters = [c for c in characters if c.get("role_importance", 0.5) >= 0.7]
        if main_characters:
            preview["key_insights"].append(f"主要キャラクター: {len(main_characters)}人")

        protagonist = next((c for c in characters if c.get("archetype") == "protagonist"), None)
        if protagonist:
            preview["key_insights"].append(f"主人公: {protagonist.get('name', '無名')}")

        # Add visual elements
        overall_style = style_guide.get("overall_style")
        if overall_style:
            preview["visual_elements"].append(f"ビジュアルスタイル: {overall_style}")

        color_palette = style_guide.get("color_palette", {})
        if color_palette.get("primary"):
            preview["visual_elements"].append(f"主要カラー: {color_palette['primary']}")

        # Character diversity info
        genders = [c.get("gender", "unknown") for c in characters]
        gender_counts = {g: genders.count(g) for g in set(genders)}
        if gender_counts:
            gender_info = ", ".join([f"{g}: {count}人" for g, count in gender_counts.items()])
            preview["visual_elements"].append(f"性別構成: {gender_info}")

        return preview

    async def apply_character_feedback(
        self,
        output_data: Dict[str, Any],
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply feedback specifically for character adjustments."""

        feedback_type = feedback.get("type", "general")

        if feedback_type == "character_modification":
            # Modify specific character
            character_name = feedback.get("character_name")
            modifications = feedback.get("modifications", {})

            characters = output_data.get("characters", [])
            for char in characters:
                if char.get("name") == character_name:
                    for key, value in modifications.items():
                        if key in char:
                            char[key] = value
                    char["last_modified"] = datetime.utcnow().isoformat()
                    break

        elif feedback_type == "style_adjustment":
            # Adjust style guide
            style_adjustments = feedback.get("adjustments", {})
            style_guide = output_data.get("style_guide", {})

            for key, value in style_adjustments.items():
                if key in style_guide:
                    style_guide[key] = value
            style_guide["last_modified"] = datetime.utcnow().isoformat()

        elif feedback_type == "add_character":
            # Add new character
            new_character = feedback.get("character_data", {})
            if new_character:
                characters = output_data.get("characters", [])
                new_character["added_via_feedback"] = True
                new_character["creation_timestamp"] = datetime.utcnow().isoformat()
                characters.append(new_character)
                output_data["total_characters"] = len(characters)

        # Update modification timestamp
        output_data["last_feedback_applied"] = datetime.utcnow().isoformat()
        output_data["feedback_history"] = output_data.get("feedback_history", [])
        output_data["feedback_history"].append({
            "type": feedback_type,
            "timestamp": datetime.utcnow().isoformat(),
            "feedback": feedback
        })

        return output_data
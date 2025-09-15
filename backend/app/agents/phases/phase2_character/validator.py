"""Validator for Phase 2: Character Design."""

from typing import Dict, Any, List
from app.agents.base.validator import BaseValidator, ValidationResult
from .schemas import (
    CharacterDesignOutput,
    CharacterProfile,
    CharacterArchetypeType,
    GenderType,
    AgeGroupType,
    VisualStyleType,
    CHARACTER_ARCHETYPES
)


class Phase2Validator(BaseValidator):
    """Validator for Phase 2 character design output."""

    def __init__(self):
        super().__init__("Character Design")

        # Phase 2 specific required fields
        self.required_fields.extend([
            "characters",
            "relationships",
            "style_guide",
            "total_characters",
            "character_summaries"
        ])

        # Character validation rules
        self.min_characters = 1
        self.max_characters = 15
        self.required_character_fields = [
            "name", "archetype", "gender", "age_group",
            "appearance", "personality", "role_importance"
        ]

        # Archetype balance requirements
        self.required_archetypes = [CharacterArchetypeType.PROTAGONIST]
        self.recommended_archetypes = [
            CharacterArchetypeType.SIDEKICK,
            CharacterArchetypeType.ANTAGONIST
        ]

    async def validate(self, output_data: Dict[str, Any]) -> ValidationResult:
        """Validate Phase 2 output with comprehensive checks."""

        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.phase_name = "Phase 2: Character Design"
        result.is_valid = True

        # Basic field validation
        basic_validation = self._validate_required_fields(output_data)
        if not basic_validation.is_valid:
            result.merge(basic_validation)
            return result

        # Character-specific validations
        character_validation = await self._validate_characters(output_data.get("characters", []))
        result.merge(character_validation)

        # Relationship validation
        relationship_validation = self._validate_relationships(
            output_data.get("relationships", []),
            output_data.get("characters", [])
        )
        result.merge(relationship_validation)

        # Style guide validation
        style_validation = self._validate_style_guide(output_data.get("style_guide", {}))
        result.merge(style_validation)

        # Character balance validation
        balance_validation = self._validate_character_balance(output_data.get("characters", []))
        result.merge(balance_validation)

        # Consistency validation
        consistency_validation = self._validate_consistency(output_data)
        result.merge(consistency_validation)

        return result

    async def _validate_characters(self, characters: List[Dict[str, Any]]) -> ValidationResult:
        """Validate individual characters."""

        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.is_valid = True

        if not characters:
            result.add_error("characters", "No characters provided")
            return result

        if len(characters) < self.min_characters:
            result.add_error("characters", f"Too few characters: {len(characters)} (minimum: {self.min_characters})")

        if len(characters) > self.max_characters:
            result.add_warning("character_count", f"Many characters: {len(characters)} (recommended max: {self.max_characters})")

        # Validate each character
        character_names = set()
        for i, char in enumerate(characters):
            char_result = self._validate_single_character(char, i)
            result.merge(char_result)

            # Check for duplicate names
            name = char.get("name", f"Character_{i}")
            if name in character_names:
                result.add_error("character_name", f"Duplicate character name: {name}")
            character_names.add(name)

        return result

    def _validate_single_character(self, character: Dict[str, Any], index: int) -> ValidationResult:
        """Validate a single character's data."""

        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.is_valid = True

        char_name = character.get("name", f"Character_{index}")

        # Required fields check
        missing_fields = [field for field in self.required_character_fields if field not in character]
        if missing_fields:
            result.add_error("character_fields", f"Character '{char_name}' missing fields: {missing_fields}")

        # Validate archetype
        archetype = character.get("archetype")
        if archetype:
            try:
                CharacterArchetypeType(archetype)
            except ValueError:
                result.add_error("character_archetype", f"Character '{char_name}' has invalid archetype: {archetype}")

        # Validate gender
        gender = character.get("gender")
        if gender:
            try:
                GenderType(gender)
            except ValueError:
                result.add_error("character_gender", f"Character '{char_name}' has invalid gender: {gender}")

        # Validate age group
        age_group = character.get("age_group")
        if age_group:
            try:
                AgeGroupType(age_group)
            except ValueError:
                result.add_error("character_age_group", f"Character '{char_name}' has invalid age_group: {age_group}")

        # Validate role importance
        role_importance = character.get("role_importance")
        if role_importance is not None:
            if not isinstance(role_importance, (int, float)) or not 0.0 <= role_importance <= 1.0:
                result.add_error("character_role_importance", f"Character '{char_name}' has invalid role_importance: {role_importance} (must be 0.0-1.0)")

        # Validate appearance structure
        appearance = character.get("appearance", {})
        if appearance:
            appearance_result = self._validate_appearance(appearance, char_name)
            result.merge(appearance_result)

        # Validate personality structure
        personality = character.get("personality", {})
        if personality:
            personality_result = self._validate_personality(personality, char_name)
            result.merge(personality_result)

        return result

    def _validate_appearance(self, appearance: Dict[str, Any], char_name: str) -> ValidationResult:
        """Validate character appearance data."""

        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.is_valid = True

        required_appearance_fields = ["hair_color", "eye_color", "height", "build"]
        missing_fields = [field for field in required_appearance_fields if field not in appearance]
        if missing_fields:
            result.add_warning("character_appearance", f"Character '{char_name}' appearance missing: {missing_fields}")

        # Validate appearance description completeness
        description_fields = ["hair_style", "clothing_style", "default_expression"]
        missing_descriptions = [field for field in description_fields if not appearance.get(field)]
        if missing_descriptions:
            result.add_info("character_details", f"Character '{char_name}' could have more detailed: {missing_descriptions}")

        return result

    def _validate_personality(self, personality: Dict[str, Any], char_name: str) -> ValidationResult:
        """Validate character personality data."""

        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.is_valid = True

        # Check for main personality components
        required_personality_fields = ["main_traits", "motivation"]
        missing_fields = [field for field in required_personality_fields if not personality.get(field)]
        if missing_fields:
            result.add_error("character_personality", f"Character '{char_name}' personality missing: {missing_fields}")

        # Validate traits structure
        main_traits = personality.get("main_traits", [])
        if isinstance(main_traits, list) and len(main_traits) < 2:
            result.add_warning("character_personality", f"Character '{char_name}' has few personality traits: {len(main_traits)}")

        # Check motivation depth
        motivation = personality.get("motivation", "")
        if isinstance(motivation, str) and len(motivation) < 10:
            result.add_warning("character_motivation", f"Character '{char_name}' has brief motivation description")

        return result

    def _validate_relationships(self, relationships: List[Dict[str, Any]], characters: List[Dict[str, Any]]) -> ValidationResult:
        """Validate character relationships."""

        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.is_valid = True

        if not relationships:
            result.add_info("character_relationships", "No character relationships defined")
            return result

        # Get character names for reference validation
        character_names = {char.get("name") for char in characters if char.get("name")}

        for i, rel in enumerate(relationships):
            # Check required relationship fields
            required_fields = ["character1_name", "character2_name", "relationship_type"]
            missing_fields = [field for field in required_fields if not rel.get(field)]
            if missing_fields:
                result.add_error("character_relationships", f"Relationship {i} missing: {missing_fields}")
                continue

            # Validate character references
            char1 = rel.get("character1_name")
            char2 = rel.get("character2_name")

            if char1 not in character_names:
                result.add_error(f"Relationship {i} references unknown character: {char1}")
            if char2 not in character_names:
                result.add_error(f"Relationship {i} references unknown character: {char2}")

            if char1 == char2:
                result.add_error(f"Relationship {i} has same character in both positions: {char1}")

        return result

    def _validate_style_guide(self, style_guide: Dict[str, Any]) -> ValidationResult:
        """Validate visual style guide."""

        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.is_valid = True

        if not style_guide:
            result.add_error("Style guide is required")
            return result

        required_style_fields = ["overall_style", "color_palette", "design_principles"]
        missing_fields = [field for field in required_style_fields if not style_guide.get(field)]
        if missing_fields:
            result.add_error(f"Style guide missing: {missing_fields}")

        # Validate overall style
        overall_style = style_guide.get("overall_style")
        if overall_style:
            try:
                VisualStyleType(overall_style)
            except ValueError:
                result.add_error(f"Invalid visual style: {overall_style}")

        # Check color palette completeness
        color_palette = style_guide.get("color_palette", {})
        if isinstance(color_palette, dict) and len(color_palette) < 3:
            result.add_warning("color_palette", "Color palette seems limited (less than 3 colors)")

        return result

    def _validate_character_balance(self, characters: List[Dict[str, Any]]) -> ValidationResult:
        """Validate character archetype balance."""

        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.is_valid = True

        # Count archetypes
        archetype_counts = {}
        for char in characters:
            archetype = char.get("archetype")
            if archetype:
                archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1

        # Check required archetypes
        missing_required = [arch.value for arch in self.required_archetypes if arch.value not in archetype_counts]
        if missing_required:
            result.add_error(f"Missing required archetypes: {missing_required}")

        # Check recommended archetypes
        missing_recommended = [arch.value for arch in self.recommended_archetypes if arch.value not in archetype_counts]
        if missing_recommended and len(characters) > 2:
            result.add_warning("character_archetypes", f"Consider adding archetypes: {missing_recommended}")

        # Check for excessive protagonists
        protagonist_count = archetype_counts.get(CharacterArchetypeType.PROTAGONIST.value, 0)
        if protagonist_count > 2:
            result.add_warning("character_balance", f"Multiple protagonists detected: {protagonist_count}")
        elif protagonist_count == 0:
            result.add_error("No protagonist character found")

        return result

    def _validate_consistency(self, output_data: Dict[str, Any]) -> ValidationResult:
        """Validate overall consistency."""

        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        result.is_valid = True

        characters = output_data.get("characters", [])
        total_characters = output_data.get("total_characters", 0)

        # Check character count consistency
        actual_count = len(characters)
        if actual_count != total_characters:
            result.add_warning("character_consistency", f"Character count mismatch: actual={actual_count}, reported={total_characters}")

        # Check character summaries consistency
        character_summaries = output_data.get("character_summaries", [])
        if len(character_summaries) != actual_count:
            result.add_warning("character_summaries", f"Character summaries count mismatch: summaries={len(character_summaries)}, characters={actual_count}")

        # Validate generation metadata
        timestamp = output_data.get("generation_timestamp")
        if not timestamp:
            result.add_info("generation_timestamp", "Missing generation timestamp")

        ai_model = output_data.get("ai_model_used")
        if not ai_model:
            result.add_info("ai_model_info", "Missing AI model information")

        return result

    def get_validation_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of validation results."""

        characters = output_data.get("characters", [])

        return {
            "total_characters": len(characters),
            "archetype_distribution": self._get_archetype_distribution(characters),
            "completeness_score": self._calculate_completeness_score(output_data),
            "consistency_score": self._calculate_consistency_score(output_data),
            "validation_passed": True  # This would be set by the actual validation
        }

    def _get_archetype_distribution(self, characters: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of character archetypes."""

        distribution = {}
        for char in characters:
            archetype = char.get("archetype", "unknown")
            distribution[archetype] = distribution.get(archetype, 0) + 1

        return distribution

    def _calculate_completeness_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate overall data completeness score."""

        characters = output_data.get("characters", [])
        if not characters:
            return 0.0

        total_score = 0.0
        for char in characters:
            char_score = 0.0

            # Basic fields (50% of score)
            basic_fields = ["name", "archetype", "gender", "age_group"]
            char_score += 0.5 * sum(1 for field in basic_fields if char.get(field)) / len(basic_fields)

            # Appearance (25% of score)
            appearance = char.get("appearance", {})
            appearance_fields = ["hair_color", "eye_color", "height", "build", "clothing_style"]
            char_score += 0.25 * sum(1 for field in appearance_fields if appearance.get(field)) / len(appearance_fields)

            # Personality (25% of score)
            personality = char.get("personality", {})
            personality_fields = ["main_traits", "motivation", "background_summary"]
            char_score += 0.25 * sum(1 for field in personality_fields if personality.get(field)) / len(personality_fields)

            total_score += char_score

        return total_score / len(characters)

    def _calculate_consistency_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate data consistency score."""

        score = 1.0

        # Check count consistency
        characters = output_data.get("characters", [])
        total_characters = output_data.get("total_characters", 0)
        if len(characters) != total_characters:
            score -= 0.1

        # Check summaries consistency
        character_summaries = output_data.get("character_summaries", [])
        if len(character_summaries) != len(characters):
            score -= 0.1

        # Check style guide presence
        style_guide = output_data.get("style_guide", {})
        if not style_guide or not style_guide.get("overall_style"):
            score -= 0.2

        return max(0.0, score)

    async def _validate_phase_specific(
        self,
        output: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate Phase 2 specific requirements."""

        # Validate characters
        character_validation = await self._validate_characters(output.get("characters", []))
        result.merge(character_validation)

        # Validate relationships
        relationship_validation = self._validate_relationships(
            output.get("relationships", []),
            output.get("characters", [])
        )
        result.merge(relationship_validation)

        # Validate style guide
        style_validation = self._validate_style_guide(output.get("style_guide", {}))
        result.merge(style_validation)

        # Validate character balance
        balance_validation = self._validate_character_balance(output.get("characters", []))
        result.merge(balance_validation)

        # Validate consistency
        consistency_validation = self._validate_consistency(output)
        result.merge(consistency_validation)
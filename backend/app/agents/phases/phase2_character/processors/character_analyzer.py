"""Character Analysis Processor for Phase 2."""

import re
from typing import Dict, List, Any, Optional
from app.core.logging import LoggerMixin
from ..schemas import (
    CharacterProfile,
    CharacterArchetypeType,
    GenderType,
    AgeGroupType,
    CharacterPersonality,
    PersonalityTrait,
    CharacterRelationship,
    CHARACTER_ARCHETYPES
)


class CharacterAnalyzer(LoggerMixin):
    """Analyzes and extracts character information from story text."""

    def __init__(self):
        """Initialize character analyzer."""
        super().__init__()

        # Character archetype templates
        self.archetype_templates = CHARACTER_ARCHETYPES

        # Age mapping for different target audiences
        self.age_mappings = {
            "children": 10,
            "teens": 16,
            "young_adults": 22,
            "adults": 30,
            "general": 18
        }

        # Gender detection keywords
        self.male_indicators = ["彼", "男", "少年", "青年", "兄", "父", "息子"]
        self.female_indicators = ["彼女", "女", "少女", "女性", "姉", "母", "娘"]

        # Personality templates by genre and archetype
        self.personality_templates = {
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

        # Motivation mapping
        self.motivation_mappings = {
            "成長": "より強くなること",
            "友情": "仲間を守ること",
            "愛": "愛する人のため",
            "正義": "悪を倒すこと",
            "冒険": "未知の世界を探検すること",
            "復讐": "失ったものを取り戻すこと"
        }

    async def analyze_characters(
        self,
        text: str,
        genre: str,
        themes: List[str],
        target_audience: str
    ) -> List[Dict[str, Any]]:
        """Analyze text and generate character profiles."""

        self.logger.info(f"Analyzing characters for genre: {genre}, audience: {target_audience}")

        characters = []

        # Always create a protagonist
        protagonist = await self._create_protagonist(text, genre, themes, target_audience)
        characters.append(protagonist)

        # Add sidekick if needed
        if self._needs_sidekick(genre, themes):
            sidekick = await self._create_sidekick(text, genre, target_audience)
            characters.append(sidekick)

        # Add antagonist if conflict detected
        if self._has_conflict(text, themes):
            antagonist = await self._create_antagonist(text, genre, themes, target_audience)
            characters.append(antagonist)

        # Add supporting characters based on story complexity
        supporting_chars = await self._create_supporting_characters(text, genre, target_audience, len(characters))
        characters.extend(supporting_chars)

        self.logger.info(f"Generated {len(characters)} characters")
        return characters

    async def _create_protagonist(
        self,
        text: str,
        genre: str,
        themes: List[str],
        target_audience: str
    ) -> Dict[str, Any]:
        """Create the main protagonist character."""

        name = self._extract_protagonist_name(text) or "主人公"
        age = self._determine_age(target_audience)
        gender = self._detect_gender(text, is_protagonist=True)
        personality = self._generate_personality(genre, "protagonist")
        motivation = self._extract_motivation(text, themes)

        return {
            "name": name,
            "archetype": CharacterArchetypeType.PROTAGONIST,
            "gender": GenderType(gender.lower()) if gender.lower() in [g.value for g in GenderType] else GenderType.UNKNOWN,
            "age_group": self._age_to_group(age),
            "age_specific": age,
            "personality": self._build_personality_profile(personality, motivation),
            "role_importance": 1.0,  # Protagonist is always max importance
            "screen_time_estimate": 0.8,  # High screen time
            "background_summary": "物語の中心人物"
        }

    async def _create_sidekick(
        self,
        text: str,
        genre: str,
        target_audience: str
    ) -> Dict[str, Any]:
        """Create a sidekick character."""

        age = self._determine_age(target_audience, offset=-2)
        gender = self._detect_gender(text, is_protagonist=False)
        personality = self._generate_personality(genre, "sidekick")

        return {
            "name": "相棒",
            "archetype": CharacterArchetypeType.SIDEKICK,
            "gender": GenderType(gender.lower()) if gender.lower() in [g.value for g in GenderType] else GenderType.UNKNOWN,
            "age_group": self._age_to_group(age),
            "age_specific": age,
            "personality": self._build_personality_profile(personality, "主人公をサポートする"),
            "role_importance": 0.7,
            "screen_time_estimate": 0.5,
            "background_summary": "主人公を支える仲間"
        }

    async def _create_antagonist(
        self,
        text: str,
        genre: str,
        themes: List[str],
        target_audience: str
    ) -> Dict[str, Any]:
        """Create an antagonist character."""

        age = self._determine_age(target_audience, offset=2)
        gender = self._detect_gender(text, is_antagonist=True)
        personality = self._generate_personality(genre, "antagonist")
        motivation = self._generate_antagonist_motivation(themes)

        return {
            "name": "ライバル",
            "archetype": CharacterArchetypeType.ANTAGONIST,
            "gender": GenderType(gender.lower()) if gender.lower() in [g.value for g in GenderType] else GenderType.UNKNOWN,
            "age_group": self._age_to_group(age),
            "age_specific": age,
            "personality": self._build_personality_profile(personality, motivation),
            "role_importance": 0.8,
            "screen_time_estimate": 0.4,
            "background_summary": "主人公と対立する存在"
        }

    async def _create_supporting_characters(
        self,
        text: str,
        genre: str,
        target_audience: str,
        existing_count: int
    ) -> List[Dict[str, Any]]:
        """Create supporting characters based on story needs."""

        supporting_chars = []

        # Add mentor if appropriate for genre
        if genre in ["fantasy", "action"] and existing_count < 5:
            mentor = {
                "name": "師匠",
                "archetype": CharacterArchetypeType.MENTOR,
                "gender": GenderType.MALE,  # Default
                "age_group": AgeGroupType.MIDDLE_AGED,
                "age_specific": 45,
                "personality": self._build_personality_profile(["知恵", "経験豊富", "忍耐強い"], "主人公を導く"),
                "role_importance": 0.5,
                "screen_time_estimate": 0.2,
                "background_summary": "主人公の指導者"
            }
            supporting_chars.append(mentor)

        # Add love interest for appropriate genres and audiences
        if genre in ["romance", "slice_of_life"] and target_audience in ["teens", "young_adults", "adults"]:
            love_interest = {
                "name": "想い人",
                "archetype": CharacterArchetypeType.LOVE_INTEREST,
                "gender": GenderType.FEMALE,  # Default opposite
                "age_group": self._age_to_group(self._determine_age(target_audience)),
                "age_specific": self._determine_age(target_audience),
                "personality": self._build_personality_profile(["魅力的", "独立心", "思いやり"], "自分の道を歩む"),
                "role_importance": 0.6,
                "screen_time_estimate": 0.3,
                "background_summary": "主人公の恋愛対象"
            }
            supporting_chars.append(love_interest)

        return supporting_chars

    def analyze_relationships(
        self,
        characters: List[Dict[str, Any]]
    ) -> List[CharacterRelationship]:
        """Analyze relationships between characters."""

        relationships = []

        for i, char1 in enumerate(characters):
            for j, char2 in enumerate(characters):
                if i < j:  # Avoid duplicates and self-relationships
                    relationship_type = self._determine_relationship(
                        char1.get("archetype", "").replace("CharacterArchetypeType.", ""),
                        char2.get("archetype", "").replace("CharacterArchetypeType.", "")
                    )

                    if relationship_type:
                        relationships.append(CharacterRelationship(
                            character1_name=char1.get("name", ""),
                            character2_name=char2.get("name", ""),
                            relationship_type=relationship_type,
                            relationship_strength=self._calculate_relationship_strength(char1, char2),
                            description=f"{char1.get('name')}と{char2.get('name')}の{relationship_type}"
                        ))

        return relationships

    def _extract_protagonist_name(self, text: str) -> Optional[str]:
        """Extract protagonist name from text."""

        # Pattern for names in Japanese text (quoted names)
        name_pattern = r'「([^」]+)」'
        matches = re.findall(name_pattern, text[:500])

        if matches:
            # Return first match that looks like a name
            for match in matches:
                if len(match) <= 10:  # Names are typically short
                    return match

        # Try to find katakana names (often used for characters)
        katakana_pattern = r'[ァ-ヶー]{2,8}'
        katakana_matches = re.findall(katakana_pattern, text[:500])

        if katakana_matches:
            return katakana_matches[0]

        return None

    def _determine_age(self, target_audience: str, offset: int = 0) -> int:
        """Determine character age based on target audience."""

        base_age = self.age_mappings.get(target_audience, 18)
        return max(8, min(60, base_age + offset))

    def _age_to_group(self, age: int) -> AgeGroupType:
        """Convert numeric age to age group."""

        if age <= 12:
            return AgeGroupType.CHILD
        elif age <= 17:
            return AgeGroupType.TEENAGER
        elif age <= 25:
            return AgeGroupType.YOUNG_ADULT
        elif age <= 40:
            return AgeGroupType.ADULT
        elif age <= 60:
            return AgeGroupType.MIDDLE_AGED
        else:
            return AgeGroupType.ELDERLY

    def _detect_gender(
        self,
        text: str,
        is_protagonist: bool = False,
        is_antagonist: bool = False
    ) -> str:
        """Detect character gender from text clues."""

        male_count = sum(1 for word in self.male_indicators if word in text)
        female_count = sum(1 for word in self.female_indicators if word in text)

        if male_count > female_count:
            return "male"
        elif female_count > male_count:
            return "female"
        else:
            # Default based on role and common patterns
            if is_protagonist:
                return "male"  # Default protagonist
            elif is_antagonist:
                return "male"  # Default antagonist
            else:
                return "unknown"

    def _generate_personality(self, genre: str, role: str) -> List[str]:
        """Generate personality traits based on genre and role."""

        template = self.personality_templates.get((genre, role))
        if template:
            return template.copy()

        # Default personality traits
        default_traits = {
            "protagonist": ["個性的", "魅力的", "成長する"],
            "sidekick": ["忠実", "サポート力", "ユーモア"],
            "antagonist": ["複雑", "野心的", "対立的"],
            "mentor": ["知恵", "経験", "指導力"],
            "love_interest": ["魅力", "独立心", "理解力"]
        }

        return default_traits.get(role, ["個性的", "魅力的", "複雑"])

    def _extract_motivation(self, text: str, themes: List[str]) -> str:
        """Extract character motivation from text and themes."""

        for theme in themes:
            if theme in self.motivation_mappings:
                return self.motivation_mappings[theme]

        # Analyze text for motivation keywords
        motivation_keywords = {
            "強く": "より強くなること",
            "守る": "大切なものを守ること",
            "見つける": "失ったものを見つけること",
            "倒す": "敵を倒すこと",
            "助ける": "困っている人を助けること"
        }

        for keyword, motivation in motivation_keywords.items():
            if keyword in text:
                return motivation

        return "目標を達成すること"

    def _generate_antagonist_motivation(self, themes: List[str]) -> str:
        """Generate antagonist motivation based on themes."""

        antagonist_motivations = {
            "復讐": "過去の恨みを晴らす",
            "権力": "世界を支配する",
            "愛": "愛する人を取り戻す",
            "正義": "自分なりの正義を貫く",
            "生存": "生き残るため"
        }

        for theme in themes:
            if theme in antagonist_motivations:
                return antagonist_motivations[theme]

        return "自分の目的を達成する"

    def _build_personality_profile(
        self,
        traits: List[str],
        motivation: str
    ) -> Dict[str, Any]:
        """Build a complete personality profile."""

        personality_traits = []
        for i, trait in enumerate(traits[:5]):  # Limit to 5 traits
            personality_traits.append(PersonalityTrait(
                trait=trait,
                strength=0.8 - (i * 0.1),  # Decreasing strength
                description=f"{trait}という特徴を持つ"
            ).dict())

        return {
            "main_traits": personality_traits,
            "motivation": motivation,
            "fears": ["失敗への恐れ"],
            "strengths": traits[:2],
            "weaknesses": ["完璧主義"],
            "speech_pattern": "普通の話し方",
            "background_summary": "詳細な背景は物語の中で明らかになる"
        }

    def _needs_sidekick(self, genre: str, themes: List[str]) -> bool:
        """Determine if story needs a sidekick character."""

        sidekick_genres = ["fantasy", "action", "mystery", "slice_of_life"]
        return genre in sidekick_genres or "友情" in themes

    def _has_conflict(self, text: str, themes: List[str]) -> bool:
        """Determine if story has conflict requiring an antagonist."""

        conflict_indicators = ["戦い", "対立", "敵", "悪", "戦う", "倒す"]
        conflict_themes = ["正義", "復讐", "戦争", "競争"]

        text_has_conflict = any(indicator in text for indicator in conflict_indicators)
        theme_has_conflict = any(theme in themes for theme in conflict_themes)

        return text_has_conflict or theme_has_conflict

    def _determine_relationship(self, archetype1: str, archetype2: str) -> Optional[str]:
        """Determine relationship type between two archetypes."""

        relationship_map = {
            ("protagonist", "sidekick"): "親友",
            ("protagonist", "mentor"): "師弟関係",
            ("protagonist", "antagonist"): "敵対関係",
            ("protagonist", "love_interest"): "恋愛関係",
            ("sidekick", "mentor"): "先輩後輩",
            ("mentor", "antagonist"): "因縁の関係",
            ("sidekick", "antagonist"): "対立関係"
        }

        # Try both orderings
        key1 = (archetype1.lower(), archetype2.lower())
        key2 = (archetype2.lower(), archetype1.lower())

        return relationship_map.get(key1) or relationship_map.get(key2)

    def _calculate_relationship_strength(self, char1: Dict[str, Any], char2: Dict[str, Any]) -> float:
        """Calculate relationship strength between two characters."""

        # Base strength on role importance
        importance1 = char1.get("role_importance", 0.5)
        importance2 = char2.get("role_importance", 0.5)

        # Higher importance characters have stronger relationships
        base_strength = (importance1 + importance2) / 2

        # Adjust based on archetype compatibility
        archetype1 = char1.get("archetype", "")
        archetype2 = char2.get("archetype", "")

        # Protagonist relationships are generally stronger
        if "protagonist" in [archetype1, archetype2]:
            base_strength += 0.2

        # Antagonist relationships are intense
        if "antagonist" in [archetype1, archetype2]:
            base_strength += 0.1

        return min(1.0, max(0.1, base_strength))
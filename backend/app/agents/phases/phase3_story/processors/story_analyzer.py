"""Story Analysis Processor for Phase 3."""

import math
from typing import Dict, List, Any, Optional, Tuple
from app.core.logging import LoggerMixin
from ..schemas import (
    StoryStructure,
    ActStructure,
    PlotProgression,
    SceneDetails,
    CharacterArc,
    ThemeDevelopment,
    TensionPoint,
    TensionCurve,
    EmotionalJourney,
    StoryBeat,
    PacingAnalysis,
    NarrativeFlow,
    ConflictAnalysis,
    ThemeIntegration,
    StoryStructureType,
    PacingType,
    ScenePurposeType,
    EmotionalBeatType,
    VisualStyleType,
    TransitionType,
    StoryFunctionType,
    STORY_STRUCTURE_TEMPLATES,
    GENRE_PACING_PATTERNS
)


class StoryAnalyzer(LoggerMixin):
    """Analyzes and structures story elements for manga production."""

    def __init__(self):
        """Initialize story analyzer."""
        super().__init__()

        # Story structure templates
        self.structure_templates = STORY_STRUCTURE_TEMPLATES
        self.genre_pacing = GENRE_PACING_PATTERNS

        # Story beat mapping for different structures
        self.story_beats = {
            StoryStructureType.THREE_ACT: [
                "setup", "inciting_incident", "plot_point_1", "midpoint",
                "plot_point_2", "climax", "resolution"
            ],
            StoryStructureType.KISHOOTENKETSU: [
                "introduction", "development", "twist", "conclusion"
            ],
            StoryStructureType.HERO_JOURNEY: [
                "call", "refusal", "mentor", "threshold", "tests",
                "ordeal", "reward", "road_back", "resurrection", "elixir"
            ]
        }

        # Emotional progression templates
        self.emotional_patterns = {
            "action": [EmotionalBeatType.EXCITEMENT, EmotionalBeatType.TENSION, EmotionalBeatType.FEAR,
                      EmotionalBeatType.TRIUMPH, EmotionalBeatType.RELIEF],
            "romance": [EmotionalBeatType.HOPE, EmotionalBeatType.JOY, EmotionalBeatType.TENSION,
                       EmotionalBeatType.SADNESS, EmotionalBeatType.JOY],
            "mystery": [EmotionalBeatType.MYSTERY, EmotionalBeatType.TENSION, EmotionalBeatType.SURPRISE,
                       EmotionalBeatType.FEAR, EmotionalBeatType.RELIEF],
            "fantasy": [EmotionalBeatType.EXCITEMENT, EmotionalBeatType.MYSTERY, EmotionalBeatType.FEAR,
                       EmotionalBeatType.TRIUMPH, EmotionalBeatType.JOY],
            "slice_of_life": [EmotionalBeatType.PEACE, EmotionalBeatType.JOY, EmotionalBeatType.SADNESS,
                             EmotionalBeatType.HOPE, EmotionalBeatType.PEACE]
        }

        self.logger.info("Story Analyzer initialized")

    async def analyze_story_structure(
        self,
        genre: str,
        themes: List[str],
        estimated_pages: int,
        characters: List[Dict[str, Any]]
    ) -> StoryStructure:
        """Determine appropriate story structure."""

        structure_type = self._determine_structure_type(genre, themes, estimated_pages)
        acts = await self._create_act_structure(structure_type, estimated_pages, genre)

        return StoryStructure(
            type=structure_type,
            acts=acts,
            total_acts=len(acts),
            structure_rationale=self._explain_structure_choice(structure_type, genre, themes),
            adaptation_notes=self._generate_adaptation_notes(structure_type, genre)
        )

    def _determine_structure_type(
        self,
        genre: str,
        themes: List[str],
        estimated_pages: int
    ) -> StoryStructureType:
        """Determine the most appropriate story structure."""

        # Short stories work well with Kishōtenketsu
        if estimated_pages <= 20:
            return StoryStructureType.KISHOOTENKETSU

        # Action and adventure work well with Hero's Journey
        if genre in ["action", "fantasy", "sci_fi"] and any(theme in ["成長", "冒険", "正義"] for theme in themes):
            return StoryStructureType.HERO_JOURNEY

        # Traditional three-act for most other cases
        if genre in ["mystery", "romance", "horror", "thriller"]:
            return StoryStructureType.THREE_ACT

        # Default to Kishōtenketsu for slice-of-life and more contemplative stories
        if genre in ["slice_of_life", "drama"]:
            return StoryStructureType.KISHOOTENKETSU

        # Default fallback
        return StoryStructureType.THREE_ACT

    async def _create_act_structure(
        self,
        structure_type: StoryStructureType,
        estimated_pages: int,
        genre: str
    ) -> List[ActStructure]:
        """Create act structure based on structure type."""

        template = self.structure_templates.get(structure_type)
        if not template:
            # Fallback to three-act
            template = self.structure_templates[StoryStructureType.THREE_ACT]

        acts = []
        current_page = 1

        for i, act_info in enumerate(template["acts"]):
            act_pages = math.ceil(estimated_pages * act_info["percentage"])
            page_range = list(range(current_page, current_page + act_pages))

            # Estimate scene range (roughly 2-4 scenes per act for most structures)
            scenes_per_act = max(1, act_pages // 3)
            scene_start = sum(max(1, math.ceil(estimated_pages * prev_act["percentage"]) // 3)
                            for prev_act in template["acts"][:i]) + 1
            scene_range = list(range(scene_start, scene_start + scenes_per_act))

            act = ActStructure(
                act_number=act_info["number"],
                title=act_info["title"],
                purpose=act_info["purpose"],
                scene_range=scene_range,
                page_range=page_range,
                duration_percentage=act_info["percentage"],
                key_events=[],  # Will be filled by plot progression
                character_arcs=[],  # Will be filled by character arc analysis
                themes_explored=[]  # Will be filled by theme development
            )

            acts.append(act)
            current_page += act_pages

        return acts

    def _explain_structure_choice(
        self,
        structure_type: StoryStructureType,
        genre: str,
        themes: List[str]
    ) -> str:
        """Explain why this structure was chosen."""

        explanations = {
            StoryStructureType.THREE_ACT: f"{genre}ジャンルの物語展開に適した古典的三幕構成を採用。明確な起承転結で読者を引き込みます。",
            StoryStructureType.KISHOOTENKETSU: f"日本的な起承転結構造を採用。{genre}の雰囲気とテーマ「{', '.join(themes[:2])}」に最適です。",
            StoryStructureType.HERO_JOURNEY: f"冒険と成長のテーマに最適なヒーローズ・ジャーニー構造。{genre}ジャンルの王道パターンです。"
        }

        return explanations.get(structure_type, "選択された構造は物語の性質に最適化されています。")

    def _generate_adaptation_notes(
        self,
        structure_type: StoryStructureType,
        genre: str
    ) -> List[str]:
        """Generate notes for structure adaptation."""

        notes = [
            f"{structure_type.value}構造を{genre}ジャンルに適用",
            "マンガの視覚的表現を考慮したペーシング調整",
            "読者の感情的な流れを重視した構成"
        ]

        if structure_type == StoryStructureType.KISHOOTENKETSU:
            notes.append("「転」の部分での視覚的インパクトを重視")
        elif structure_type == StoryStructureType.HERO_JOURNEY:
            notes.append("キャラクターの変化を視覚的に表現")

        return notes

    async def generate_plot_progression(
        self,
        story_structure: StoryStructure,
        themes: List[str],
        characters: List[Dict[str, Any]]
    ) -> PlotProgression:
        """Generate detailed plot progression."""

        # Extract main character for protagonist-driven plot
        protagonist = self._find_protagonist(characters)

        if story_structure.type == StoryStructureType.THREE_ACT:
            return self._generate_three_act_progression(themes, protagonist)
        elif story_structure.type == StoryStructureType.KISHOOTENKETSU:
            return self._generate_kishootenketsu_progression(themes, protagonist)
        else:
            return self._generate_hero_journey_progression(themes, protagonist)

    def _find_protagonist(self, characters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find the protagonist character."""
        for char in characters:
            if char.get("archetype") == "protagonist":
                return char
        # Fallback to first character
        return characters[0] if characters else {"name": "主人公"}

    def _generate_three_act_progression(
        self,
        themes: List[str],
        protagonist: Dict[str, Any]
    ) -> PlotProgression:
        """Generate three-act plot progression."""

        protagonist_name = protagonist.get("name", "主人公")

        return PlotProgression(
            opening=f"{protagonist_name}の日常から物語が始まる",
            inciting_incident=f"{protagonist_name}に変化をもたらす出来事が発生",
            rising_action=[
                f"{protagonist_name}が問題に直面し行動を開始",
                "障害や対立が次々と現れる",
                "状況がより複雑になっていく"
            ],
            climax=f"{protagonist_name}が最大の困難に立ち向かう決定的瞬間",
            falling_action=[
                "クライマックスの結果が明らかになる",
                "残された問題が解決されていく"
            ],
            resolution=f"{protagonist_name}とその世界に新たな安定が訪れる",
            progression_notes=[
                "三幕構成による明確な物語の流れ",
                f"テーマ「{', '.join(themes[:2])}」を各幕で発展",
                "視覚的なクライマックスを重視"
            ]
        )

    def _generate_kishootenketsu_progression(
        self,
        themes: List[str],
        protagonist: Dict[str, Any]
    ) -> PlotProgression:
        """Generate Kishōtenketsu plot progression."""

        protagonist_name = protagonist.get("name", "主人公")

        return PlotProgression(
            opening=f"{protagonist_name}と世界の紹介",
            inciting_incident="物語世界の発展と深化",
            rising_action=[
                "状況や関係性が自然に展開",
                "新しい要素や視点が加わる"
            ],
            climax="予想外の展開や新たな発見",
            falling_action=[
                "転の結果を受けて物語が収束"
            ],
            resolution="新たな理解と調和の到達",
            progression_notes=[
                "起承転結による自然な流れ",
                "対立よりも発見を重視",
                f"テーマ「{', '.join(themes[:2])}」の深化"
            ]
        )

    def _generate_hero_journey_progression(
        self,
        themes: List[str],
        protagonist: Dict[str, Any]
    ) -> PlotProgression:
        """Generate Hero's Journey plot progression."""

        protagonist_name = protagonist.get("name", "主人公")

        return PlotProgression(
            opening=f"{protagonist_name}の平凡な世界",
            inciting_incident=f"{protagonist_name}への冒険の呼び声",
            rising_action=[
                "旅立ちと試練の開始",
                "仲間との出会いと成長",
                "より大きな困難への直面"
            ],
            climax=f"{protagonist_name}の最大の試練と変容",
            falling_action=[
                "報酬の獲得と帰還の準備",
                "元の世界への復帰"
            ],
            resolution=f"{protagonist_name}が新たな知恵を持って世界を変える",
            progression_notes=[
                "英雄の旅路による成長物語",
                f"テーマ「{', '.join(themes[:2])}」を成長と結びつけ",
                "変容の過程を視覚化"
            ]
        )

    async def create_scene_breakdown(
        self,
        story_structure: StoryStructure,
        plot_progression: PlotProgression,
        estimated_pages: int,
        genre: str
    ) -> List[SceneDetails]:
        """Create detailed scene breakdown."""

        # Calculate scene count based on page estimate
        scene_count = self._calculate_scene_count(estimated_pages, genre)

        scenes = []
        current_page = 1
        pages_per_scene = estimated_pages / scene_count

        pacing_distribution = self.genre_pacing.get(genre, {"medium": 0.5, "fast": 0.3, "slow": 0.2})

        for scene_num in range(1, scene_count + 1):
            scene_pages = math.ceil(pages_per_scene) if scene_num == scene_count else math.floor(pages_per_scene)
            scene_end_page = min(current_page + scene_pages - 1, estimated_pages)

            scene = SceneDetails(
                scene_number=scene_num,
                pages=list(range(current_page, scene_end_page + 1)),
                page_count=scene_end_page - current_page + 1,
                title=f"シーン{scene_num}",
                purpose=self._determine_scene_purpose(scene_num, scene_count, story_structure),
                pacing=self._determine_scene_pacing(scene_num, scene_count, pacing_distribution),
                emotional_beat=self._determine_emotional_beat(scene_num, scene_count, genre),
                visual_style=self._determine_visual_style(scene_num, genre),
                transition_type=self._determine_transition_type(scene_num, scene_count),
                key_story_function=self._determine_story_function(scene_num, scene_count, story_structure),
                characters_present=[],  # Will be filled by character analysis
                mood="neutral",
                location=f"場所{scene_num}",
                time_of_day="不定"
            )

            scenes.append(scene)
            current_page = scene_end_page + 1

        return scenes

    def _calculate_scene_count(self, estimated_pages: int, genre: str) -> int:
        """Calculate appropriate number of scenes."""

        # Base scenes on genre and page count
        if genre in ["action", "adventure"]:
            # More dynamic scenes for action
            return max(3, min(20, estimated_pages // 2))
        elif genre in ["romance", "slice_of_life"]:
            # Fewer, longer scenes for character development
            return max(3, min(15, estimated_pages // 3))
        else:
            # Standard pacing
            return max(3, min(18, math.ceil(estimated_pages / 2.5)))

    def _determine_scene_purpose(
        self,
        scene_num: int,
        total_scenes: int,
        story_structure: StoryStructure
    ) -> ScenePurposeType:
        """Determine scene purpose based on position."""

        position_ratio = scene_num / total_scenes

        if position_ratio <= 0.1:
            return ScenePurposeType.EXPOSITION
        elif position_ratio <= 0.25:
            if scene_num == 2:
                return ScenePurposeType.INCITING_INCIDENT
            return ScenePurposeType.CHARACTER_DEVELOPMENT
        elif position_ratio <= 0.75:
            if 0.4 <= position_ratio <= 0.6:
                return ScenePurposeType.CLIMAX
            return ScenePurposeType.RISING_ACTION
        elif position_ratio <= 0.9:
            return ScenePurposeType.FALLING_ACTION
        else:
            return ScenePurposeType.RESOLUTION

    def _determine_scene_pacing(
        self,
        scene_num: int,
        total_scenes: int,
        pacing_distribution: Dict[str, float]
    ) -> PacingType:
        """Determine scene pacing based on position and genre."""

        position_ratio = scene_num / total_scenes

        # Climax scenes tend to be faster
        if 0.4 <= position_ratio <= 0.6:
            return PacingType.FAST

        # Opening and ending tend to be slower
        if position_ratio <= 0.2 or position_ratio >= 0.8:
            return PacingType.SLOW

        # Default to genre distribution
        import random
        weighted_choices = []
        for pacing, weight in pacing_distribution.items():
            weighted_choices.extend([pacing] * int(weight * 100))

        selected = random.choice(weighted_choices) if weighted_choices else "medium"
        return PacingType(selected)

    def _determine_emotional_beat(
        self,
        scene_num: int,
        total_scenes: int,
        genre: str
    ) -> EmotionalBeatType:
        """Determine emotional beat for scene."""

        emotional_pattern = self.emotional_patterns.get(genre, [
            EmotionalBeatType.PEACE, EmotionalBeatType.TENSION,
            EmotionalBeatType.EXCITEMENT, EmotionalBeatType.RELIEF
        ])

        # Map scene position to emotional pattern
        pattern_index = min(len(emotional_pattern) - 1,
                          int((scene_num - 1) / total_scenes * len(emotional_pattern)))

        return emotional_pattern[pattern_index]

    def _determine_visual_style(self, scene_num: int, genre: str) -> VisualStyleType:
        """Determine visual style for scene."""

        # Genre-based visual style mapping
        if genre in ["action", "adventure"]:
            return VisualStyleType.ACTION
        elif genre in ["romance", "slice_of_life"]:
            return VisualStyleType.INTIMATE if scene_num % 3 == 0 else VisualStyleType.DIALOGUE
        elif genre in ["mystery", "horror"]:
            return VisualStyleType.ATMOSPHERIC
        else:
            # Vary between styles
            styles = [VisualStyleType.DIALOGUE, VisualStyleType.ACTION, VisualStyleType.ATMOSPHERIC]
            return styles[(scene_num - 1) % len(styles)]

    def _determine_transition_type(
        self,
        scene_num: int,
        total_scenes: int
    ) -> TransitionType:
        """Determine transition type to next scene."""

        if scene_num == total_scenes:
            return TransitionType.FADE  # Final scene

        position_ratio = scene_num / total_scenes

        # Dramatic transitions for key moments
        if 0.4 <= position_ratio <= 0.6:
            return TransitionType.MATCH_CUT

        # Time jumps for progression
        if position_ratio <= 0.3 or position_ratio >= 0.7:
            return TransitionType.TIME_JUMP

        # Default smooth transitions
        return TransitionType.CUT

    def _determine_story_function(
        self,
        scene_num: int,
        total_scenes: int,
        story_structure: StoryStructure
    ) -> StoryFunctionType:
        """Determine key story function."""

        position_ratio = scene_num / total_scenes

        if position_ratio <= 0.15:
            return StoryFunctionType.SETUP
        elif position_ratio <= 0.25:
            return StoryFunctionType.CATALYST
        elif 0.45 <= position_ratio <= 0.55:
            return StoryFunctionType.MIDPOINT
        elif 0.7 <= position_ratio <= 0.8:
            return StoryFunctionType.ALL_IS_LOST
        elif position_ratio >= 0.85:
            return StoryFunctionType.FINALE
        else:
            return StoryFunctionType.FUN_AND_GAMES

    async def analyze_character_arcs(
        self,
        characters: List[Dict[str, Any]],
        scenes: List[SceneDetails],
        themes: List[str]
    ) -> List[CharacterArc]:
        """Analyze character arcs through the story."""

        character_arcs = []

        for char in characters:
            arc_type = self._determine_arc_type(char, themes)
            starting_state = self._determine_starting_state(char)
            ending_state = self._determine_ending_state(char, arc_type)

            # Determine scene involvement based on character importance
            involvement = self._calculate_scene_involvement(char, len(scenes))

            arc = CharacterArc(
                character_name=char.get("name", "無名"),
                arc_type=arc_type,
                starting_state=starting_state,
                key_turning_points=self._generate_turning_points(char, arc_type),
                ending_state=ending_state,
                growth_trajectory=f"{starting_state}から{ending_state}への{arc_type}",
                scene_involvement=involvement
            )

            character_arcs.append(arc)

        return character_arcs

    def _determine_arc_type(self, character: Dict[str, Any], themes: List[str]) -> str:
        """Determine character arc type."""

        archetype = character.get("archetype", "supporting")

        if archetype == "protagonist":
            if "成長" in themes:
                return "成長アーク"
            elif "復讐" in themes:
                return "復讐アーク"
            else:
                return "変化アーク"
        elif archetype == "antagonist":
            return "対立アーク"
        else:
            return "サポートアーク"

    def _determine_starting_state(self, character: Dict[str, Any]) -> str:
        """Determine character's starting emotional state."""

        personality = character.get("personality", {})
        main_traits = personality.get("main_traits", [])

        if main_traits and isinstance(main_traits[0], dict):
            primary_trait = main_traits[0].get("trait", "普通")
            return f"{primary_trait}な状態"

        return "平凡な状態"

    def _determine_ending_state(self, character: Dict[str, Any], arc_type: str) -> str:
        """Determine character's ending state based on arc type."""

        if "成長" in arc_type:
            return "成長した状態"
        elif "対立" in arc_type:
            return "敗北または改心した状態"
        elif "復讐" in arc_type:
            return "目的を達成または諦めた状態"
        else:
            return "物語に貢献した状態"

    def _generate_turning_points(self, character: Dict[str, Any], arc_type: str) -> List[str]:
        """Generate key turning points for character."""

        name = character.get("name", "キャラクター")

        if "成長" in arc_type:
            return [
                f"{name}が現実と向き合う",
                f"{name}が重要な決断を下す",
                f"{name}が新たな力を発見する"
            ]
        elif "対立" in arc_type:
            return [
                f"{name}が敵意を明確にする",
                f"{name}が最大の攻撃を仕掛ける",
                f"{name}が最終的に対峙する"
            ]
        else:
            return [f"{name}が物語に重要な貢献をする"]

    def _calculate_scene_involvement(self, character: Dict[str, Any], total_scenes: int) -> List[int]:
        """Calculate which scenes character appears in."""

        importance = character.get("role_importance", 0.5)

        if importance >= 0.8:  # Main characters
            # Appear in most scenes
            return list(range(1, total_scenes + 1))
        elif importance >= 0.5:  # Supporting characters
            # Appear in about half the scenes
            step = max(1, total_scenes // (total_scenes // 2))
            return list(range(1, total_scenes + 1, step))
        else:  # Minor characters
            # Appear in key scenes only
            key_scenes = max(1, total_scenes // 4)
            return [1, total_scenes // 2, total_scenes][:key_scenes]

    async def generate_tension_curve(self, scenes: List[SceneDetails]) -> TensionCurve:
        """Generate tension curve for the story."""

        tension_points = []

        for scene in scenes:
            tension_level = self._calculate_scene_tension(scene, len(scenes))

            point = TensionPoint(
                scene_number=scene.scene_number,
                tension_level=tension_level,
                tension_type=self._determine_tension_type(scene),
                description=f"シーン{scene.scene_number}: {scene.purpose.value}による緊張"
            )
            tension_points.append(point)

        # Find peak and lowest tension
        peak_scene = max(tension_points, key=lambda p: p.tension_level).scene_number
        lowest_scene = min(tension_points, key=lambda p: p.tension_level).scene_number

        return TensionCurve(
            points=tension_points,
            peak_tension_scene=peak_scene,
            lowest_tension_scene=lowest_scene,
            overall_pattern="物語の進行に伴う自然な緊張の起伏",
            pacing_recommendations=[
                "クライマックスに向けて段階的に緊張を高める",
                "適度な緩急をつけて読者を飽きさせない",
                "感情的な解放のタイミングを重視"
            ]
        )

    def _calculate_scene_tension(self, scene: SceneDetails, total_scenes: int) -> float:
        """Calculate tension level for a scene."""

        position_ratio = scene.scene_number / total_scenes

        # Base tension on scene purpose
        purpose_tension = {
            ScenePurposeType.EXPOSITION: 0.2,
            ScenePurposeType.INCITING_INCIDENT: 0.6,
            ScenePurposeType.RISING_ACTION: 0.7,
            ScenePurposeType.CLIMAX: 1.0,
            ScenePurposeType.FALLING_ACTION: 0.4,
            ScenePurposeType.RESOLUTION: 0.1
        }

        base_tension = purpose_tension.get(scene.purpose, 0.5)

        # Adjust based on emotional beat
        emotional_tension = {
            EmotionalBeatType.FEAR: 0.9,
            EmotionalBeatType.TENSION: 0.8,
            EmotionalBeatType.ANGER: 0.7,
            EmotionalBeatType.EXCITEMENT: 0.6,
            EmotionalBeatType.SURPRISE: 0.6,
            EmotionalBeatType.JOY: 0.3,
            EmotionalBeatType.PEACE: 0.1,
            EmotionalBeatType.SADNESS: 0.4
        }

        emotional_modifier = emotional_tension.get(scene.emotional_beat, 0.5)

        # Combine and normalize
        final_tension = min(1.0, (base_tension + emotional_modifier) / 2)
        return round(final_tension, 2)

    def _determine_tension_type(self, scene: SceneDetails) -> str:
        """Determine type of tension in scene."""

        if scene.purpose in [ScenePurposeType.CLIMAX, ScenePurposeType.CONFLICT_ESCALATION]:
            return "アクション緊張"
        elif scene.emotional_beat in [EmotionalBeatType.FEAR, EmotionalBeatType.MYSTERY]:
            return "サスペンス緊張"
        elif scene.emotional_beat in [EmotionalBeatType.SADNESS, EmotionalBeatType.ANGER]:
            return "感情的緊張"
        else:
            return "状況的緊張"
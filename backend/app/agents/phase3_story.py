"""Phase 3: Plot and Story Structure Agent."""

from typing import Dict, Any, Optional, List
from uuid import UUID
import asyncio
import json
import math

from app.agents.base_agent import BaseAgent
from app.core.config import settings


class Phase3StoryAgent(BaseAgent):
    """Agent for creating plot structure and story progression."""
    
    def __init__(self):
        super().__init__(
            phase_number=3,
            phase_name="プロット・ストーリー構成",
            timeout_seconds=settings.phase_timeouts[3]
        )
        
        self.story_structures = {
            "three_act": {
                "act1_percentage": 0.25,
                "act2_percentage": 0.50,
                "act3_percentage": 0.25,
                "key_points": ["setup", "inciting_incident", "plot_point_1", "midpoint", "plot_point_2", "climax", "resolution"]
            },
            "hero_journey": {
                "stages": ["ordinary_world", "call_to_adventure", "refusal", "meeting_mentor", 
                          "crossing_threshold", "tests", "ordeal", "reward", "road_back", "resurrection", "return"]
            },
            "kishōtenketsu": {
                "ki": 0.25,    # Introduction
                "shō": 0.25,   # Development  
                "ten": 0.25,   # Twist
                "ketsu": 0.25  # Conclusion
            }
        }
        
        self.genre_pacing = {
            "action": {"fast_scenes": 0.6, "medium_scenes": 0.3, "slow_scenes": 0.1},
            "romance": {"fast_scenes": 0.2, "medium_scenes": 0.5, "slow_scenes": 0.3},
            "mystery": {"fast_scenes": 0.3, "medium_scenes": 0.4, "slow_scenes": 0.3},
            "slice_of_life": {"fast_scenes": 0.1, "medium_scenes": 0.4, "slow_scenes": 0.5},
            "fantasy": {"fast_scenes": 0.4, "medium_scenes": 0.4, "slow_scenes": 0.2}
        }
    
    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: UUID,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Generate story structure and plot progression."""
        
        if not previous_results or 1 not in previous_results:
            raise ValueError("Phase 1 results required for story structure")
        
        phase1_result = previous_results[1]
        phase2_result = previous_results.get(2, {}) if previous_results else {}
        
        # Extract story requirements
        genre = phase1_result.get("genre", "general")
        themes = phase1_result.get("themes", [])
        estimated_pages = phase1_result.get("estimated_pages", 8)
        characters = phase2_result.get("characters", [])
        
        # Determine story structure
        story_structure = await self._determine_story_structure(genre, estimated_pages)
        
        # Generate plot progression
        plot_progression = await self._generate_plot_progression(
            story_structure, themes, characters, estimated_pages
        )
        
        # Create scene breakdown
        scene_breakdown = await self._create_scene_breakdown(
            plot_progression, estimated_pages, genre
        )
        
        # Generate pacing analysis
        pacing_analysis = await self._analyze_pacing(scene_breakdown, genre)
        
        # Create narrative flow
        narrative_flow = await self._create_narrative_flow(
            scene_breakdown, characters, themes
        )
        
        result = {
            "story_structure": story_structure,
            "plot_progression": plot_progression,
            "scene_breakdown": scene_breakdown,
            "narrative_flow": narrative_flow,
            "pacing_analysis": pacing_analysis,
            "total_scenes": len(scene_breakdown),
            "story_complexity_score": self._calculate_story_complexity(plot_progression, characters),
            "theme_integration": self._analyze_theme_integration(themes, plot_progression),
            "conflict_structure": self._analyze_conflict_structure(characters, plot_progression)
        }
        
        return result
    
    async def generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate Gemini Pro prompt for story structure creation."""
        
        phase1_result = previous_results[1] if previous_results else {}
        phase2_result = previous_results.get(2, {}) if previous_results else {}
        
        genre = phase1_result.get("genre", "general")
        themes = phase1_result.get("themes", [])
        estimated_pages = phase1_result.get("estimated_pages", 8)
        characters = phase2_result.get("characters", [])
        
        character_summary = ""
        if characters:
            character_summary = "\n".join([
                f"- {char.get('name', '不明')}: {char.get('role', '不明')}（{char.get('goals', '目標不明')}）"
                for char in characters[:3]
            ])
        
        prompt = f"""あなたは漫画制作における脚本・構成の専門家です。
以下の設定に基づいて、{estimated_pages}ページの漫画のストーリー構成を作成してください。

【基本設定】
ジャンル: {genre}
テーマ: {', '.join(themes)}
推定ページ数: {estimated_pages}

【キャラクター】
{character_summary or "キャラクター情報なし"}

【構成要件】
1. 起承転結またはthree-act構造での構成
2. 各シーンの目的と機能を明確化
3. キャラクターの成長弧を組み込み
4. テーマの効果的な表現
5. 適切なクライマックスとしめくくり

【出力形式】JSON
{{
    "story_structure": {{
        "type": "three_act/kishōtenketsu",
        "acts": [
            {{
                "act_name": "導入/起",
                "pages": [1,3],
                "purpose": "世界観とキャラクター紹介",
                "key_events": ["event1", "event2"]
            }}
        ]
    }},
    "scene_breakdown": [
        {{
            "scene_number": 1,
            "pages": [1,2],
            "title": "シーン名",
            "purpose": "シーンの目的",
            "characters": ["character1"],
            "location": "場所",
            "mood": "雰囲気",
            "key_dialogue": "重要なセリフ",
            "visual_focus": "視覚的注目点",
            "pacing": "fast/medium/slow"
        }}
    ],
    "plot_points": [
        {{
            "name": "inciting_incident",
            "scene": 2,
            "description": "物語の転換点"
        }}
    ]
}}"""
        
        return prompt
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate Phase 3 output."""
        
        required_keys = [
            "story_structure", "plot_progression", "scene_breakdown",
            "narrative_flow", "total_scenes"
        ]
        
        for key in required_keys:
            if key not in output_data:
                self.log_warning(f"Missing required key: {key}")
                return False
        
        scene_breakdown = output_data.get("scene_breakdown", [])
        
        # Must have at least 3 scenes
        if len(scene_breakdown) < 3:
            self.log_warning("Too few scenes in breakdown")
            return False
        
        # Check scene completeness
        for scene in scene_breakdown:
            required_scene_fields = ["scene_number", "title", "purpose", "pacing"]
            if not all(field in scene for field in required_scene_fields):
                self.log_warning(f"Incomplete scene data: {scene.get('scene_number', 'unknown')}")
                return False
        
        # Check story structure
        story_structure = output_data.get("story_structure", {})
        if not story_structure.get("type") or not story_structure.get("acts"):
            self.log_warning("Invalid story structure")
            return False
        
        return True
    
    async def _determine_story_structure(self, genre: str, estimated_pages: int) -> Dict[str, Any]:
        """Determine optimal story structure based on genre and length."""
        
        # Short stories (< 10 pages) work better with kishōtenketsu
        # Longer stories benefit from three-act structure
        if estimated_pages <= 10:
            structure_type = "kishōtenketsu"
            structure = self.story_structures["kishōtenketsu"].copy()
        else:
            structure_type = "three_act"
            structure = self.story_structures["three_act"].copy()
        
        structure["type"] = structure_type
        structure["total_pages"] = estimated_pages
        
        return structure
    
    async def _generate_plot_progression(
        self,
        story_structure: Dict[str, Any],
        themes: List[str],
        characters: List[Dict[str, Any]],
        estimated_pages: int
    ) -> Dict[str, Any]:
        """Generate detailed plot progression."""
        
        protagonist = next((c for c in characters if c.get("role") == "protagonist"), None)
        antagonist = next((c for c in characters if c.get("role") == "antagonist"), None)
        
        structure_type = story_structure.get("type", "three_act")
        
        if structure_type == "three_act":
            return await self._generate_three_act_progression(
                themes, protagonist, antagonist, estimated_pages
            )
        else:
            return await self._generate_kishōtenketsu_progression(
                themes, protagonist, antagonist, estimated_pages
            )
    
    async def _generate_three_act_progression(
        self,
        themes: List[str],
        protagonist: Optional[Dict[str, Any]],
        antagonist: Optional[Dict[str, Any]],
        estimated_pages: int
    ) -> Dict[str, Any]:
        """Generate three-act story progression."""
        
        act1_pages = math.ceil(estimated_pages * 0.25)
        act2_pages = math.ceil(estimated_pages * 0.50)
        act3_pages = estimated_pages - act1_pages - act2_pages
        
        progression = {
            "act_1": {
                "pages": list(range(1, act1_pages + 1)),
                "purpose": "世界観・キャラクター紹介、事件の発生",
                "key_events": [
                    "opening_scene",
                    "character_introduction",
                    "inciting_incident"
                ],
                "character_state": self._get_character_state("beginning", protagonist),
                "theme_introduction": themes[0] if themes else "基本テーマ導入"
            },
            "act_2": {
                "pages": list(range(act1_pages + 1, act1_pages + act2_pages + 1)),
                "purpose": "対立の発展、困難への挑戦",
                "key_events": [
                    "rising_action",
                    "midpoint_twist",
                    "obstacles_escalation"
                ],
                "character_state": self._get_character_state("middle", protagonist),
                "conflict_escalation": self._generate_conflict_escalation(protagonist, antagonist)
            },
            "act_3": {
                "pages": list(range(act1_pages + act2_pages + 1, estimated_pages + 1)),
                "purpose": "クライマックス、解決、結末",
                "key_events": [
                    "climax",
                    "falling_action",
                    "resolution"
                ],
                "character_state": self._get_character_state("end", protagonist),
                "theme_resolution": self._generate_theme_resolution(themes)
            }
        }
        
        return progression
    
    async def _generate_kishōtenketsu_progression(
        self,
        themes: List[str],
        protagonist: Optional[Dict[str, Any]],
        antagonist: Optional[Dict[str, Any]],
        estimated_pages: int
    ) -> Dict[str, Any]:
        """Generate kishōtenketsu (four-act) story progression."""
        
        pages_per_act = estimated_pages // 4
        remaining_pages = estimated_pages % 4
        
        progression = {
            "ki": {
                "pages": list(range(1, pages_per_act + 1)),
                "purpose": "導入・背景設定",
                "description": "登場人物と状況の紹介"
            },
            "shō": {
                "pages": list(range(pages_per_act + 1, pages_per_act * 2 + 1)),
                "purpose": "発展・展開",
                "description": "物語の基本的な流れを確立"
            },
            "ten": {
                "pages": list(range(pages_per_act * 2 + 1, pages_per_act * 3 + 1 + remaining_pages)),
                "purpose": "転・変化",
                "description": "予想外の展開や視点の転換"
            },
            "ketsu": {
                "pages": list(range(pages_per_act * 3 + 1 + remaining_pages, estimated_pages + 1)),
                "purpose": "結・まとめ",
                "description": "物語の結論と余韻"
            }
        }
        
        return progression
    
    async def _create_scene_breakdown(
        self,
        plot_progression: Dict[str, Any],
        estimated_pages: int,
        genre: str
    ) -> List[Dict[str, Any]]:
        """Create detailed scene breakdown."""
        
        # Estimate scenes based on page count (roughly 1-3 pages per scene)
        scene_count = max(3, min(estimated_pages, estimated_pages // 2))
        pages_per_scene = estimated_pages / scene_count
        
        scenes = []
        current_page = 1
        
        pacing_distribution = self.genre_pacing.get(genre, {"fast": 0.3, "medium": 0.4, "slow": 0.3})
        
        for scene_num in range(1, scene_count + 1):
            scene_pages = math.ceil(pages_per_scene) if scene_num == scene_count else math.floor(pages_per_scene)
            scene_end_page = min(current_page + scene_pages - 1, estimated_pages)
            
            # Determine scene pacing based on position and genre
            pacing = self._determine_scene_pacing(scene_num, scene_count, pacing_distribution)
            
            # Determine scene purpose based on position in story
            purpose = self._determine_scene_purpose(scene_num, scene_count, plot_progression)
            
            scene = {
                "scene_number": scene_num,
                "pages": list(range(current_page, scene_end_page + 1)),
                "page_count": scene_end_page - current_page + 1,
                "title": f"シーン{scene_num}",
                "purpose": purpose,
                "pacing": pacing,
                "emotional_beat": self._determine_emotional_beat(scene_num, scene_count),
                "visual_style": self._determine_visual_style(pacing, purpose),
                "transition_type": self._determine_transition_type(scene_num, scene_count),
                "key_story_function": self._determine_story_function(scene_num, scene_count)
            }
            
            scenes.append(scene)
            current_page = scene_end_page + 1
        
        return scenes
    
    def _determine_scene_pacing(
        self, scene_num: int, total_scenes: int, pacing_dist: Dict[str, float]
    ) -> str:
        """Determine pacing for a scene based on position."""
        
        scene_position = scene_num / total_scenes
        
        # Beginning: usually slow to medium
        if scene_position <= 0.3:
            return "medium" if scene_num == 1 else "slow"
        # Middle: varies based on genre
        elif scene_position <= 0.7:
            # Midpoint often has faster pacing
            if 0.4 <= scene_position <= 0.6:
                return "fast"
            return "medium"
        # End: usually fast for climax, then slow for resolution
        else:
            if scene_position <= 0.8:
                return "fast"  # Climax
            return "medium"  # Resolution
    
    def _determine_scene_purpose(
        self, scene_num: int, total_scenes: int, plot_progression: Dict[str, Any]
    ) -> str:
        """Determine the narrative purpose of a scene."""
        
        scene_position = scene_num / total_scenes
        
        if scene_position <= 0.25:
            return "introduction_and_setup"
        elif scene_position <= 0.5:
            return "development_and_conflict"
        elif scene_position <= 0.75:
            return "complications_and_crisis"
        else:
            return "climax_and_resolution"
    
    def _determine_emotional_beat(self, scene_num: int, total_scenes: int) -> str:
        """Determine emotional beat for the scene."""
        
        scene_position = scene_num / total_scenes
        
        emotional_progression = [
            "curiosity", "engagement", "concern", "tension", 
            "anxiety", "climax", "relief", "satisfaction"
        ]
        
        beat_index = min(len(emotional_progression) - 1, int(scene_position * len(emotional_progression)))
        return emotional_progression[beat_index]
    
    def _determine_visual_style(self, pacing: str, purpose: str) -> str:
        """Determine visual style based on pacing and purpose."""
        
        if pacing == "fast":
            return "dynamic_angles_close_ups"
        elif pacing == "slow":
            return "wide_shots_detailed_backgrounds"
        else:
            return "balanced_composition"
    
    def _determine_transition_type(self, scene_num: int, total_scenes: int) -> str:
        """Determine transition type between scenes."""
        
        if scene_num == 1:
            return "opening"
        elif scene_num == total_scenes:
            return "ending"
        else:
            return "standard_transition"
    
    def _determine_story_function(self, scene_num: int, total_scenes: int) -> str:
        """Determine the story function of the scene."""
        
        scene_position = scene_num / total_scenes
        
        if scene_position <= 0.2:
            return "exposition"
        elif scene_position <= 0.4:
            return "plot_advancement"
        elif scene_position <= 0.6:
            return "character_development"
        elif scene_position <= 0.8:
            return "conflict_escalation"
        else:
            return "resolution"
    
    async def _analyze_pacing(
        self, scene_breakdown: List[Dict[str, Any]], genre: str
    ) -> Dict[str, Any]:
        """Analyze story pacing."""
        
        pacing_count = {"fast": 0, "medium": 0, "slow": 0}
        for scene in scene_breakdown:
            pacing = scene.get("pacing", "medium")
            pacing_count[pacing] += 1
        
        total_scenes = len(scene_breakdown)
        pacing_ratios = {k: v / total_scenes for k, v in pacing_count.items()}
        
        # Compare with genre expectations
        expected_pacing = self.genre_pacing.get(genre, {"fast": 0.3, "medium": 0.4, "slow": 0.3})
        
        pacing_analysis = {
            "actual_pacing_distribution": pacing_ratios,
            "expected_pacing_distribution": expected_pacing,
            "pacing_match_score": self._calculate_pacing_match_score(pacing_ratios, expected_pacing),
            "pacing_flow_analysis": self._analyze_pacing_flow(scene_breakdown),
            "recommendations": self._generate_pacing_recommendations(pacing_ratios, expected_pacing)
        }
        
        return pacing_analysis
    
    def _calculate_pacing_match_score(
        self, actual: Dict[str, float], expected: Dict[str, float]
    ) -> float:
        """Calculate how well actual pacing matches expected pacing."""
        
        total_difference = sum(abs(actual.get(k, 0) - v) for k, v in expected.items())
        match_score = max(0, 1 - total_difference / 2)  # Normalize to 0-1
        
        return round(match_score, 2)
    
    def _analyze_pacing_flow(self, scene_breakdown: List[Dict[str, Any]]) -> List[str]:
        """Analyze the flow of pacing throughout the story."""
        
        pacing_sequence = [scene.get("pacing", "medium") for scene in scene_breakdown]
        flow_analysis = []
        
        for i in range(len(pacing_sequence) - 1):
            current = pacing_sequence[i]
            next_pacing = pacing_sequence[i + 1]
            
            if current == "slow" and next_pacing == "fast":
                flow_analysis.append(f"Scene {i + 1} → {i + 2}: 急展開")
            elif current == "fast" and next_pacing == "slow":
                flow_analysis.append(f"Scene {i + 1} → {i + 2}: 緊張緩和")
            elif current == next_pacing == "fast":
                flow_analysis.append(f"Scene {i + 1} → {i + 2}: 高張度維持")
        
        return flow_analysis
    
    def _generate_pacing_recommendations(
        self, actual: Dict[str, float], expected: Dict[str, float]
    ) -> List[str]:
        """Generate pacing recommendations."""
        
        recommendations = []
        
        for pace_type, expected_ratio in expected.items():
            actual_ratio = actual.get(pace_type, 0)
            difference = expected_ratio - actual_ratio
            
            if abs(difference) > 0.1:  # Significant difference
                if difference > 0:
                    recommendations.append(f"{pace_type}ペースのシーンを増やすことを推奨")
                else:
                    recommendations.append(f"{pace_type}ペースのシーンを減らすことを推奨")
        
        return recommendations
    
    async def _create_narrative_flow(
        self,
        scene_breakdown: List[Dict[str, Any]],
        characters: List[Dict[str, Any]],
        themes: List[str]
    ) -> Dict[str, Any]:
        """Create narrative flow structure."""
        
        narrative_flow = {
            "character_arcs": self._map_character_arcs(scene_breakdown, characters),
            "theme_development": self._map_theme_development(scene_breakdown, themes),
            "tension_curve": self._generate_tension_curve(scene_breakdown),
            "emotional_journey": self._map_emotional_journey(scene_breakdown),
            "story_beats": self._identify_story_beats(scene_breakdown)
        }
        
        return narrative_flow
    
    def _map_character_arcs(
        self, scene_breakdown: List[Dict[str, Any]], characters: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Map character development through scenes."""
        
        character_arcs = {}
        
        for char in characters:
            char_name = char.get("name", "unknown")
            arc_stages = []
            
            for scene in scene_breakdown:
                scene_num = scene.get("scene_number", 0)
                scene_purpose = scene.get("purpose", "")
                
                if scene_num <= 2:
                    arc_stages.append("character_introduction")
                elif "development" in scene_purpose:
                    arc_stages.append("character_growth")
                elif "conflict" in scene_purpose:
                    arc_stages.append("character_challenge")
                elif "climax" in scene_purpose:
                    arc_stages.append("character_transformation")
                else:
                    arc_stages.append("character_resolution")
            
            character_arcs[char_name] = arc_stages
        
        return character_arcs
    
    def _map_theme_development(
        self, scene_breakdown: List[Dict[str, Any]], themes: List[str]
    ) -> Dict[str, List[str]]:
        """Map theme development through scenes."""
        
        theme_development = {}
        
        for theme in themes:
            development_stages = []
            
            for scene in scene_breakdown:
                scene_num = scene.get("scene_number", 0)
                total_scenes = len(scene_breakdown)
                scene_position = scene_num / total_scenes
                
                if scene_position <= 0.25:
                    development_stages.append(f"{theme}_introduction")
                elif scene_position <= 0.5:
                    development_stages.append(f"{theme}_exploration")
                elif scene_position <= 0.75:
                    development_stages.append(f"{theme}_challenge")
                else:
                    development_stages.append(f"{theme}_resolution")
            
            theme_development[theme] = development_stages
        
        return theme_development
    
    def _generate_tension_curve(self, scene_breakdown: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate tension/intensity curve for the story."""
        
        tension_curve = []
        
        for scene in scene_breakdown:
            scene_num = scene.get("scene_number", 0)
            total_scenes = len(scene_breakdown)
            scene_position = scene_num / total_scenes
            
            # Calculate tension level based on position and pacing
            if scene_position <= 0.2:
                tension_level = 2  # Low, setup
            elif scene_position <= 0.4:
                tension_level = 4  # Medium, building
            elif scene_position <= 0.6:
                tension_level = 6  # Medium-high, complications
            elif scene_position <= 0.8:
                tension_level = 9  # Very high, climax
            else:
                tension_level = 3  # Low, resolution
            
            # Adjust based on pacing
            pacing = scene.get("pacing", "medium")
            if pacing == "fast":
                tension_level = min(10, tension_level + 1)
            elif pacing == "slow":
                tension_level = max(1, tension_level - 1)
            
            tension_curve.append({
                "scene_number": scene_num,
                "tension_level": tension_level,
                "description": self._describe_tension_level(tension_level)
            })
        
        return tension_curve
    
    def _describe_tension_level(self, level: int) -> str:
        """Describe tension level."""
        
        descriptions = {
            1: "非常に穏やか",
            2: "落ち着いている",
            3: "軽い緊張",
            4: "興味深い展開",
            5: "やや緊迫",
            6: "緊張感高まる",
            7: "かなり緊迫",
            8: "非常に緊迫",
            9: "極度の緊張",
            10: "最高潮"
        }
        
        return descriptions.get(level, "普通")
    
    def _map_emotional_journey(self, scene_breakdown: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map emotional journey through the story."""
        
        emotional_journey = []
        
        for scene in scene_breakdown:
            emotional_beat = scene.get("emotional_beat", "neutral")
            scene_num = scene.get("scene_number", 0)
            
            emotional_journey.append({
                "scene_number": scene_num,
                "emotional_beat": emotional_beat,
                "reader_emotion": self._map_emotional_beat_to_reader_emotion(emotional_beat)
            })
        
        return emotional_journey
    
    def _map_emotional_beat_to_reader_emotion(self, emotional_beat: str) -> str:
        """Map story emotional beat to expected reader emotion."""
        
        emotion_mapping = {
            "curiosity": "興味",
            "engagement": "関心",
            "concern": "心配",
            "tension": "緊張",
            "anxiety": "不安",
            "climax": "興奮",
            "relief": "安堵",
            "satisfaction": "満足"
        }
        
        return emotion_mapping.get(emotional_beat, "中立")
    
    def _identify_story_beats(self, scene_breakdown: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify key story beats."""
        
        story_beats = []
        total_scenes = len(scene_breakdown)
        
        for scene in scene_breakdown:
            scene_num = scene.get("scene_number", 0)
            scene_position = scene_num / total_scenes
            
            beat_type = None
            if scene_num == 1:
                beat_type = "opening"
            elif scene_position <= 0.25:
                beat_type = "setup"
            elif scene_position <= 0.5:
                beat_type = "plot_point_1"
            elif abs(scene_position - 0.5) < 0.1:
                beat_type = "midpoint"
            elif scene_position <= 0.75:
                beat_type = "plot_point_2"
            elif scene_position > 0.8:
                if scene_num == total_scenes:
                    beat_type = "resolution"
                else:
                    beat_type = "climax"
            
            if beat_type:
                story_beats.append({
                    "scene_number": scene_num,
                    "beat_type": beat_type,
                    "description": self._describe_story_beat(beat_type)
                })
        
        return story_beats
    
    def _describe_story_beat(self, beat_type: str) -> str:
        """Describe story beat type."""
        
        descriptions = {
            "opening": "物語の導入",
            "setup": "基本設定の確立",
            "plot_point_1": "主要な転換点",
            "midpoint": "物語の中間点",
            "plot_point_2": "クライマックスへの転換",
            "climax": "物語のクライマックス",
            "resolution": "物語の解決"
        }
        
        return descriptions.get(beat_type, "ストーリービート")
    
    def _get_character_state(self, phase: str, protagonist: Optional[Dict[str, Any]]) -> str:
        """Get character state description for story phase."""
        
        if not protagonist:
            return "キャラクター情報なし"
        
        char_name = protagonist.get("name", "主人公")
        
        states = {
            "beginning": f"{char_name}は平凡な日常を送っている",
            "middle": f"{char_name}は困難に直面し、成長を始める",
            "end": f"{char_name}は試練を乗り越え、変化を遂げる"
        }
        
        return states.get(phase, "キャラクターの状態")
    
    def _generate_conflict_escalation(
        self, protagonist: Optional[Dict[str, Any]], antagonist: Optional[Dict[str, Any]]
    ) -> str:
        """Generate conflict escalation description."""
        
        if protagonist and antagonist:
            return f"{protagonist.get('name', '主人公')}と{antagonist.get('name', '敵役')}の対立が激化"
        elif protagonist:
            return f"{protagonist.get('name', '主人公')}が内面的な葛藤に直面"
        else:
            return "対立が激化する"
    
    def _generate_theme_resolution(self, themes: List[str]) -> str:
        """Generate theme resolution description."""
        
        if not themes:
            return "テーマが解決される"
        
        main_theme = themes[0]
        return f"{main_theme}というテーマが最終的に表現される"
    
    def _calculate_story_complexity(
        self, plot_progression: Dict[str, Any], characters: List[Dict[str, Any]]
    ) -> float:
        """Calculate story complexity score."""
        
        complexity_factors = []
        
        # Character count complexity
        char_complexity = min(1.0, len(characters) / 5)
        complexity_factors.append(char_complexity)
        
        # Plot structure complexity
        structure_complexity = 0.7 if len(plot_progression) >= 3 else 0.4
        complexity_factors.append(structure_complexity)
        
        # Character relationship complexity
        main_chars = [c for c in characters if c.get("importance", 0) >= 7]
        relationship_complexity = min(1.0, len(main_chars) / 3)
        complexity_factors.append(relationship_complexity)
        
        # Average complexity
        overall_complexity = sum(complexity_factors) / len(complexity_factors)
        
        return round(overall_complexity, 2)
    
    def _analyze_theme_integration(
        self, themes: List[str], plot_progression: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze how themes are integrated into the plot."""
        
        integration_analysis = {
            "themes_covered": themes,
            "integration_points": [],
            "theme_balance": "balanced" if len(themes) <= 3 else "complex",
            "primary_theme": themes[0] if themes else None
        }
        
        # Identify integration points in plot progression
        for act_name, act_data in plot_progression.items():
            if isinstance(act_data, dict) and "purpose" in act_data:
                integration_analysis["integration_points"].append({
                    "act": act_name,
                    "theme_expression": f"Act {act_name} explores theme through {act_data['purpose']}"
                })
        
        return integration_analysis
    
    def _analyze_conflict_structure(
        self, characters: List[Dict[str, Any]], plot_progression: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze conflict structure in the story."""
        
        protagonist = next((c for c in characters if c.get("role") == "protagonist"), None)
        antagonist = next((c for c in characters if c.get("role") == "antagonist"), None)
        
        conflict_analysis = {
            "primary_conflict_type": "character_vs_character" if antagonist else "character_vs_self",
            "conflict_participants": [],
            "conflict_escalation_pattern": "rising_action",
            "resolution_type": "positive"
        }
        
        if protagonist:
            conflict_analysis["conflict_participants"].append({
                "character": protagonist.get("name"),
                "role": "protagonist",
                "conflict_source": protagonist.get("goals", "unknown goals")
            })
        
        if antagonist:
            conflict_analysis["conflict_participants"].append({
                "character": antagonist.get("name"),
                "role": "antagonist",
                "conflict_source": antagonist.get("goals", "opposing goals")
            })
        
        return conflict_analysis
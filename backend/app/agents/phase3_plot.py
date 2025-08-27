"""Phase 3: Plot and Story Structure Agent."""

from typing import Dict, Any, Optional, List
from uuid import UUID
import json

from app.agents.base_agent import BaseAgent
from app.core.config import settings
from app.services.vertex_ai_service import VertexAIService


class Phase3PlotAgent(BaseAgent):
    """Agent for plot and story structure design."""
    
    def __init__(self):
        super().__init__(
            phase_number=3,
            phase_name="プロット・ストーリー構成",
            timeout_seconds=settings.phase_timeouts[3]
        )
        
        self.story_structures = {
            "three_act": {
                "act1": "設定・導入（25%）",
                "act2": "対立・展開（50%）",
                "act3": "解決・結末（25%）"
            },
            "kishōtenketsu": {
                "ki": "起：導入",
                "shō": "承：発展",
                "ten": "転：転換",
                "ketsu": "結：結末"
            },
            "hero_journey": {
                "ordinary_world": "日常世界",
                "call_to_adventure": "冒険への誘い",
                "trials": "試練",
                "revelation": "啓示",
                "return": "帰還"
            }
        }
        
        self.pacing_patterns = {
            "action": {"fast": 60, "medium": 30, "slow": 10},
            "romance": {"fast": 20, "medium": 40, "slow": 40},
            "mystery": {"fast": 30, "medium": 50, "slow": 20},
            "slice_of_life": {"fast": 10, "medium": 30, "slow": 60}
        }
        
        # Vertex AI サービス初期化
        self.vertex_ai = VertexAIService()
    
    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: UUID,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Process plot and story structure based on concept analysis.
        
        Args:
            input_data: Contains original text
            session_id: Current session ID
            previous_results: Phase 1 results (can run parallel with Phase 2)
            
        Returns:
            Story structure with plot points and pacing
        """
        
        phase1_result = previous_results.get(1, {}) if previous_results else {}
        
        # Extract from Phase 1
        text = input_data.get("text", "")
        genre = phase1_result.get("genre", "general")
        themes = phase1_result.get("themes", [])
        estimated_pages = phase1_result.get("estimated_pages", 8)
        
        # Generate AI prompt
        prompt = await self.generate_prompt(
            {
                "text": text,
                "genre": genre,
                "themes": themes,
                "pages": estimated_pages
            },
            previous_results
        )
        
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
                story_structure = ai_result if ai_result else await self._analyze_story_structure(text, genre, themes)
                
            else:
                # Fallback to rule-based analysis
                self.log_warning(f"Gemini Pro failed, using fallback: {ai_response.get('error', 'Unknown error')}")
                story_structure = await self._analyze_story_structure(text, genre, themes)
                
        except Exception as e:
            # Fallback to rule-based analysis on error
            self.log_error(f"AI analysis failed, using fallback: {str(e)}")
            story_structure = await self._analyze_story_structure(text, genre, themes)
        
        # Divide into scenes
        scenes = await self._divide_into_scenes(
            text,
            story_structure,
            estimated_pages,
            genre
        )
        
        # Analyze pacing
        pacing = self._analyze_pacing(scenes, genre)
        
        # Create plot timeline
        timeline = self._create_timeline(scenes, estimated_pages)
        
        result = {
            "structure_type": self._select_structure_type(genre),
            "story_structure": story_structure,
            "scenes": scenes,
            "total_scenes": len(scenes),
            "pacing": pacing,
            "timeline": timeline,
            "plot_points": self._extract_plot_points(story_structure),
            "conflict": self._analyze_conflict(text, themes),
            "emotional_arc": self._create_emotional_arc(scenes, genre),
            "page_allocation": self._allocate_pages(scenes, estimated_pages)
        }
        
        return result
    
    async def generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate Gemini Pro prompt for story structuring."""
        
        text = input_data.get("text", "")[:3000]
        genre = input_data.get("genre", "general")
        themes = input_data.get("themes", [])
        pages = input_data.get("pages", 8)
        
        prompt = f"""あなたは漫画のストーリー構成の専門家です。
以下のテキストを{pages}ページの漫画用に構成してください。

入力テキスト:
{text}

ジャンル: {genre}
テーマ: {', '.join(themes)}
ページ数: {pages}

以下の要素を含むストーリー構成をJSON形式で出力してください：

1. story_structure (3幕構成):
   - act1: 導入部の内容とページ配分
   - act2: 展開部の内容とページ配分
   - act3: 結末部の内容とページ配分

2. scenes (シーンリスト):
   - scene_number: シーン番号
   - description: シーンの説明
   - purpose: そのシーンの目的
   - emotion: 感情的なトーン
   - importance: 重要度（high/medium/low）
   - estimated_panels: 推定コマ数

3. plot_points (主要プロットポイント):
   - inciting_incident: きっかけとなる出来事
   - turning_point1: 第一転換点
   - midpoint: 中間点
   - turning_point2: 第二転換点
   - climax: クライマックス
   - resolution: 解決

4. pacing:
   - ペーシング分析（fast/medium/slow）の割合

JSONフォーマットで回答してください。"""
        
        return prompt
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate phase 3 output."""
        
        required_keys = ["story_structure", "scenes", "pacing", "plot_points"]
        
        for key in required_keys:
            if key not in output_data:
                self.log_warning(f"Missing required key: {key}")
                return False
        
        # Validate scenes
        if not output_data["scenes"] or len(output_data["scenes"]) < 3:
            self.log_warning("Insufficient scenes generated")
            return False
        
        # Validate each scene
        for scene in output_data["scenes"]:
            if not all(k in scene for k in ["description", "purpose", "importance"]):
                self.log_warning(f"Scene missing required fields")
                return False
        
        return True
    
    async def _analyze_story_structure(
        self,
        text: str,
        genre: str,
        themes: List[str]
    ) -> Dict[str, Any]:
        """Analyze and create story structure."""
        
        # Detect story beats
        text_length = len(text)
        act1_end = int(text_length * 0.25)
        act2_end = int(text_length * 0.75)
        
        # Extract acts
        act1_text = text[:act1_end]
        act2_text = text[act1_end:act2_end]
        act3_text = text[act2_end:]
        
        structure = {
            "type": "three_act",
            "act1": {
                "title": "導入・設定",
                "content": self._summarize_text(act1_text, 100),
                "purpose": "世界観とキャラクター紹介",
                "percentage": 25,
                "key_elements": self._extract_key_elements(act1_text)
            },
            "act2": {
                "title": "展開・対立",
                "content": self._summarize_text(act2_text, 150),
                "purpose": "メインの物語展開と困難",
                "percentage": 50,
                "key_elements": self._extract_key_elements(act2_text)
            },
            "act3": {
                "title": "解決・結末",
                "content": self._summarize_text(act3_text, 100),
                "purpose": "クライマックスと解決",
                "percentage": 25,
                "key_elements": self._extract_key_elements(act3_text)
            }
        }
        
        return structure
    
    async def _divide_into_scenes(
        self,
        text: str,
        story_structure: Dict[str, Any],
        estimated_pages: int,
        genre: str
    ) -> List[Dict[str, Any]]:
        """Divide story into scenes."""
        
        scenes = []
        
        # Calculate scenes per act
        total_scenes = max(estimated_pages, 8)  # At least 1 scene per page
        act1_scenes = int(total_scenes * 0.25)
        act2_scenes = int(total_scenes * 0.5)
        act3_scenes = total_scenes - act1_scenes - act2_scenes
        
        scene_counter = 1
        
        # Act 1 scenes
        for i in range(act1_scenes):
            scenes.append({
                "scene_number": scene_counter,
                "act": 1,
                "description": f"導入シーン {i+1}",
                "purpose": self._determine_scene_purpose(1, i, act1_scenes),
                "emotion": self._determine_emotion(genre, 1, i),
                "importance": "high" if i == 0 else "medium",
                "location": self._generate_location(genre, 1),
                "characters_present": ["protagonist"],
                "estimated_panels": self._estimate_panels(genre, "medium")
            })
            scene_counter += 1
        
        # Act 2 scenes
        for i in range(act2_scenes):
            importance = "high" if i == act2_scenes // 2 else "medium"
            scenes.append({
                "scene_number": scene_counter,
                "act": 2,
                "description": f"展開シーン {i+1}",
                "purpose": self._determine_scene_purpose(2, i, act2_scenes),
                "emotion": self._determine_emotion(genre, 2, i),
                "importance": importance,
                "location": self._generate_location(genre, 2),
                "characters_present": self._determine_characters(2, i),
                "estimated_panels": self._estimate_panels(genre, importance)
            })
            scene_counter += 1
        
        # Act 3 scenes
        for i in range(act3_scenes):
            importance = "high" if i >= act3_scenes - 2 else "medium"
            scenes.append({
                "scene_number": scene_counter,
                "act": 3,
                "description": f"解決シーン {i+1}",
                "purpose": self._determine_scene_purpose(3, i, act3_scenes),
                "emotion": self._determine_emotion(genre, 3, i),
                "importance": importance,
                "location": self._generate_location(genre, 3),
                "characters_present": self._determine_characters(3, i),
                "estimated_panels": self._estimate_panels(genre, importance)
            })
            scene_counter += 1
        
        return scenes
    
    def _select_structure_type(self, genre: str) -> str:
        """Select appropriate story structure type."""
        
        if genre in ["action", "fantasy", "sci_fi"]:
            return "hero_journey"
        elif genre in ["romance", "slice_of_life"]:
            return "kishōtenketsu"
        else:
            return "three_act"
    
    def _summarize_text(self, text: str, max_length: int) -> str:
        """Summarize text segment."""
        
        # Simple truncation for now
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    
    def _extract_key_elements(self, text: str) -> List[str]:
        """Extract key story elements from text."""
        
        elements = []
        
        # Look for action words
        action_words = ["戦", "走", "飛", "叫", "泣", "笑", "愛", "憎"]
        for word in action_words:
            if word in text:
                elements.append(f"{word}のシーン")
        
        # Limit to 5 elements
        return elements[:5] if elements else ["物語の展開"]
    
    def _determine_scene_purpose(self, act: int, scene_index: int, total_scenes: int) -> str:
        """Determine the purpose of a scene."""
        
        if act == 1:
            if scene_index == 0:
                return "世界観の導入"
            elif scene_index == total_scenes - 1:
                return "事件の発生"
            else:
                return "キャラクター紹介"
        
        elif act == 2:
            if scene_index == 0:
                return "新たな展開"
            elif scene_index == total_scenes // 2:
                return "中間点の転換"
            elif scene_index == total_scenes - 1:
                return "最大の危機"
            else:
                return "試練と成長"
        
        else:  # act == 3
            if scene_index == 0:
                return "最終対決への準備"
            elif scene_index == total_scenes - 2:
                return "クライマックス"
            elif scene_index == total_scenes - 1:
                return "エピローグ"
            else:
                return "解決への道"
    
    def _determine_emotion(self, genre: str, act: int, scene_index: int) -> str:
        """Determine emotional tone of scene."""
        
        emotion_patterns = {
            "action": {
                1: ["curiosity", "excitement"],
                2: ["tension", "determination", "fear"],
                3: ["triumph", "relief"]
            },
            "romance": {
                1: ["anticipation", "joy"],
                2: ["longing", "conflict", "passion"],
                3: ["resolution", "happiness"]
            },
            "mystery": {
                1: ["intrigue", "suspicion"],
                2: ["confusion", "revelation", "danger"],
                3: ["understanding", "justice"]
            }
        }
        
        genre_emotions = emotion_patterns.get(genre, {
            1: ["neutral"],
            2: ["tension"],
            3: ["resolution"]
        })
        
        act_emotions = genre_emotions.get(act, ["neutral"])
        
        import random
        return random.choice(act_emotions)
    
    def _generate_location(self, genre: str, act: int) -> str:
        """Generate appropriate location for scene."""
        
        location_templates = {
            "fantasy": {
                1: ["村", "森の入り口", "宿屋"],
                2: ["ダンジョン", "山道", "古代遺跡"],
                3: ["魔王城", "聖地", "故郷"]
            },
            "romance": {
                1: ["学校", "カフェ", "街"],
                2: ["公園", "海辺", "祭り"],
                3: ["展望台", "空港", "教会"]
            },
            "action": {
                1: ["基地", "都市", "訓練場"],
                2: ["戦場", "敵地", "追跡現場"],
                3: ["最終決戦場", "本部", "平和な街"]
            }
        }
        
        genre_locations = location_templates.get(genre, {
            1: ["開始地点"],
            2: ["中間地点"],
            3: ["終了地点"]
        })
        
        act_locations = genre_locations.get(act, ["どこか"])
        
        import random
        return random.choice(act_locations)
    
    def _determine_characters(self, act: int, scene_index: int) -> List[str]:
        """Determine which characters appear in scene."""
        
        characters = ["protagonist"]
        
        if act == 1 and scene_index > 0:
            characters.append("sidekick")
        elif act == 2:
            if scene_index % 3 == 0:
                characters.append("antagonist")
            else:
                characters.append("sidekick")
        elif act == 3:
            characters.extend(["sidekick", "antagonist"])
        
        return characters
    
    def _estimate_panels(self, genre: str, importance: str) -> int:
        """Estimate number of panels for scene."""
        
        base_panels = {
            "high": 6,
            "medium": 4,
            "low": 2
        }
        
        genre_multiplier = {
            "action": 1.2,
            "romance": 0.8,
            "mystery": 1.0,
            "fantasy": 1.1
        }
        
        base = base_panels.get(importance, 4)
        multiplier = genre_multiplier.get(genre, 1.0)
        
        return int(base * multiplier)
    
    def _analyze_pacing(self, scenes: List[Dict[str, Any]], genre: str) -> Dict[str, Any]:
        """Analyze story pacing."""
        
        pacing_pattern = self.pacing_patterns.get(genre, {
            "fast": 33,
            "medium": 34,
            "slow": 33
        })
        
        total_scenes = len(scenes)
        
        pacing = {
            "pattern": pacing_pattern,
            "distribution": {
                "fast": int(total_scenes * pacing_pattern["fast"] / 100),
                "medium": int(total_scenes * pacing_pattern["medium"] / 100),
                "slow": int(total_scenes * pacing_pattern["slow"] / 100)
            },
            "rhythm": self._determine_rhythm(genre),
            "tension_curve": self._create_tension_curve(scenes)
        }
        
        return pacing
    
    def _determine_rhythm(self, genre: str) -> str:
        """Determine pacing rhythm."""
        
        rhythm_patterns = {
            "action": "escalating",
            "romance": "wave",
            "mystery": "building",
            "slice_of_life": "steady"
        }
        
        return rhythm_patterns.get(genre, "balanced")
    
    def _create_tension_curve(self, scenes: List[Dict[str, Any]]) -> List[float]:
        """Create tension curve for story."""
        
        curve = []
        total = len(scenes)
        
        for i, scene in enumerate(scenes):
            position = i / total
            
            # Basic three-act tension curve
            if position < 0.25:  # Act 1
                tension = 0.3 + (position * 1.2)
            elif position < 0.75:  # Act 2
                tension = 0.5 + (position * 0.8)
            else:  # Act 3
                if position < 0.9:
                    tension = 0.9
                else:
                    tension = 0.4  # Resolution
            
            # Adjust for scene importance
            if scene["importance"] == "high":
                tension = min(1.0, tension * 1.2)
            
            curve.append(round(tension, 2))
        
        return curve
    
    def _create_timeline(self, scenes: List[Dict[str, Any]], pages: int) -> List[Dict[str, Any]]:
        """Create timeline mapping scenes to pages."""
        
        timeline = []
        scenes_per_page = len(scenes) / pages
        
        for page in range(1, pages + 1):
            start_scene = int((page - 1) * scenes_per_page)
            end_scene = int(page * scenes_per_page)
            
            page_scenes = scenes[start_scene:end_scene]
            
            timeline.append({
                "page": page,
                "scenes": [s["scene_number"] for s in page_scenes],
                "primary_content": page_scenes[0]["description"] if page_scenes else "",
                "act": page_scenes[0]["act"] if page_scenes else 1
            })
        
        return timeline
    
    def _extract_plot_points(self, story_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Extract major plot points."""
        
        return {
            "inciting_incident": {
                "description": "物語を動かす出来事",
                "location": "Act 1 終盤",
                "impact": "high"
            },
            "turning_point1": {
                "description": "第一の転換点",
                "location": "Act 2 開始",
                "impact": "medium"
            },
            "midpoint": {
                "description": "物語の中間点",
                "location": "Act 2 中盤",
                "impact": "high"
            },
            "turning_point2": {
                "description": "第二の転換点",
                "location": "Act 2 終盤",
                "impact": "high"
            },
            "climax": {
                "description": "クライマックス",
                "location": "Act 3 中盤",
                "impact": "very_high"
            },
            "resolution": {
                "description": "解決と結末",
                "location": "Act 3 終盤",
                "impact": "medium"
            }
        }
    
    def _analyze_conflict(self, text: str, themes: List[str]) -> Dict[str, Any]:
        """Analyze story conflict."""
        
        conflict_types = []
        
        # Detect conflict types
        if any(word in text for word in ["敵", "戦", "対立"]):
            conflict_types.append("external_physical")
        if any(word in text for word in ["心", "悩み", "迷い"]):
            conflict_types.append("internal_psychological")
        if any(word in text for word in ["社会", "世界", "組織"]):
            conflict_types.append("societal")
        
        if not conflict_types:
            conflict_types.append("interpersonal")
        
        return {
            "types": conflict_types,
            "primary": conflict_types[0] if conflict_types else "unknown",
            "intensity": self._assess_conflict_intensity(text),
            "resolution_type": self._determine_resolution_type(themes)
        }
    
    def _assess_conflict_intensity(self, text: str) -> str:
        """Assess conflict intensity."""
        
        intensity_words = {
            "high": ["死", "破壊", "終末", "絶望"],
            "medium": ["戦い", "対決", "困難", "危機"],
            "low": ["問題", "悩み", "迷い", "選択"]
        }
        
        for level, words in intensity_words.items():
            if any(word in text for word in words):
                return level
        
        return "medium"
    
    def _determine_resolution_type(self, themes: List[str]) -> str:
        """Determine how conflict is resolved."""
        
        if "成長" in themes:
            return "growth"
        elif "友情" in themes or "仲間" in themes:
            return "cooperation"
        elif "愛" in themes:
            return "love"
        elif "正義" in themes:
            return "justice"
        else:
            return "triumph"
    
    def _create_emotional_arc(self, scenes: List[Dict[str, Any]], genre: str) -> List[str]:
        """Create emotional arc for story."""
        
        emotional_arcs = {
            "action": ["anticipation", "excitement", "fear", "determination", "triumph"],
            "romance": ["curiosity", "attraction", "conflict", "realization", "joy"],
            "mystery": ["intrigue", "confusion", "discovery", "revelation", "satisfaction"],
            "fantasy": ["wonder", "challenge", "growth", "crisis", "victory"]
        }
        
        arc = emotional_arcs.get(genre, ["beginning", "middle", "end"])
        
        # Stretch arc to match scene count
        emotional_timeline = []
        scenes_per_emotion = len(scenes) / len(arc)
        
        for i, scene in enumerate(scenes):
            emotion_index = min(int(i / scenes_per_emotion), len(arc) - 1)
            emotional_timeline.append(arc[emotion_index])
        
        return emotional_timeline
    
    def _allocate_pages(self, scenes: List[Dict[str, Any]], total_pages: int) -> List[Dict[str, Any]]:
        """Allocate scenes to pages."""
        
        allocation = []
        
        # Calculate importance score for each scene
        scene_scores = []
        for scene in scenes:
            score = {
                "high": 3,
                "medium": 2,
                "low": 1
            }.get(scene["importance"], 1)
            scene_scores.append(score)
        
        total_score = sum(scene_scores)
        
        # Allocate pages proportionally
        current_page = 1
        accumulated_score = 0
        page_scenes = []
        
        for i, scene in enumerate(scenes):
            page_scenes.append(scene["scene_number"])
            accumulated_score += scene_scores[i]
            
            # Check if we should move to next page
            expected_page = int((accumulated_score / total_score) * total_pages) + 1
            
            if expected_page > current_page or i == len(scenes) - 1:
                allocation.append({
                    "page": current_page,
                    "scenes": page_scenes.copy(),
                    "panel_count": sum(scenes[j-1]["estimated_panels"] 
                                     for j in page_scenes if j <= len(scenes))
                })
                current_page = expected_page
                page_scenes = []
        
        return allocation
    
    async def generate_preview(
        self,
        output_data: Dict[str, Any],
        quality_level: str = "high"
    ) -> Dict[str, Any]:
        """Generate preview for phase 3 results."""
        
        preview = {
            "phase": self.phase_number,
            "title": "ストーリー構成",
            "structure_visualization": {
                "type": output_data.get("structure_type", "three_act"),
                "acts": self._visualize_acts(output_data.get("story_structure", {}))
            },
            "scene_timeline": [
                {
                    "scene": scene.get("scene_number"),
                    "purpose": scene.get("purpose"),
                    "emotion": scene.get("emotion"),
                    "importance": scene.get("importance")
                }
                for scene in output_data.get("scenes", [])[:8]  # First 8 scenes
            ],
            "plot_curve": {
                "tension": output_data.get("pacing", {}).get("tension_curve", []),
                "emotional_arc": output_data.get("emotional_arc", [])
            },
            "key_points": output_data.get("plot_points", {})
        }
        
        return preview
    
    def _visualize_acts(self, story_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create visual representation of acts."""
        
        visualization = []
        
        for act_key in ["act1", "act2", "act3"]:
            if act_key in story_structure:
                act = story_structure[act_key]
                visualization.append({
                    "name": act.get("title", act_key),
                    "percentage": act.get("percentage", 33),
                    "content": act.get("content", "")[:100],
                    "key_elements": act.get("key_elements", [])[:3]
                })
        
        return visualization

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
"""Phase 4: Name Generation (Panel Layout and Composition) Agent - CRITICAL PHASE."""

from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
import json
import math

from app.agents.base_agent import BaseAgent
from app.core.config import settings
from app.services.vertex_ai_service import VertexAIService


class Phase4NameAgent(BaseAgent):
    """Agent for name generation (panel layout, composition, camera work) - Most important phase."""
    
    def __init__(self):
        super().__init__(
            phase_number=4,
            phase_name="ネーム生成",
            timeout_seconds=settings.phase_timeouts[4]
        )
        
        # Panel layout patterns
        self.layout_patterns = {
            "standard": {
                "panels_per_page": 5,
                "variation": 2,
                "complexity": "medium"
            },
            "action": {
                "panels_per_page": 4,
                "variation": 3,
                "complexity": "high"
            },
            "dialogue": {
                "panels_per_page": 6,
                "variation": 1,
                "complexity": "low"
            },
            "dramatic": {
                "panels_per_page": 3,
                "variation": 2,
                "complexity": "high"
            }
        }
        
        # Camera angles
        self.camera_angles = {
            "extreme_long": {"distance": 5, "impact": "establishing", "frequency": 0.05},
            "long": {"distance": 4, "impact": "context", "frequency": 0.15},
            "medium": {"distance": 3, "impact": "standard", "frequency": 0.40},
            "close": {"distance": 2, "impact": "emotion", "frequency": 0.25},
            "extreme_close": {"distance": 1, "impact": "detail", "frequency": 0.10},
            "bird_eye": {"distance": 4, "impact": "overview", "frequency": 0.03},
            "worm_eye": {"distance": 3, "impact": "dramatic", "frequency": 0.02}
        }
        
        # Composition rules
        self.composition_rules = {
            "rule_of_thirds": 0.4,
            "golden_ratio": 0.2,
            "symmetrical": 0.15,
            "diagonal": 0.15,
            "centered": 0.1
        }
        
        # Panel shapes
        self.panel_shapes = {
            "rectangle": {"frequency": 0.7, "aspect_ratios": [(4, 3), (16, 9), (3, 2)]},
            "square": {"frequency": 0.15, "aspect_ratios": [(1, 1)]},
            "vertical": {"frequency": 0.08, "aspect_ratios": [(2, 3), (9, 16)]},
            "horizontal": {"frequency": 0.05, "aspect_ratios": [(3, 1), (4, 1)]},
            "irregular": {"frequency": 0.02, "aspect_ratios": None}
        }
        
        # Vertex AI サービス初期化
        self.vertex_ai = VertexAIService()
    
    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: UUID,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Process name generation - the most critical phase for manga creation.
        
        Args:
            input_data: Contains original text
            session_id: Current session ID
            previous_results: Results from phases 1-3
            
        Returns:
            Complete panel layout with camera work and composition
        """
        
        # Extract from previous phases
        phase1 = previous_results.get(1, {}) if previous_results else {}
        phase2 = previous_results.get(2, {}) if previous_results else {}
        phase3 = previous_results.get(3, {}) if previous_results else {}
        
        genre = phase1.get("genre", "general")
        characters = phase2.get("characters", [])
        scenes = phase3.get("scenes", [])
        page_allocation = phase3.get("page_allocation", [])
        pacing = phase3.get("pacing", {})
        
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
                pages = ai_result.get("panel_layouts", []) if ai_result else await self._generate_panel_layouts(scenes, page_allocation, genre, pacing)
                
            else:
                # Fallback to rule-based analysis
                self.log_warning(f"Gemini Pro failed, using fallback: {ai_response.get('error', 'Unknown error')}")
                pages = await self._generate_panel_layouts(scenes, page_allocation, genre, pacing)
                
        except Exception as e:
            # Fallback to rule-based analysis on error
            self.log_error(f"AI analysis failed, using fallback: {str(e)}")
            pages = await self._generate_panel_layouts(scenes, page_allocation, genre, pacing)
        
        # Assign camera angles and compositions
        pages_with_camera = await self._assign_camera_work(
            pages,
            scenes,
            genre,
            characters
        )
        
        # Calculate visual flow
        pages_with_flow = self._calculate_visual_flow(pages_with_camera)
        
        # Add dramatic effects
        final_pages = self._add_dramatic_effects(
            pages_with_flow,
            phase3.get("plot_points", {}),
            genre
        )
        
        # Generate detailed shot descriptions
        shot_list = self._generate_shot_list(final_pages, characters)
        
        result = {
            "pages": final_pages,
            "total_pages": len(final_pages),
            "total_panels": sum(len(page["panels"]) for page in final_pages),
            "shot_list": shot_list,
            "layout_analysis": self._analyze_layout(final_pages),
            "camera_statistics": self._calculate_camera_statistics(final_pages),
            "composition_guide": self._create_composition_guide(final_pages),
            "reading_flow": self._analyze_reading_flow(final_pages),
            "dramatic_moments": self._identify_dramatic_moments(final_pages),
            "panel_transitions": self._analyze_transitions(final_pages)
        }
        
        return result
    
    async def generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate Gemini Pro prompt for name generation."""
        
        scenes = input_data.get("scenes", [])
        genre = input_data.get("genre", "general")
        characters = input_data.get("characters", [])
        
        prompt = f"""あなたは漫画のネーム（コマ割り）の専門家です。
以下のシーンを魅力的な漫画のコマ割りに変換してください。

シーン情報:
{json.dumps(scenes[:3], ensure_ascii=False, indent=2)}

ジャンル: {genre}
キャラクター: {json.dumps([c.get("name") for c in characters], ensure_ascii=False)}

以下の要素を含むネーム設計をJSON形式で出力してください：

1. pages (各ページのレイアウト):
   - page_number: ページ番号
   - panels: コマのリスト
     - panel_id: コマID
     - size: large/medium/small
     - position: {x, y, width, height} (0-1の相対座標)
     - camera_angle: extreme_long/long/medium/close/extreme_close
     - camera_position: normal/bird_eye/worm_eye
     - composition: rule_of_thirds/golden_ratio/symmetrical/diagonal/centered
     - content: コマの内容説明
     - characters_in_panel: 登場キャラクター
     - dialog_preview: セリフのプレビュー

2. visual_flow:
   - 視線誘導のパターン
   - 読みやすさのスコア

3. dramatic_effects:
   - 見開きページの使用
   - スピード線や効果線の配置
   - インパクトのあるコマの配置

JSONフォーマットで回答してください。"""
        
        return prompt
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate phase 4 output."""
        
        required_keys = ["pages", "total_panels", "shot_list", "layout_analysis"]
        
        for key in required_keys:
            if key not in output_data:
                self.log_warning(f"Missing required key: {key}")
                return False
        
        # Validate pages
        if not output_data["pages"] or len(output_data["pages"]) < 1:
            self.log_warning("No pages generated")
            return False
        
        # Validate each page has panels
        for page in output_data["pages"]:
            if not page.get("panels") or len(page["panels"]) < 1:
                self.log_warning(f"Page {page.get('page_number')} has no panels")
                return False
            
            # Validate panel structure
            for panel in page["panels"]:
                required_panel_keys = ["panel_id", "size", "position", "camera_angle"]
                if not all(k in panel for k in required_panel_keys):
                    self.log_warning("Panel missing required fields")
                    return False
        
        return True
    
    async def _generate_panel_layouts(
        self,
        scenes: List[Dict[str, Any]],
        page_allocation: List[Dict[str, Any]],
        genre: str,
        pacing: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate panel layouts for all pages - CRITICAL FUNCTION."""
        
        pages = []
        
        # Determine base layout pattern
        layout_pattern = self._select_layout_pattern(genre, pacing)
        
        for page_info in page_allocation:
            page_num = page_info.get("page", 1)
            page_scenes = page_info.get("scenes", [])
            
            # Get scenes for this page
            scenes_on_page = [s for s in scenes if s["scene_number"] in page_scenes]
            
            # Determine panel count and layout
            panel_count = self._calculate_panel_count(
                scenes_on_page,
                layout_pattern,
                pacing
            )
            
            # Generate panel layout
            panels = self._create_panel_layout(
                panel_count,
                scenes_on_page,
                page_num,
                genre
            )
            
            pages.append({
                "page_number": page_num,
                "panels": panels,
                "scene_numbers": page_scenes,
                "layout_type": self._determine_layout_type(panels),
                "reading_order": self._establish_reading_order(panels)
            })
        
        return pages
    
    def _select_layout_pattern(self, genre: str, pacing: Dict[str, Any]) -> Dict[str, Any]:
        """Select appropriate layout pattern based on genre and pacing."""
        
        if genre == "action":
            return self.layout_patterns["action"]
        elif pacing.get("rhythm") == "steady":
            return self.layout_patterns["dialogue"]
        elif any(p > 0.5 for p in pacing.get("tension_curve", [])):
            return self.layout_patterns["dramatic"]
        else:
            return self.layout_patterns["standard"]
    
    def _calculate_panel_count(
        self,
        scenes: List[Dict[str, Any]],
        layout_pattern: Dict[str, Any],
        pacing: Dict[str, Any]
    ) -> int:
        """Calculate optimal panel count for page."""
        
        base_count = layout_pattern["panels_per_page"]
        variation = layout_pattern["variation"]
        
        # Adjust for scene importance
        importance_modifier = 0
        for scene in scenes:
            if scene.get("importance") == "high":
                importance_modifier -= 1  # Fewer panels for important scenes
            elif scene.get("importance") == "low":
                importance_modifier += 1  # More panels for less important scenes
        
        # Apply variation
        import random
        variation_amount = random.randint(-variation, variation)
        
        final_count = base_count + importance_modifier + variation_amount
        
        # Clamp between reasonable limits
        return max(2, min(8, final_count))
    
    def _create_panel_layout(
        self,
        panel_count: int,
        scenes: List[Dict[str, Any]],
        page_num: int,
        genre: str
    ) -> List[Dict[str, Any]]:
        """Create specific panel layout for a page."""
        
        panels = []
        
        # Select layout template
        layout_template = self._select_layout_template(panel_count, genre)
        
        for i in range(panel_count):
            panel_id = f"p{page_num}_panel{i+1}"
            
            # Determine panel size based on position and importance
            size = self._determine_panel_size(i, panel_count, scenes)
            
            # Calculate position
            position = self._calculate_panel_position(
                i,
                panel_count,
                layout_template,
                size
            )
            
            # Determine content
            scene_index = min(i * len(scenes) // panel_count, len(scenes) - 1)
            scene = scenes[scene_index] if scenes else {}
            
            panels.append({
                "panel_id": panel_id,
                "size": size,
                "position": position,
                "shape": self._select_panel_shape(size, genre),
                "border_style": self._select_border_style(scene.get("emotion", "neutral")),
                "content_description": scene.get("description", f"Panel {i+1}"),
                "scene_reference": scene.get("scene_number", 0),
                "importance": scene.get("importance", "medium")
            })
        
        return panels
    
    def _select_layout_template(self, panel_count: int, genre: str) -> str:
        """Select layout template based on panel count and genre."""
        
        templates = {
            2: ["horizontal_split", "vertical_split", "diagonal_split"],
            3: ["triangle", "L_shape", "vertical_thirds"],
            4: ["grid_2x2", "cross", "Z_pattern"],
            5: ["cross_plus_corner", "spiral", "asymmetric"],
            6: ["grid_2x3", "grid_3x2", "honeycomb"],
            7: ["mosaic", "circular", "free_form"],
            8: ["grid_2x4", "grid_4x2", "complex_mosaic"]
        }
        
        available_templates = templates.get(panel_count, ["free_form"])
        
        # Genre-specific preferences
        if genre == "action":
            preferred = ["diagonal_split", "Z_pattern", "spiral"]
        elif genre == "romance":
            preferred = ["vertical_split", "L_shape", "honeycomb"]
        else:
            preferred = available_templates
        
        # Select from preferred if available
        import random
        for template in preferred:
            if template in available_templates:
                return template
        
        return random.choice(available_templates)
    
    def _determine_panel_size(
        self,
        index: int,
        total_panels: int,
        scenes: List[Dict[str, Any]]
    ) -> str:
        """Determine panel size based on position and importance."""
        
        # First and last panels are often larger
        if index == 0 or index == total_panels - 1:
            return "large"
        
        # Check scene importance
        scene_index = min(index * len(scenes) // total_panels, len(scenes) - 1)
        if scenes and scene_index < len(scenes):
            scene = scenes[scene_index]
            if scene.get("importance") == "high":
                return "large"
            elif scene.get("importance") == "low":
                return "small"
        
        # Default distribution
        size_distribution = ["large"] * 2 + ["medium"] * 4 + ["small"] * 2
        import random
        return random.choice(size_distribution)
    
    def _calculate_panel_position(
        self,
        index: int,
        total_panels: int,
        layout_template: str,
        size: str
    ) -> Dict[str, float]:
        """Calculate panel position in page grid (0-1 normalized)."""
        
        # Size-based dimensions
        size_dimensions = {
            "large": {"width": 0.6, "height": 0.5},
            "medium": {"width": 0.4, "height": 0.35},
            "small": {"width": 0.3, "height": 0.25}
        }
        
        dims = size_dimensions.get(size, {"width": 0.35, "height": 0.3})
        
        # Template-based positioning
        if layout_template == "grid_2x2":
            row = index // 2
            col = index % 2
            return {
                "x": col * 0.5,
                "y": row * 0.5,
                "width": 0.48,
                "height": 0.48
            }
        elif layout_template == "vertical_split":
            return {
                "x": 0.02,
                "y": index * (1.0 / total_panels),
                "width": 0.96,
                "height": (0.96 / total_panels)
            }
        elif layout_template == "Z_pattern":
            # Z-shaped reading flow
            positions = [
                {"x": 0.02, "y": 0.02},  # Top-left
                {"x": 0.52, "y": 0.02},  # Top-right
                {"x": 0.27, "y": 0.35},  # Middle
                {"x": 0.02, "y": 0.68},  # Bottom-left
                {"x": 0.52, "y": 0.68}   # Bottom-right
            ]
            
            if index < len(positions):
                pos = positions[index]
                return {
                    "x": pos["x"],
                    "y": pos["y"],
                    "width": dims["width"],
                    "height": dims["height"]
                }
        
        # Default grid fallback
        cols = math.ceil(math.sqrt(total_panels))
        row = index // cols
        col = index % cols
        
        return {
            "x": col * (1.0 / cols) + 0.02,
            "y": row * (1.0 / cols) + 0.02,
            "width": (0.96 / cols),
            "height": (0.96 / cols)
        }
    
    def _select_panel_shape(self, size: str, genre: str) -> str:
        """Select panel shape based on size and genre."""
        
        if size == "large":
            # Large panels can be more varied
            shapes = ["rectangle", "horizontal", "vertical"]
            if genre == "action":
                shapes.append("diagonal")
        else:
            # Small panels are typically rectangular
            shapes = ["rectangle", "square"]
        
        import random
        return random.choice(shapes)
    
    def _select_border_style(self, emotion: str) -> str:
        """Select panel border style based on emotion."""
        
        border_styles = {
            "tension": "thick_jagged",
            "fear": "wavy",
            "excitement": "speed_lines",
            "calm": "thin_straight",
            "joy": "decorative",
            "neutral": "standard"
        }
        
        return border_styles.get(emotion, "standard")
    
    def _determine_layout_type(self, panels: List[Dict[str, Any]]) -> str:
        """Determine overall layout type of page."""
        
        panel_count = len(panels)
        large_panels = sum(1 for p in panels if p["size"] == "large")
        
        if large_panels >= panel_count * 0.5:
            return "impact"
        elif panel_count >= 6:
            return "dense"
        elif panel_count <= 3:
            return "sparse"
        else:
            return "balanced"
    
    def _establish_reading_order(self, panels: List[Dict[str, Any]]) -> List[str]:
        """Establish reading order for panels (right-to-left, top-to-bottom for manga)."""
        
        # Sort panels by position (manga reading order)
        sorted_panels = sorted(
            panels,
            key=lambda p: (
                p["position"]["y"],  # Top to bottom
                -p["position"]["x"]   # Right to left (negative for reverse)
            )
        )
        
        return [p["panel_id"] for p in sorted_panels]
    
    async def _assign_camera_work(
        self,
        pages: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        genre: str,
        characters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Assign camera angles and shots to panels - CRITICAL FOR VISUAL STORYTELLING."""
        
        for page in pages:
            for panel in page["panels"]:
                # Get associated scene
                scene_num = panel.get("scene_reference", 0)
                scene = next((s for s in scenes if s["scene_number"] == scene_num), {})
                
                # Determine camera angle
                camera_angle = self._select_camera_angle(
                    panel["size"],
                    panel["importance"],
                    scene.get("purpose", ""),
                    genre
                )
                
                # Determine camera position
                camera_position = self._select_camera_position(
                    scene.get("emotion", "neutral"),
                    panel["importance"]
                )
                
                # Determine composition
                composition = self._select_composition(
                    panel["size"],
                    scene.get("characters_present", []),
                    genre
                )
                
                # Add camera work to panel
                panel.update({
                    "camera_angle": camera_angle,
                    "camera_position": camera_position,
                    "composition": composition,
                    "focal_point": self._determine_focal_point(composition),
                    "depth_of_field": self._determine_depth_of_field(camera_angle),
                    "motion_blur": self._needs_motion_blur(scene, genre)
                })
        
        return pages
    
    def _select_camera_angle(
        self,
        panel_size: str,
        importance: str,
        scene_purpose: str,
        genre: str
    ) -> str:
        """Select appropriate camera angle for panel."""
        
        # Size-based preferences
        if panel_size == "large":
            if importance == "high":
                angles = ["extreme_long", "extreme_close", "bird_eye"]
            else:
                angles = ["long", "medium"]
        elif panel_size == "small":
            angles = ["close", "extreme_close"]
        else:
            angles = ["medium", "close"]
        
        # Purpose-based adjustments
        if "導入" in scene_purpose or "世界観" in scene_purpose:
            angles.append("extreme_long")
        elif "感情" in scene_purpose or "心" in scene_purpose:
            angles.extend(["close", "extreme_close"])
        elif "戦" in scene_purpose or "対決" in scene_purpose:
            angles.extend(["medium", "worm_eye"])
        
        # Genre preferences
        if genre == "action":
            angles.extend(["worm_eye", "bird_eye"])
        elif genre == "romance":
            angles.extend(["close", "extreme_close"])
        
        # Select based on frequency distribution
        import random
        angle_weights = {a: self.camera_angles[a]["frequency"] 
                        for a in angles if a in self.camera_angles}
        
        if angle_weights:
            total = sum(angle_weights.values())
            r = random.random() * total
            cumulative = 0
            for angle, weight in angle_weights.items():
                cumulative += weight
                if r <= cumulative:
                    return angle
        
        return "medium"  # Default
    
    def _select_camera_position(self, emotion: str, importance: str) -> str:
        """Select camera position (normal, high angle, low angle)."""
        
        if importance == "high":
            if emotion in ["fear", "tension"]:
                return "high_angle"  # Looking down
            elif emotion in ["triumph", "determination"]:
                return "low_angle"  # Looking up
        
        # Dramatic positions
        if emotion == "triumph":
            return "low_angle"
        elif emotion == "despair":
            return "high_angle"
        
        return "normal"
    
    def _select_composition(
        self,
        panel_size: str,
        characters_present: List[str],
        genre: str
    ) -> str:
        """Select composition rule for panel."""
        
        # Multiple characters favor certain compositions
        if len(characters_present) > 2:
            compositions = ["rule_of_thirds", "diagonal", "triangular"]
        elif len(characters_present) == 2:
            compositions = ["symmetrical", "rule_of_thirds", "golden_ratio"]
        else:
            compositions = list(self.composition_rules.keys())
        
        # Size preferences
        if panel_size == "large":
            # Large panels can use more complex compositions
            pass
        elif panel_size == "small":
            # Small panels need simpler compositions
            compositions = ["centered", "rule_of_thirds"]
        
        # Genre preferences
        if genre == "action":
            compositions.extend(["diagonal", "dynamic_symmetry"])
        elif genre == "romance":
            compositions.extend(["golden_ratio", "symmetrical"])
        
        # Select based on weights
        import random
        valid_compositions = [c for c in compositions if c in self.composition_rules]
        if valid_compositions:
            return random.choice(valid_compositions)
        
        return "rule_of_thirds"  # Default
    
    def _determine_focal_point(self, composition: str) -> Dict[str, float]:
        """Determine focal point based on composition."""
        
        focal_points = {
            "rule_of_thirds": {"x": 0.33, "y": 0.33},
            "golden_ratio": {"x": 0.382, "y": 0.618},
            "centered": {"x": 0.5, "y": 0.5},
            "diagonal": {"x": 0.3, "y": 0.3},
            "symmetrical": {"x": 0.5, "y": 0.5}
        }
        
        return focal_points.get(composition, {"x": 0.5, "y": 0.5})
    
    def _determine_depth_of_field(self, camera_angle: str) -> str:
        """Determine depth of field based on camera angle."""
        
        if camera_angle in ["extreme_close", "close"]:
            return "shallow"  # Blurred background
        elif camera_angle in ["extreme_long", "bird_eye"]:
            return "deep"  # Everything in focus
        else:
            return "normal"
    
    def _needs_motion_blur(self, scene: Dict[str, Any], genre: str) -> bool:
        """Determine if motion blur is needed."""
        
        if genre == "action":
            action_words = ["走", "飛", "戦", "跳", "動"]
            return any(word in scene.get("description", "") for word in action_words)
        
        return scene.get("emotion") == "excitement"
    
    def _calculate_visual_flow(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate visual flow for reading guidance."""
        
        for page in pages:
            panels = page["panels"]
            
            # Create flow vectors between panels
            flow_vectors = []
            reading_order = page.get("reading_order", [])
            
            for i in range(len(reading_order) - 1):
                current_id = reading_order[i]
                next_id = reading_order[i + 1]
                
                current_panel = next((p for p in panels if p["panel_id"] == current_id), None)
                next_panel = next((p for p in panels if p["panel_id"] == next_id), None)
                
                if current_panel and next_panel:
                    # Calculate flow vector
                    vector = {
                        "from": current_id,
                        "to": next_id,
                        "direction": self._calculate_flow_direction(
                            current_panel["position"],
                            next_panel["position"]
                        ),
                        "strength": self._calculate_flow_strength(
                            current_panel["size"],
                            next_panel["size"]
                        )
                    }
                    flow_vectors.append(vector)
            
            page["visual_flow"] = {
                "vectors": flow_vectors,
                "smoothness": self._calculate_flow_smoothness(flow_vectors),
                "reading_difficulty": self._assess_reading_difficulty(flow_vectors)
            }
        
        return pages
    
    def _calculate_flow_direction(self, from_pos: Dict, to_pos: Dict) -> str:
        """Calculate flow direction between panels."""
        
        dx = to_pos["x"] - from_pos["x"]
        dy = to_pos["y"] - from_pos["y"]
        
        if abs(dx) > abs(dy):
            return "left" if dx < 0 else "right"
        else:
            return "up" if dy < 0 else "down"
    
    def _calculate_flow_strength(self, from_size: str, to_size: str) -> float:
        """Calculate flow strength based on panel sizes."""
        
        size_values = {"large": 3, "medium": 2, "small": 1}
        from_val = size_values.get(from_size, 2)
        to_val = size_values.get(to_size, 2)
        
        # Stronger flow to larger panels
        return to_val / from_val
    
    def _calculate_flow_smoothness(self, flow_vectors: List[Dict]) -> float:
        """Calculate how smooth the reading flow is."""
        
        if len(flow_vectors) < 2:
            return 1.0
        
        # Check for consistent direction changes
        direction_changes = 0
        for i in range(len(flow_vectors) - 1):
            if flow_vectors[i]["direction"] != flow_vectors[i + 1]["direction"]:
                direction_changes += 1
        
        # Less direction changes = smoother flow
        smoothness = 1.0 - (direction_changes / len(flow_vectors))
        return max(0.0, smoothness)
    
    def _assess_reading_difficulty(self, flow_vectors: List[Dict]) -> str:
        """Assess reading difficulty based on flow."""
        
        if not flow_vectors:
            return "easy"
        
        # Count problematic patterns
        problems = 0
        
        for vector in flow_vectors:
            # Going up or left is harder to read
            if vector["direction"] in ["up", "left"]:
                problems += 1
            # Weak flow is harder to follow
            if vector["strength"] < 0.5:
                problems += 1
        
        difficulty_ratio = problems / (len(flow_vectors) * 2)
        
        if difficulty_ratio < 0.2:
            return "easy"
        elif difficulty_ratio < 0.4:
            return "medium"
        else:
            return "hard"
    
    def _add_dramatic_effects(
        self,
        pages: List[Dict[str, Any]],
        plot_points: Dict[str, Any],
        genre: str
    ) -> List[Dict[str, Any]]:
        """Add dramatic effects to key moments."""
        
        # Identify climax page
        climax_info = plot_points.get("climax", {})
        
        for page in pages:
            dramatic_effects = []
            
            # Check if this is a key moment
            for panel in page["panels"]:
                if panel.get("importance") == "high":
                    # Add appropriate effects
                    if genre == "action":
                        dramatic_effects.extend([
                            {"type": "speed_lines", "intensity": "high"},
                            {"type": "impact_burst", "position": panel["position"]}
                        ])
                    elif genre == "romance":
                        dramatic_effects.append(
                            {"type": "sparkle_effect", "density": "medium"}
                        )
                    elif genre == "horror":
                        dramatic_effects.append(
                            {"type": "shadow_gradient", "darkness": 0.7}
                        )
                
                # Check for emotional peaks
                if panel.get("camera_angle") == "extreme_close":
                    dramatic_effects.append(
                        {"type": "focus_vignette", "strength": 0.5}
                    )
            
            # Add page-level effects
            if page["layout_type"] == "impact":
                dramatic_effects.append(
                    {"type": "full_page_emphasis", "style": "radial_burst"}
                )
            
            page["dramatic_effects"] = dramatic_effects
        
        return pages
    
    def _generate_shot_list(
        self,
        pages: List[Dict[str, Any]],
        characters: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate detailed shot list for image generation."""
        
        shot_list = []
        shot_id = 1
        
        for page in pages:
            for panel in page["panels"]:
                # Create shot description
                shot = {
                    "shot_id": shot_id,
                    "page": page["page_number"],
                    "panel": panel["panel_id"],
                    "camera": {
                        "angle": panel.get("camera_angle", "medium"),
                        "position": panel.get("camera_position", "normal"),
                        "focal_length": self._determine_focal_length(
                            panel.get("camera_angle", "medium")
                        )
                    },
                    "composition": {
                        "rule": panel.get("composition", "rule_of_thirds"),
                        "focal_point": panel.get("focal_point", {"x": 0.5, "y": 0.5})
                    },
                    "content": panel.get("content_description", ""),
                    "characters": self._identify_characters_in_shot(
                        panel,
                        characters
                    ),
                    "lighting": self._determine_lighting(
                        panel.get("camera_position", "normal"),
                        page.get("scene_numbers", [])
                    ),
                    "mood": self._determine_mood(panel),
                    "effects": self._list_required_effects(panel, page)
                }
                
                shot_list.append(shot)
                shot_id += 1
        
        return shot_list
    
    def _determine_focal_length(self, camera_angle: str) -> str:
        """Determine focal length based on camera angle."""
        
        focal_lengths = {
            "extreme_long": "wide_angle_24mm",
            "long": "normal_35mm",
            "medium": "standard_50mm",
            "close": "portrait_85mm",
            "extreme_close": "macro_100mm",
            "bird_eye": "wide_angle_24mm",
            "worm_eye": "wide_angle_28mm"
        }
        
        return focal_lengths.get(camera_angle, "standard_50mm")
    
    def _identify_characters_in_shot(
        self,
        panel: Dict[str, Any],
        characters: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Identify which characters appear in shot."""
        
        # This would be determined by scene analysis
        # For now, return placeholder based on panel size
        if panel["size"] == "large":
            return [{"name": c["name"], "position": "center"} 
                   for c in characters[:2]]
        else:
            return [{"name": characters[0]["name"], "position": "center"}] if characters else []
    
    def _determine_lighting(self, camera_position: str, scene_numbers: List[int]) -> Dict[str, Any]:
        """Determine lighting setup for shot."""
        
        base_lighting = {
            "normal": {"key": "45_degrees", "fill": "soft", "rim": "subtle"},
            "high_angle": {"key": "top_down", "fill": "minimal", "rim": "none"},
            "low_angle": {"key": "bottom_up", "fill": "dramatic", "rim": "strong"}
        }
        
        lighting = base_lighting.get(camera_position, base_lighting["normal"])
        
        # Add time-of-day based on scene
        # Early scenes = morning, late scenes = evening
        if scene_numbers:
            avg_scene = sum(scene_numbers) / len(scene_numbers)
            if avg_scene < 3:
                lighting["time_of_day"] = "morning"
            elif avg_scene > 6:
                lighting["time_of_day"] = "evening"
            else:
                lighting["time_of_day"] = "afternoon"
        
        return lighting
    
    def _determine_mood(self, panel: Dict[str, Any]) -> str:
        """Determine mood of shot."""
        
        # Based on camera and importance
        if panel.get("importance") == "high":
            if panel.get("camera_angle") in ["extreme_close", "close"]:
                return "intense"
            else:
                return "epic"
        elif panel.get("camera_position") == "low_angle":
            return "heroic"
        elif panel.get("camera_position") == "high_angle":
            return "vulnerable"
        else:
            return "neutral"
    
    def _list_required_effects(
        self,
        panel: Dict[str, Any],
        page: Dict[str, Any]
    ) -> List[str]:
        """List required visual effects for shot."""
        
        effects = []
        
        if panel.get("motion_blur"):
            effects.append("motion_blur")
        
        if panel.get("depth_of_field") == "shallow":
            effects.append("bokeh_background")
        
        # Add dramatic effects from page
        for effect in page.get("dramatic_effects", []):
            if effect["type"] not in effects:
                effects.append(effect["type"])
        
        return effects
    
    def _analyze_layout(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall layout characteristics."""
        
        total_panels = sum(len(page["panels"]) for page in pages)
        panel_sizes = []
        layout_types = []
        
        for page in pages:
            for panel in page["panels"]:
                panel_sizes.append(panel["size"])
            layout_types.append(page.get("layout_type", "standard"))
        
        # Calculate statistics
        size_distribution = {
            "large": panel_sizes.count("large") / total_panels,
            "medium": panel_sizes.count("medium") / total_panels,
            "small": panel_sizes.count("small") / total_panels
        }
        
        layout_distribution = {
            layout: layout_types.count(layout) / len(pages)
            for layout in set(layout_types)
        }
        
        return {
            "total_panels": total_panels,
            "average_panels_per_page": total_panels / len(pages),
            "size_distribution": size_distribution,
            "layout_distribution": layout_distribution,
            "complexity": self._assess_layout_complexity(pages)
        }
    
    def _assess_layout_complexity(self, pages: List[Dict[str, Any]]) -> str:
        """Assess overall layout complexity."""
        
        avg_panels = sum(len(p["panels"]) for p in pages) / len(pages)
        
        if avg_panels < 4:
            return "simple"
        elif avg_panels < 6:
            return "moderate"
        else:
            return "complex"
    
    def _calculate_camera_statistics(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate camera usage statistics."""
        
        angles = []
        positions = []
        compositions = []
        
        for page in pages:
            for panel in page["panels"]:
                angles.append(panel.get("camera_angle", "medium"))
                positions.append(panel.get("camera_position", "normal"))
                compositions.append(panel.get("composition", "rule_of_thirds"))
        
        total = len(angles)
        
        return {
            "angle_distribution": {
                angle: angles.count(angle) / total
                for angle in set(angles)
            },
            "position_distribution": {
                pos: positions.count(pos) / total
                for pos in set(positions)
            },
            "composition_distribution": {
                comp: compositions.count(comp) / total
                for comp in set(compositions)
            },
            "variety_score": self._calculate_variety_score(angles, positions, compositions)
        }
    
    def _calculate_variety_score(self, angles: List, positions: List, compositions: List) -> float:
        """Calculate variety score for camera work."""
        
        # More unique values = higher variety
        angle_variety = len(set(angles)) / len(angles) if angles else 0
        position_variety = len(set(positions)) / len(positions) if positions else 0
        composition_variety = len(set(compositions)) / len(compositions) if compositions else 0
        
        return (angle_variety + position_variety + composition_variety) / 3
    
    def _create_composition_guide(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create composition guidelines for artists."""
        
        guidelines = {
            "primary_compositions": [],
            "focal_points": [],
            "balance_analysis": []
        }
        
        for page in pages:
            page_balance = {"left": 0, "right": 0, "top": 0, "bottom": 0}
            
            for panel in page["panels"]:
                # Track compositions
                comp = panel.get("composition", "rule_of_thirds")
                if comp not in guidelines["primary_compositions"]:
                    guidelines["primary_compositions"].append(comp)
                
                # Track focal points
                focal = panel.get("focal_point", {"x": 0.5, "y": 0.5})
                guidelines["focal_points"].append(focal)
                
                # Analyze balance
                pos = panel["position"]
                if pos["x"] < 0.5:
                    page_balance["left"] += 1
                else:
                    page_balance["right"] += 1
                
                if pos["y"] < 0.5:
                    page_balance["top"] += 1
                else:
                    page_balance["bottom"] += 1
            
            guidelines["balance_analysis"].append(page_balance)
        
        return guidelines
    
    def _analyze_reading_flow(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze reading flow patterns."""
        
        flow_analysis = {
            "average_smoothness": 0,
            "difficulty_distribution": {"easy": 0, "medium": 0, "hard": 0},
            "problematic_pages": []
        }
        
        smoothness_scores = []
        
        for page in pages:
            flow = page.get("visual_flow", {})
            smoothness = flow.get("smoothness", 0.5)
            difficulty = flow.get("reading_difficulty", "medium")
            
            smoothness_scores.append(smoothness)
            flow_analysis["difficulty_distribution"][difficulty] += 1
            
            if smoothness < 0.5 or difficulty == "hard":
                flow_analysis["problematic_pages"].append(page["page_number"])
        
        if smoothness_scores:
            flow_analysis["average_smoothness"] = sum(smoothness_scores) / len(smoothness_scores)
        
        # Convert to percentages
        total_pages = len(pages)
        for key in flow_analysis["difficulty_distribution"]:
            flow_analysis["difficulty_distribution"][key] /= total_pages
        
        return flow_analysis
    
    def _identify_dramatic_moments(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify key dramatic moments in the layout."""
        
        dramatic_moments = []
        
        for page in pages:
            for panel in page["panels"]:
                if panel.get("importance") == "high" or panel.get("size") == "large":
                    moment = {
                        "page": page["page_number"],
                        "panel": panel["panel_id"],
                        "type": self._classify_dramatic_type(panel),
                        "intensity": self._calculate_drama_intensity(panel, page)
                    }
                    dramatic_moments.append(moment)
        
        # Sort by intensity
        dramatic_moments.sort(key=lambda x: x["intensity"], reverse=True)
        
        return dramatic_moments[:10]  # Top 10 moments
    
    def _classify_dramatic_type(self, panel: Dict[str, Any]) -> str:
        """Classify type of dramatic moment."""
        
        if panel.get("camera_angle") == "extreme_close":
            return "emotional_peak"
        elif panel.get("camera_angle") == "extreme_long":
            return "epic_reveal"
        elif panel.get("camera_position") == "worm_eye":
            return "heroic_moment"
        elif panel.get("size") == "large":
            return "impact_moment"
        else:
            return "tension_point"
    
    def _calculate_drama_intensity(self, panel: Dict[str, Any], page: Dict[str, Any]) -> float:
        """Calculate dramatic intensity of moment."""
        
        intensity = 0.5  # Base
        
        # Size contribution
        if panel["size"] == "large":
            intensity += 0.3
        elif panel["size"] == "small":
            intensity -= 0.1
        
        # Importance contribution
        if panel.get("importance") == "high":
            intensity += 0.2
        
        # Camera contribution
        if panel.get("camera_angle") in ["extreme_close", "extreme_long"]:
            intensity += 0.15
        
        if panel.get("camera_position") != "normal":
            intensity += 0.1
        
        # Page effects
        if page.get("dramatic_effects"):
            intensity += 0.1 * len(page["dramatic_effects"])
        
        return min(1.0, intensity)
    
    def _analyze_transitions(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze panel-to-panel transitions."""
        
        transition_types = {
            "moment_to_moment": 0,
            "action_to_action": 0,
            "subject_to_subject": 0,
            "scene_to_scene": 0,
            "aspect_to_aspect": 0,
            "non_sequitur": 0
        }
        
        for page in pages:
            panels = page["panels"]
            
            for i in range(len(panels) - 1):
                current = panels[i]
                next_panel = panels[i + 1]
                
                transition_type = self._classify_transition(current, next_panel)
                transition_types[transition_type] += 1
        
        total_transitions = sum(transition_types.values())
        
        if total_transitions > 0:
            # Convert to percentages
            for key in transition_types:
                transition_types[key] = transition_types[key] / total_transitions
        
        return {
            "types": transition_types,
            "dominant_type": max(transition_types, key=transition_types.get),
            "variety": len([t for t in transition_types.values() if t > 0.1])
        }
    
    def _classify_transition(self, panel1: Dict[str, Any], panel2: Dict[str, Any]) -> str:
        """Classify transition type between panels."""
        
        # Simplified classification based on camera changes
        angle1 = panel1.get("camera_angle", "medium")
        angle2 = panel2.get("camera_angle", "medium")
        
        if angle1 == angle2:
            if panel1.get("size") == panel2.get("size"):
                return "moment_to_moment"
            else:
                return "action_to_action"
        else:
            angle_distance = abs(
                list(self.camera_angles.keys()).index(angle1) -
                list(self.camera_angles.keys()).index(angle2)
            )
            
            if angle_distance == 1:
                return "subject_to_subject"
            elif angle_distance > 3:
                return "scene_to_scene"
            else:
                return "aspect_to_aspect"
    
    async def generate_preview(
        self,
        output_data: Dict[str, Any],
        quality_level: str = "high"
    ) -> Dict[str, Any]:
        """Generate preview for phase 4 results."""
        
        pages = output_data.get("pages", [])
        
        # Select sample pages for preview
        sample_pages = pages[:2] if len(pages) > 2 else pages
        
        preview = {
            "phase": self.phase_number,
            "title": "ネーム（コマ割り）",
            "page_previews": [
                {
                    "page": page["page_number"],
                    "panel_count": len(page["panels"]),
                    "layout_type": page.get("layout_type", "standard"),
                    "panels": [
                        {
                            "id": panel["panel_id"],
                            "size": panel["size"],
                            "camera": f"{panel.get('camera_angle', 'medium')}_{panel.get('camera_position', 'normal')}",
                            "composition": panel.get("composition", "rule_of_thirds")
                        }
                        for panel in page["panels"]
                    ]
                }
                for page in sample_pages
            ],
            "statistics": {
                "total_pages": output_data.get("total_pages", 0),
                "total_panels": output_data.get("total_panels", 0),
                "camera_variety": output_data.get("camera_statistics", {}).get("variety_score", 0),
                "reading_flow": output_data.get("reading_flow", {}).get("average_smoothness", 0)
            },
            "key_shots": [
                {
                    "shot_id": shot["shot_id"],
                    "description": shot["content"],
                    "camera": shot["camera"]["angle"]
                }
                for shot in output_data.get("shot_list", [])[:5]
            ]
        }
        
        return preview

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
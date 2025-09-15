"""Phase 4: Name Generation (Panel Layout and Composition) Agent."""

from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
import json
import math
import random

from app.agents.base.agent import BaseAgent
from app.core.config import settings
from app.services.vertex_ai_service import VertexAIService
from app.domain.manga.entities.phase_result import PhaseStatus

from .schemas import (
    NameGenerationInput, NameGenerationOutput, PageLayout,
    LayoutAnalysis, CameraStatistics, DramaticMoment,
    PanelTransition, ShotListItem, TransitionType,
    CameraAngleType, ImportanceLevel
)
from .validator import Phase4Validator
from .processors import NameGenerator

class Phase4NameAgent(BaseAgent):
    """Agent for name generation (panel layout, composition, camera work) - Critical phase."""

    def __init__(self):
        """Initialize Phase 4 Name Agent."""
        super().__init__(
            phase_number=4,
            phase_name="ネーム生成",
            timeout_seconds=settings.phase_timeouts[4]
        )

        # Initialize components
        self.processor = NameGenerator()
        self.validator = Phase4Validator()

        # Initialize AI service
        self.vertex_ai = VertexAIService()

        # Initialize prompts
        from app.agents.phases.phase4_name.prompts import PanelLayoutPrompts
        self.prompts = PanelLayoutPrompts()

    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: UUID,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process name generation - the most critical phase for manga creation.

        Args:
            input_data: Contains original text
            session_id: Current session ID
            previous_results: Results from phases 1-3

        Returns:
            Dict containing complete panel layout with camera work and composition
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

        # Fallback if phase3 data is empty
        if not page_allocation:
            self.log_warning("Phase 3 page_allocation is empty, creating fallback data")
            page_allocation = [{"page": 1, "scenes": [1]}]

        if not scenes:
            self.log_warning("Phase 3 scenes is empty, creating fallback data")
            scenes = [{"scene_number": 1, "content": "Default scene", "type": "dialogue"}]

        try:
            # Generate prompt for AI analysis
            prompt = await self.generate_prompt(input_data, previous_results)

            # Call Vertex AI for intelligent layout generation
            ai_response = await self.vertex_ai.generate_text(
                prompt=prompt,
                phase_number=self.phase_number
            )

            pages = None
            if ai_response.get("success", False):
                # Parse AI response
                ai_result = self._parse_ai_response(ai_response.get("content", ""))
                self.log_info(f"Vertex AI analysis successful",
                            tokens=ai_response.get("usage", {}).get("total_tokens", 0))

                # Use AI result if available
                if ai_result and ai_result.get("panel_layouts"):
                    pages = await self._process_ai_layouts(ai_result["panel_layouts"], scenes, genre)
                else:
                    self.log_warning("AI response lacks panel layout data, falling back to rule-based generation")
                    pages = self.processor.generate_panel_layouts(scenes, page_allocation, genre, pacing)
            else:
                # Fallback to rule-based generation
                self.log_warning(f"Vertex AI failed, using fallback: {ai_response.get('error', 'Unknown error')}")
                pages = self.processor.generate_panel_layouts(scenes, page_allocation, genre, pacing)

        except Exception as e:
            # Fallback to rule-based generation on error
            self.log_error(f"AI analysis failed, using fallback: {str(e)}")
            pages = self.processor.generate_panel_layouts(scenes, page_allocation, genre, pacing)

        # Enhance pages with additional processing
        enhanced_pages = await self._enhance_page_layouts(pages, scenes, genre, characters)

        # Final fallback if no pages were created
        if not enhanced_pages:
            self.log_warning("No pages were generated, creating minimal fallback page")
            from .schemas import PageLayout, Panel, PanelSize, PanelPosition, CameraSettings, ReadingFlow

            # Create a minimal page with one panel
            minimal_panel = Panel(
                panel_id=1,
                position=PanelPosition(x=0.0, y=0.0, z_index=0),
                size=PanelSize(width=1.0, height=1.0, aspect_ratio=(1, 1)),
                camera=CameraSettings(
                    angle="medium",
                    position="center",
                    focus="character"
                ),
                content="Fallback panel",
                dialogue=[],
                importance="medium"
            )

            minimal_page = PageLayout(
                page_number=1,
                panels=[minimal_panel],
                layout_pattern="standard",
                reading_flow=ReadingFlow(
                    primary_path=[(0.5, 0.5)],
                    secondary_paths=[],
                    focal_points=[]
                ),
                composition_guide={}
            )

            enhanced_pages = [minimal_page]

        # Generate comprehensive analysis
        layout_analysis = self._analyze_layout(enhanced_pages)
        camera_statistics = self._calculate_camera_statistics(enhanced_pages)
        shot_list = self._generate_shot_list(enhanced_pages, characters)
        dramatic_moments = self._identify_dramatic_moments(enhanced_pages)
        panel_transitions = self._analyze_transitions(enhanced_pages)

        # Create output
        output = NameGenerationOutput(
            pages=enhanced_pages,
            total_pages=len(enhanced_pages),
            total_panels=sum(len(page.panels) for page in enhanced_pages),
            shot_list=shot_list,
            layout_analysis=layout_analysis,
            camera_statistics=camera_statistics,
            composition_guide=self._create_composition_guide(enhanced_pages),
            reading_flow={f"page_{i+1}": page.reading_flow for i, page in enumerate(enhanced_pages)},
            dramatic_moments=dramatic_moments,
            panel_transitions=panel_transitions,
            quality_metrics=self._calculate_quality_metrics(enhanced_pages),
            recommendations=self._generate_recommendations(enhanced_pages, layout_analysis)
        )

        # Validate output
        is_valid, errors, quality_scores = self.validator.validate_output(output)

        if not is_valid:
            self.log_warning(f"Phase 4 validation failed: {errors}")

        # Log completion
        self.log_info(f"Phase 4 completed",
                     pages=len(enhanced_pages),
                     panels=output.total_panels,
                     quality=quality_scores.get("overall_quality", 0))

        # 辞書形式で結果を返す（IntegratedAIServiceとの互換性を確保）
        return {
            **output.dict(),  # メインの出力データ
            "status": "completed" if is_valid else "error",
            "error_message": "; ".join(errors) if errors else None,
            "quality_score": quality_scores.get("overall_quality", 0),
            "processing_time": 0,  # Will be set by parent
            "metadata": {
                "validation_errors": errors,
                "quality_breakdown": quality_scores,
                "ai_assisted": ai_response.get("success", False) if 'ai_response' in locals() else False
            }
        }

    async def generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate AI prompt for name generation."""
        return self.prompts.get_main_prompt(
            input_data=input_data,
            previous_results=previous_results
        )

    def _parse_ai_response(self, ai_content: str) -> Dict[str, Any]:
        """Parse AI JSON response into structured data."""
        try:
            # Find JSON in response
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

    def _create_validator(self):
        """Create Phase 4 specific validator."""
        return Phase4Validator()

    async def _generate_preview(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview data for Phase 4."""

        preview = {
            "phase_name": "ネーム生成",
            "summary": f"総パネル数: {output_data.get('total_panels', 0)}",
            "key_insights": [],
            "visual_elements": []
        }

        # Add key insights
        if output_data.get("total_panels"):
            preview["key_insights"].append(f"総パネル数: {output_data['total_panels']}")

        if output_data.get("total_pages"):
            preview["key_insights"].append(f"総ページ数: {output_data['total_pages']}")

        # Add layout analysis insights
        layout_analysis = output_data.get("layout_analysis", {})
        if layout_analysis.get("dominant_layout_type"):
            preview["key_insights"].append(f"主要レイアウト: {layout_analysis['dominant_layout_type']}")

        # Add visual elements
        camera_stats = output_data.get("camera_statistics", {})
        if camera_stats.get("dominant_angle_type"):
            preview["visual_elements"].append(f"主要カメラアングル: {camera_stats['dominant_angle_type']}")

        dramatic_moments = output_data.get("dramatic_moments", [])
        if dramatic_moments:
            preview["visual_elements"].append(f"ドラマティックシーン: {len(dramatic_moments)}箇所")

        return preview

    async def _generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate AI prompt for name generation."""
        return await self.generate_prompt(input_data, previous_results)

    async def _process_ai_response(
        self,
        ai_response: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process AI response into structured output."""
        return self._parse_ai_response(ai_response)

    async def _process_ai_layouts(
        self,
        ai_layouts: List[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
        genre: str
    ) -> List[PageLayout]:
        """Process AI-generated layouts into PageLayout objects."""
        pages = []

        for i, layout_data in enumerate(ai_layouts):
            try:
                # Convert AI layout to PageLayout
                page = await self._convert_ai_layout_to_page(layout_data, i + 1, scenes, genre)
                pages.append(page)
            except Exception as e:
                self.log_warning(f"Failed to process AI layout {i+1}: {e}")
                # Use fallback for this page
                fallback_page = self.processor._generate_single_page_layout(i + 1, scenes, {"panels_per_page": 4, "variation": 1}, genre)
                pages.append(fallback_page)

        return pages

    async def _convert_ai_layout_to_page(
        self,
        layout_data: Dict[str, Any],
        page_num: int,
        scenes: List[Dict[str, Any]],
        genre: str
    ) -> PageLayout:
        """Convert AI layout data to PageLayout object."""
        # This would involve parsing the AI response format
        # For now, use the processor as fallback
        return self.processor._generate_single_page_layout(
            page_num, scenes, {"panels_per_page": 4, "variation": 1}, genre
        )

    async def _enhance_page_layouts(
        self,
        pages: List[PageLayout],
        scenes: List[Dict[str, Any]],
        genre: str,
        characters: List[Dict[str, Any]]
    ) -> List[PageLayout]:
        """Enhance page layouts with additional processing."""
        enhanced_pages = []

        for page in pages:
            # Add visual flow calculations
            enhanced_flow = self._calculate_visual_flow(page)

            # Add dramatic effects
            enhanced_page = self._add_dramatic_effects(
                page,
                scenes,
                genre
            )

            enhanced_pages.append(enhanced_page)

        return enhanced_pages

    def _calculate_visual_flow(self, page: PageLayout) -> PageLayout:
        """Calculate and enhance visual flow for a page."""
        # Visual flow calculation logic
        # This would analyze panel positions and update reading flow
        return page

    def _add_dramatic_effects(
        self,
        page: PageLayout,
        scenes: List[Dict[str, Any]],
        genre: str
    ) -> PageLayout:
        """Add dramatic effects to page layout."""
        # Dramatic effects logic
        # This would modify panel properties for dramatic impact
        return page

    def _analyze_layout(self, pages: List[PageLayout]) -> LayoutAnalysis:
        """Analyze overall layout quality and characteristics."""
        if not pages:
            return LayoutAnalysis(
                total_panels=0,
                average_panels_per_page=0,
                layout_variety=0,
                composition_quality=0,
                visual_balance=0,
                pacing_effectiveness=0,
                readability_score=0,
                complexity_level="simple"
            )

        total_panels = sum(len(page.panels) for page in pages)
        avg_panels = total_panels / len(pages)

        # Calculate layout variety
        layout_types = [page.layout_type for page in pages]
        unique_layouts = len(set(layout_types))
        layout_variety = unique_layouts / len(layout_types) if layout_types else 0

        # Calculate composition quality
        composition_scores = []
        for page in pages:
            for panel in page.panels:
                # Simple composition quality based on rule compliance
                if panel.composition.rule:
                    composition_scores.append(panel.composition.balance_weight)

        composition_quality = sum(composition_scores) / len(composition_scores) if composition_scores else 0.5

        # Calculate visual balance
        visual_balance = self._calculate_overall_visual_balance(pages)

        # Calculate pacing effectiveness
        pacing_effectiveness = self._calculate_pacing_effectiveness(pages)

        # Calculate readability score
        readability_scores = [page.reading_flow.flow_quality for page in pages]
        readability_score = sum(readability_scores) / len(readability_scores) if readability_scores else 0.5

        # Determine complexity level
        complexity_level = self._determine_complexity_level(avg_panels, layout_variety)

        return LayoutAnalysis(
            total_panels=total_panels,
            average_panels_per_page=avg_panels,
            layout_variety=layout_variety,
            composition_quality=composition_quality,
            visual_balance=visual_balance,
            pacing_effectiveness=pacing_effectiveness,
            readability_score=readability_score,
            complexity_level=complexity_level
        )

    def _calculate_overall_visual_balance(self, pages: List[PageLayout]) -> float:
        """Calculate overall visual balance across all pages."""
        balance_scores = []

        for page in pages:
            # Calculate center of mass for page
            total_weight = 0
            weighted_x = 0
            weighted_y = 0

            for panel in page.panels:
                weight = panel.size.width * panel.size.height
                center_x = panel.position.x + panel.size.width / 2
                center_y = panel.position.y + panel.size.height / 2

                total_weight += weight
                weighted_x += center_x * weight
                weighted_y += center_y * weight

            if total_weight > 0:
                center_of_mass_x = weighted_x / total_weight
                center_of_mass_y = weighted_y / total_weight

                # Distance from ideal center
                distance = math.sqrt((center_of_mass_x - 0.5)**2 + (center_of_mass_y - 0.5)**2)
                balance_score = max(0, 1.0 - distance * 2)
                balance_scores.append(balance_score)

        return sum(balance_scores) / len(balance_scores) if balance_scores else 0.5

    def _calculate_pacing_effectiveness(self, pages: List[PageLayout]) -> float:
        """Calculate pacing effectiveness based on panel distribution."""
        if len(pages) < 2:
            return 1.0

        panel_counts = [len(page.panels) for page in pages]

        # Calculate variation in panel counts (good pacing has some variation)
        avg_panels = sum(panel_counts) / len(panel_counts)
        variance = sum((count - avg_panels)**2 for count in panel_counts) / len(panel_counts)

        # Normalize variance to effectiveness score
        # Some variation is good (0.5-1.5 range), too much is chaotic
        optimal_variance = 1.0
        effectiveness = max(0, 1.0 - abs(variance - optimal_variance) / 2)

        return effectiveness

    def _determine_complexity_level(self, avg_panels: float, layout_variety: float) -> str:
        """Determine overall complexity level."""
        complexity_score = avg_panels / 8 + layout_variety  # Normalize and combine

        if complexity_score >= 1.5:
            return "very_complex"
        elif complexity_score >= 1.0:
            return "complex"
        elif complexity_score >= 0.5:
            return "moderate"
        else:
            return "simple"

    def _calculate_camera_statistics(self, pages: List[PageLayout]) -> CameraStatistics:
        """Calculate camera usage statistics."""
        angle_counts = {}
        distance_counts = {}
        all_angles = []

        for page in pages:
            for panel in page.panels:
                camera = panel.camera_settings

                # Count angles
                angle = camera.angle
                angle_counts[angle] = angle_counts.get(angle, 0) + 1
                all_angles.append(angle)

                # Count distances
                distance = camera.distance
                distance_counts[distance] = distance_counts.get(distance, 0) + 1

        # Calculate variety score
        unique_angles = len(angle_counts)
        variety_score = unique_angles / len(CameraAngleType) if unique_angles > 0 else 0

        # Find dominant angle
        dominant_angle = max(angle_counts, key=angle_counts.get) if angle_counts else CameraAngleType.MEDIUM

        # Calculate cinematic quality (based on variety and interesting angles)
        interesting_angles = [CameraAngleType.BIRD_EYE, CameraAngleType.WORM_EYE, CameraAngleType.EXTREME_CLOSE]
        interesting_count = sum(angle_counts.get(angle, 0) for angle in interesting_angles)
        cinematic_quality = min(1.0, (variety_score + interesting_count / len(all_angles)) / 2) if all_angles else 0

        return CameraStatistics(
            angle_distribution=angle_counts,
            distance_distribution=distance_counts,
            variety_score=variety_score,
            dominant_angle=dominant_angle,
            cinematic_quality=cinematic_quality
        )

    def _generate_shot_list(
        self,
        pages: List[PageLayout],
        characters: List[Dict[str, Any]]
    ) -> List[ShotListItem]:
        """Generate detailed shot list."""
        shot_list = []
        shot_number = 1

        for page in pages:
            for panel in page.panels:
                shot_item = ShotListItem(
                    shot_number=shot_number,
                    panel_id=panel.panel_id,
                    shot_type=self._determine_shot_type(panel.camera_settings.angle),
                    camera_angle=panel.camera_settings.angle,
                    camera_movement=self._determine_camera_movement(panel),
                    subject=self._determine_main_subject(panel, characters),
                    background=self._determine_background(panel),
                    lighting=self._determine_lighting(panel),
                    mood=self._determine_mood(panel),
                    duration_weight=self._calculate_duration_weight(panel)
                )

                shot_list.append(shot_item)
                shot_number += 1

        return shot_list

    def _determine_shot_type(self, camera_angle: CameraAngleType) -> str:
        """Determine shot type from camera angle."""
        shot_types = {
            CameraAngleType.EXTREME_LONG: "Extreme Long Shot",
            CameraAngleType.LONG: "Long Shot",
            CameraAngleType.MEDIUM: "Medium Shot",
            CameraAngleType.CLOSE: "Close-Up",
            CameraAngleType.EXTREME_CLOSE: "Extreme Close-Up",
            CameraAngleType.BIRD_EYE: "Bird's Eye View",
            CameraAngleType.WORM_EYE: "Worm's Eye View"
        }
        return shot_types.get(camera_angle, "Medium Shot")

    def _determine_camera_movement(self, panel) -> Optional[str]:
        """Determine camera movement for panel."""
        if abs(panel.camera_settings.tilt) > 10:
            return f"Tilt {panel.camera_settings.tilt:.1f}°"
        return None

    def _determine_main_subject(self, panel, characters: List[Dict[str, Any]]) -> str:
        """Determine main subject of panel."""
        if characters:
            # Simple logic: use first character as default
            return characters[0].get("name", "Character")
        return "Scene"

    def _determine_background(self, panel) -> str:
        """Determine background description."""
        # This would be more sophisticated in practice
        return "Standard background"

    def _determine_lighting(self, panel) -> str:
        """Determine lighting conditions."""
        return "Natural lighting"

    def _determine_mood(self, panel) -> str:
        """Determine mood of panel."""
        # Could be derived from composition or content
        return "neutral"

    def _calculate_duration_weight(self, panel) -> float:
        """Calculate relative duration weight for panel."""
        # Important panels should have higher duration weight
        importance_weights = {
            ImportanceLevel.CRITICAL: 2.0,
            ImportanceLevel.HIGH: 1.5,
            ImportanceLevel.MEDIUM: 1.0,
            ImportanceLevel.LOW: 0.5
        }
        return importance_weights.get(panel.importance, 1.0)

    def _identify_dramatic_moments(self, pages: List[PageLayout]) -> List[DramaticMoment]:
        """Identify dramatic moments in the layout."""
        dramatic_moments = []

        for page in pages:
            for panel in page.panels:
                if panel.importance in [ImportanceLevel.HIGH, ImportanceLevel.CRITICAL]:
                    # This panel represents a dramatic moment
                    buildup_panels = self._find_buildup_panels(page, panel)

                    dramatic_moment = DramaticMoment(
                        page_number=page.page_number,
                        panel_id=panel.panel_id,
                        moment_type=self._classify_dramatic_moment(panel),
                        intensity=self._calculate_dramatic_intensity(panel),
                        buildup_panels=buildup_panels,
                        impact_factor=self._calculate_impact_factor(panel)
                    )

                    dramatic_moments.append(dramatic_moment)

        return dramatic_moments

    def _find_buildup_panels(self, page: PageLayout, target_panel) -> List[str]:
        """Find panels that build up to a dramatic moment."""
        reading_order = page.reading_flow.reading_order
        target_index = reading_order.index(target_panel.panel_id) if target_panel.panel_id in reading_order else -1

        if target_index > 0:
            # Return previous 1-2 panels as buildup
            start_index = max(0, target_index - 2)
            return reading_order[start_index:target_index]

        return []

    def _classify_dramatic_moment(self, panel) -> str:
        """Classify the type of dramatic moment."""
        if panel.camera_settings.angle == CameraAngleType.EXTREME_CLOSE:
            return "emotional_revelation"
        elif panel.camera_settings.angle in [CameraAngleType.BIRD_EYE, CameraAngleType.WORM_EYE]:
            return "dramatic_perspective"
        else:
            return "climactic_action"

    def _calculate_dramatic_intensity(self, panel) -> float:
        """Calculate intensity of dramatic moment."""
        intensity_factors = []

        # Camera angle contribution
        angle_intensity = {
            CameraAngleType.EXTREME_CLOSE: 0.9,
            CameraAngleType.CLOSE: 0.7,
            CameraAngleType.BIRD_EYE: 0.8,
            CameraAngleType.WORM_EYE: 0.8,
            CameraAngleType.MEDIUM: 0.5,
            CameraAngleType.LONG: 0.3,
            CameraAngleType.EXTREME_LONG: 0.2
        }
        intensity_factors.append(angle_intensity.get(panel.camera_settings.angle, 0.5))

        # Panel importance contribution
        importance_intensity = {
            ImportanceLevel.CRITICAL: 1.0,
            ImportanceLevel.HIGH: 0.8,
            ImportanceLevel.MEDIUM: 0.5,
            ImportanceLevel.LOW: 0.2
        }
        intensity_factors.append(importance_intensity.get(panel.importance, 0.5))

        return sum(intensity_factors) / len(intensity_factors)

    def _calculate_impact_factor(self, panel) -> float:
        """Calculate visual impact factor."""
        # Panel size contributes to impact
        size_factor = panel.size.width * panel.size.height

        # Camera distance affects impact (closer = more impact)
        distance_factor = (6 - panel.camera_settings.distance) / 5  # Normalize to 0-1

        return (size_factor + distance_factor) / 2

    def _analyze_transitions(self, pages: List[PageLayout]) -> List[PanelTransition]:
        """Analyze transitions between panels."""
        transitions = []

        for page in pages:
            reading_order = page.reading_flow.reading_order

            for i in range(len(reading_order) - 1):
                current_panel_id = reading_order[i]
                next_panel_id = reading_order[i + 1]

                # Find panel objects
                current_panel = next((p for p in page.panels if p.panel_id == current_panel_id), None)
                next_panel = next((p for p in page.panels if p.panel_id == next_panel_id), None)

                if current_panel and next_panel:
                    transition = PanelTransition(
                        from_panel=current_panel_id,
                        to_panel=next_panel_id,
                        transition_type=self._classify_transition(current_panel, next_panel),
                        time_gap=self._estimate_time_gap(current_panel, next_panel),
                        spatial_relationship=self._describe_spatial_relationship(current_panel, next_panel),
                        transition_quality=self._assess_transition_quality(current_panel, next_panel)
                    )

                    transitions.append(transition)

        return transitions

    def _classify_transition(self, panel1, panel2) -> TransitionType:
        """Classify the type of transition between panels."""
        # Simple classification based on scene references
        if panel1.scene_reference == panel2.scene_reference:
            if panel1.camera_settings.angle == panel2.camera_settings.angle:
                return TransitionType.MOMENT_TO_MOMENT
            else:
                return TransitionType.ACTION_TO_ACTION
        else:
            return TransitionType.SCENE_TO_SCENE

    def _estimate_time_gap(self, panel1, panel2) -> float:
        """Estimate time gap between panels."""
        # Simple estimation based on transition type
        transition_type = self._classify_transition(panel1, panel2)

        time_gaps = {
            TransitionType.MOMENT_TO_MOMENT: 0.0,
            TransitionType.ACTION_TO_ACTION: 1.0,
            TransitionType.SUBJECT_TO_SUBJECT: 0.5,
            TransitionType.SCENE_TO_SCENE: 5.0,
            TransitionType.ASPECT_TO_ASPECT: 0.0,
            TransitionType.NON_SEQUITUR: 10.0
        }

        return time_gaps.get(transition_type, 2.0)

    def _describe_spatial_relationship(self, panel1, panel2) -> str:
        """Describe spatial relationship between panels."""
        dx = panel2.position.x - panel1.position.x
        dy = panel2.position.y - panel1.position.y

        if abs(dx) > abs(dy):
            return "horizontal_flow" if dx > 0 else "reverse_horizontal"
        else:
            return "vertical_flow" if dy > 0 else "reverse_vertical"

    def _assess_transition_quality(self, panel1, panel2) -> float:
        """Assess quality of transition between panels."""
        quality_factors = []

        # Spatial flow quality
        dx = panel2.position.x - panel1.position.x
        dy = panel2.position.y - panel1.position.y

        if dx > 0 or (dx == 0 and dy > 0):  # Natural reading flow
            quality_factors.append(1.0)
        else:
            quality_factors.append(0.3)

        # Camera angle transition quality
        angle_change = abs(panel1.camera_settings.distance - panel2.camera_settings.distance)
        if angle_change <= 1:  # Smooth camera transition
            quality_factors.append(0.8)
        elif angle_change <= 2:
            quality_factors.append(0.6)
        else:
            quality_factors.append(0.4)

        return sum(quality_factors) / len(quality_factors)

    def _create_composition_guide(self, pages: List[PageLayout]) -> Dict[str, Any]:
        """Create comprehensive composition guide."""
        return {
            "general_principles": [
                "Maintain visual balance across pages",
                "Use variety in panel sizes and shapes",
                "Consider reading flow in panel arrangement",
                "Apply rule of thirds for focal points"
            ],
            "camera_usage": [
                "Vary camera angles for dynamic storytelling",
                "Use close-ups for emotional moments",
                "Use wide shots for establishing scenes",
                "Balance dramatic angles with standard shots"
            ],
            "layout_tips": [
                "Start with simple layouts and add complexity",
                "Use panel borders to convey emotion",
                "Consider white space for pacing",
                "Group related panels visually"
            ]
        }

    def _calculate_quality_metrics(self, pages: List[PageLayout]) -> Dict[str, float]:
        """Calculate detailed quality metrics."""
        if not pages:
            return {}

        # Layout consistency
        panel_counts = [len(page.panels) for page in pages]
        consistency = 1.0 - (max(panel_counts) - min(panel_counts)) / (max(panel_counts) if panel_counts else 1)

        # Camera variety
        all_angles = [panel.camera_settings.angle for page in pages for panel in page.panels]
        unique_angles = len(set(all_angles))
        camera_variety = unique_angles / len(CameraAngleType)

        # Reading flow quality
        flow_scores = [page.reading_flow.flow_quality for page in pages]
        avg_flow = sum(flow_scores) / len(flow_scores)

        return {
            "layout_consistency": consistency,
            "camera_variety": camera_variety,
            "reading_flow": avg_flow,
            "overall_complexity": len(pages) * sum(panel_counts) / (len(pages) * 6)  # Normalized to 6-panel average
        }

    def _generate_recommendations(
        self,
        pages: List[PageLayout],
        analysis: LayoutAnalysis
    ) -> List[str]:
        """Generate improvement recommendations."""
        recommendations = []

        if analysis.layout_variety < 0.5:
            recommendations.append("Consider adding more variety to panel layouts")

        if analysis.composition_quality < 0.6:
            recommendations.append("Apply composition rules more consistently")

        if analysis.readability_score < 0.7:
            recommendations.append("Improve panel arrangement for better reading flow")

        if analysis.visual_balance < 0.5:
            recommendations.append("Balance panel distribution across pages")

        # Camera-specific recommendations
        camera_stats = self._calculate_camera_statistics(pages)
        if camera_stats.variety_score < 0.4:
            recommendations.append("Increase camera angle variety for more dynamic storytelling")

        return recommendations
"""Phase 7 Page Compilation Module."""

from typing import Dict, Any, List, Optional
import asyncio
from dataclasses import dataclass

from app.core.logging import LoggerMixin


@dataclass
class CompiledPage:
    """Compiled page data structure."""
    page_number: int
    panels: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    dialogues: List[Dict[str, Any]]
    layout_info: Dict[str, Any]
    completion_score: float


class PageCompilerModule(LoggerMixin):
    """Module for compiling and optimizing manga pages."""

    def __init__(self):
        """Initialize page compiler module."""
        self.logger.info("Page Compiler Module initialized")

    async def compile_manga_pages(
        self,
        phase_results: Dict[int, Any]
    ) -> Dict[str, Any]:
        """Compile final manga pages from all phase results."""

        self.logger.info("Starting manga page compilation")

        # Extract data from different phases
        pages_data = phase_results.get(4, {}).get("pages", [])
        images_data = phase_results.get(5, {}).get("generated_images", [])
        dialogue_data = phase_results.get(6, {}).get("dialogue_placement", [])

        compiled_pages = []

        for page_data in pages_data:
            compiled_page = await self._compile_single_page(
                page_data, images_data, dialogue_data
            )
            compiled_pages.append(compiled_page)

        # Optimize layouts
        optimized_pages = await self._optimize_layouts(compiled_pages)

        # Validate reading experience
        reading_validation = await self._validate_reading_experience(optimized_pages)

        return {
            "compiled_pages": [
                {
                    "page_number": page.page_number,
                    "panels": page.panels,
                    "images": page.images,
                    "dialogues": page.dialogues,
                    "layout_info": page.layout_info,
                    "completion_score": page.completion_score
                }
                for page in optimized_pages
            ],
            "total_pages": len(optimized_pages),
            "average_completion_score": sum(p.completion_score for p in optimized_pages) / len(optimized_pages),
            "reading_validation": reading_validation,
            "compilation_metadata": {
                "total_panels": sum(len(p.panels) for p in optimized_pages),
                "total_images": sum(len(p.images) for p in optimized_pages),
                "total_dialogues": sum(len(p.dialogues) for p in optimized_pages)
            }
        }

    async def _compile_single_page(
        self,
        page_data: Dict[str, Any],
        images_data: List[Dict[str, Any]],
        dialogue_data: List[Dict[str, Any]]
    ) -> CompiledPage:
        """Compile a single page with all its components."""

        page_number = page_data.get("page_number", 1)
        panels = page_data.get("panels", [])

        # Match images to panels
        page_images = []
        for panel in panels:
            panel_id = panel.get("panel_id")
            matching_images = [
                img for img in images_data
                if img.get("panel_id") == panel_id
            ]
            page_images.extend(matching_images)

        # Match dialogues to panels
        page_dialogues = []
        for panel in panels:
            panel_id = panel.get("panel_id")
            matching_dialogues = [
                dlg for dlg in dialogue_data
                if dlg.get("panel_id") == panel_id
            ]
            page_dialogues.extend(matching_dialogues)

        # Assess page completion
        completion_score = await self._assess_page_completion(
            panels, page_images, page_dialogues
        )

        # Generate layout info
        layout_info = self._generate_layout_info(page_data, panels)

        return CompiledPage(
            page_number=page_number,
            panels=panels,
            images=page_images,
            dialogues=page_dialogues,
            layout_info=layout_info,
            completion_score=completion_score
        )

    async def _assess_page_completion(
        self,
        panels: List[Dict[str, Any]],
        images: List[Dict[str, Any]],
        dialogues: List[Dict[str, Any]]
    ) -> float:
        """Assess completion level of a page."""

        total_panels = len(panels)
        if total_panels == 0:
            return 0.0

        # Check image completion
        panels_with_images = len(set(img.get("panel_id") for img in images))
        image_completion = panels_with_images / total_panels

        # Check dialogue completion (not all panels need dialogue)
        panels_with_dialogue = len(set(dlg.get("panel_id") for dlg in dialogues))
        dialogue_completion = min(panels_with_dialogue / max(total_panels * 0.7, 1), 1.0)

        # Check panel layout completion
        complete_panels = sum(
            1 for panel in panels
            if all(key in panel for key in ["panel_id", "position", "size"])
        )
        layout_completion = complete_panels / total_panels

        # Weighted average
        completion_score = (
            image_completion * 0.4 +
            dialogue_completion * 0.3 +
            layout_completion * 0.3
        )

        return completion_score

    def _generate_layout_info(
        self,
        page_data: Dict[str, Any],
        panels: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate layout information for the page."""

        return {
            "page_dimensions": page_data.get("dimensions", {"width": 1200, "height": 1600}),
            "panel_count": len(panels),
            "layout_type": page_data.get("layout_type", "standard"),
            "reading_direction": page_data.get("reading_direction", "right_to_left"),
            "gutters": page_data.get("gutters", {"horizontal": 10, "vertical": 10}),
            "margins": page_data.get("margins", {"top": 20, "bottom": 20, "left": 20, "right": 20})
        }

    async def _optimize_layouts(
        self,
        compiled_pages: List[CompiledPage]
    ) -> List[CompiledPage]:
        """Optimize page layouts for better readability."""

        optimized_pages = []

        for page in compiled_pages:
            # Optimize page readability
            readability_optimized = await self._optimize_page_readability(page)

            # Optimize visual consistency
            visual_optimized = await self._optimize_visual_consistency(readability_optimized)

            # Optimize pacing flow
            pacing_optimized = await self._optimize_pacing_flow(visual_optimized)

            optimized_pages.append(pacing_optimized)

        return optimized_pages

    async def _optimize_page_readability(self, page: CompiledPage) -> CompiledPage:
        """Optimize page for better readability."""

        # Analyze text density and adjust if needed
        optimized_dialogues = []
        for dialogue in page.dialogues:
            # Simplified optimization - adjust font size based on text length
            text_length = len(dialogue.get("text", ""))
            if text_length > 50:
                dialogue["font_size"] = max(dialogue.get("font_size", 12) - 1, 10)
            optimized_dialogues.append(dialogue)

        return CompiledPage(
            page_number=page.page_number,
            panels=page.panels,
            images=page.images,
            dialogues=optimized_dialogues,
            layout_info=page.layout_info,
            completion_score=page.completion_score
        )

    async def _optimize_visual_consistency(self, page: CompiledPage) -> CompiledPage:
        """Optimize visual consistency across the page."""

        # Analyze color consistency and adjust if needed
        optimized_images = []
        for image in page.images:
            # Simplified optimization - ensure consistent style parameters
            if "style_parameters" not in image:
                image["style_parameters"] = {
                    "color_palette": "consistent",
                    "art_style": "manga",
                    "line_style": "clean"
                }
            optimized_images.append(image)

        return CompiledPage(
            page_number=page.page_number,
            panels=page.panels,
            images=optimized_images,
            dialogues=page.dialogues,
            layout_info=page.layout_info,
            completion_score=page.completion_score
        )

    async def _optimize_pacing_flow(self, page: CompiledPage) -> CompiledPage:
        """Optimize pacing and flow for the page."""

        # Adjust panel sizes based on content importance
        optimized_panels = []
        for panel in page.panels:
            # Simplified optimization - adjust panel prominence
            emotional_weight = panel.get("emotional_weight", 0.5)
            if emotional_weight > 0.8:
                # Increase size for high-impact panels
                panel["size_multiplier"] = panel.get("size_multiplier", 1.0) * 1.2
            optimized_panels.append(panel)

        return CompiledPage(
            page_number=page.page_number,
            panels=optimized_panels,
            images=page.images,
            dialogues=page.dialogues,
            layout_info=page.layout_info,
            completion_score=page.completion_score
        )

    async def _validate_reading_experience(
        self,
        compiled_pages: List[CompiledPage]
    ) -> Dict[str, Any]:
        """Validate overall reading experience."""

        # Analyze page flow
        page_flow_analysis = await self._analyze_page_flow(compiled_pages)

        # Check story completeness
        story_completeness = await self._check_story_completeness(compiled_pages)

        # Assess reader engagement
        engagement_assessment = await self._assess_reader_engagement(compiled_pages)

        return {
            "page_flow_analysis": page_flow_analysis,
            "story_completeness": story_completeness,
            "engagement_assessment": engagement_assessment,
            "overall_reading_score": self._calculate_reading_score(
                page_flow_analysis, story_completeness, engagement_assessment
            )
        }

    async def _analyze_page_flow(self, compiled_pages: List[CompiledPage]) -> Dict[str, Any]:
        """Analyze flow between pages."""

        if len(compiled_pages) < 2:
            return {"flow_quality": 0.5, "transition_issues": []}

        transition_scores = []
        issues = []

        for i in range(len(compiled_pages) - 1):
            current_page = compiled_pages[i]
            next_page = compiled_pages[i + 1]

            # Analyze transition quality (simplified)
            transition_score = self._calculate_page_transition_quality(current_page, next_page)
            transition_scores.append(transition_score)

            if transition_score < 0.6:
                issues.append({
                    "page_transition": f"{current_page.page_number} -> {next_page.page_number}",
                    "score": transition_score,
                    "issue": "Poor page flow transition"
                })

        return {
            "flow_quality": sum(transition_scores) / len(transition_scores) if transition_scores else 0.5,
            "transition_issues": issues,
            "total_transitions": len(transition_scores)
        }

    def _calculate_page_transition_quality(
        self,
        current_page: CompiledPage,
        next_page: CompiledPage
    ) -> float:
        """Calculate quality of transition between pages."""

        # Simplified calculation based on completion scores
        avg_completion = (current_page.completion_score + next_page.completion_score) / 2

        # Check for visual consistency
        visual_consistency = 0.8  # Simplified

        # Check for narrative flow
        narrative_flow = 0.7  # Simplified

        return (avg_completion + visual_consistency + narrative_flow) / 3

    async def _check_story_completeness(self, compiled_pages: List[CompiledPage]) -> Dict[str, Any]:
        """Check story completeness across pages."""

        total_panels = sum(len(page.panels) for page in compiled_pages)
        total_dialogues = sum(len(page.dialogues) for page in compiled_pages)
        total_images = sum(len(page.images) for page in compiled_pages)

        # Calculate completeness ratios
        dialogue_coverage = min(total_dialogues / max(total_panels * 0.7, 1), 1.0)
        image_coverage = total_images / max(total_panels, 1)

        completeness_score = (dialogue_coverage + image_coverage) / 2

        return {
            "completeness_score": completeness_score,
            "total_panels": total_panels,
            "dialogue_coverage": dialogue_coverage,
            "image_coverage": image_coverage,
            "story_complete": completeness_score >= 0.8
        }

    async def _assess_reader_engagement(self, compiled_pages: List[CompiledPage]) -> Dict[str, Any]:
        """Assess potential reader engagement."""

        # Calculate visual variety
        visual_variety = self._calculate_visual_variety(compiled_pages)

        # Calculate pacing variety
        pacing_variety = self._calculate_pacing_variety(compiled_pages)

        # Calculate character presence
        character_presence = self._calculate_character_presence(compiled_pages)

        engagement_score = (visual_variety + pacing_variety + character_presence) / 3

        return {
            "engagement_score": engagement_score,
            "visual_variety": visual_variety,
            "pacing_variety": pacing_variety,
            "character_presence": character_presence,
            "engagement_level": self._classify_engagement_level(engagement_score)
        }

    def _calculate_visual_variety(self, compiled_pages: List[CompiledPage]) -> float:
        """Calculate visual variety across pages."""
        # Simplified calculation
        if not compiled_pages:
            return 0.5

        # Check for variety in panel counts
        panel_counts = [len(page.panels) for page in compiled_pages]
        panel_variety = len(set(panel_counts)) / len(compiled_pages)

        return min(panel_variety * 2, 1.0)

    def _calculate_pacing_variety(self, compiled_pages: List[CompiledPage]) -> float:
        """Calculate pacing variety across pages."""
        # Simplified calculation based on completion scores
        if not compiled_pages:
            return 0.5

        completion_scores = [page.completion_score for page in compiled_pages]
        avg_score = sum(completion_scores) / len(completion_scores)

        # Higher average completion = better pacing
        return min(avg_score * 1.2, 1.0)

    def _calculate_character_presence(self, compiled_pages: List[CompiledPage]) -> float:
        """Calculate character presence across pages."""
        if not compiled_pages:
            return 0.5

        # Check for consistent character dialogue presence
        pages_with_dialogue = sum(1 for page in compiled_pages if page.dialogues)
        dialogue_presence = pages_with_dialogue / len(compiled_pages)

        return dialogue_presence

    def _classify_engagement_level(self, engagement_score: float) -> str:
        """Classify engagement level based on score."""
        if engagement_score >= 0.8:
            return "高い"
        elif engagement_score >= 0.6:
            return "中程度"
        elif engagement_score >= 0.4:
            return "低い"
        else:
            return "要改善"

    def _calculate_reading_score(
        self,
        page_flow: Dict[str, Any],
        story_completeness: Dict[str, Any],
        engagement: Dict[str, Any]
    ) -> float:
        """Calculate overall reading experience score."""

        flow_score = page_flow.get("flow_quality", 0.5)
        completeness_score = story_completeness.get("completeness_score", 0.5)
        engagement_score = engagement.get("engagement_score", 0.5)

        # Weighted average
        reading_score = (
            flow_score * 0.3 +
            completeness_score * 0.4 +
            engagement_score * 0.3
        )

        return reading_score
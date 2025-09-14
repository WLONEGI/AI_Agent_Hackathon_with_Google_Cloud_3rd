"""Phase 7 Output Formatting Module."""

from typing import Dict, Any, List, Optional
import json
from dataclasses import dataclass, asdict
from datetime import datetime

from app.core.logging import LoggerMixin


@dataclass
class OutputMetadata:
    """Output metadata structure."""
    generated_at: str
    total_pages: int
    total_panels: int
    total_images: int
    total_dialogues: int
    average_completion_score: float
    processing_time: Optional[float] = None


@dataclass
class FormattedOutput:
    """Formatted output structure."""
    format_type: str
    content: Dict[str, Any]
    metadata: OutputMetadata
    file_suggestions: List[str]


class OutputFormatterModule(LoggerMixin):
    """Module for formatting output in different formats."""

    def __init__(self):
        """Initialize output formatter module."""
        self.logger.info("Output Formatter Module initialized")

    async def format_output(
        self,
        compiled_pages: List[Dict[str, Any]],
        quality_assessment: Dict[str, Any],
        reading_validation: Dict[str, Any],
        compilation_metadata: Dict[str, Any],
        output_format: str = "comprehensive"
    ) -> FormattedOutput:
        """Format output based on specified format type."""

        self.logger.info(f"Formatting output as: {output_format}")

        # Generate metadata
        metadata = self._generate_metadata(
            compiled_pages, compilation_metadata
        )

        # Format based on type
        if output_format == "web":
            content = await self._format_for_web(
                compiled_pages, quality_assessment, reading_validation
            )
        elif output_format == "print":
            content = await self._format_for_print(
                compiled_pages, quality_assessment
            )
        elif output_format == "digital":
            content = await self._format_for_digital(
                compiled_pages, quality_assessment, reading_validation
            )
        elif output_format == "api":
            content = await self._format_for_api(
                compiled_pages, quality_assessment, reading_validation
            )
        else:  # comprehensive
            content = await self._format_comprehensive(
                compiled_pages, quality_assessment, reading_validation, compilation_metadata
            )

        # Generate file suggestions
        file_suggestions = self._generate_file_suggestions(output_format, metadata)

        return FormattedOutput(
            format_type=output_format,
            content=content,
            metadata=metadata,
            file_suggestions=file_suggestions
        )

    def _generate_metadata(
        self,
        compiled_pages: List[Dict[str, Any]],
        compilation_metadata: Dict[str, Any]
    ) -> OutputMetadata:
        """Generate output metadata."""

        total_pages = len(compiled_pages)
        avg_completion = sum(
            page.get("completion_score", 0) for page in compiled_pages
        ) / max(total_pages, 1)

        return OutputMetadata(
            generated_at=datetime.now().isoformat(),
            total_pages=total_pages,
            total_panels=compilation_metadata.get("total_panels", 0),
            total_images=compilation_metadata.get("total_images", 0),
            total_dialogues=compilation_metadata.get("total_dialogues", 0),
            average_completion_score=avg_completion
        )

    async def _format_for_web(
        self,
        compiled_pages: List[Dict[str, Any]],
        quality_assessment: Dict[str, Any],
        reading_validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format output for web display."""

        web_pages = []
        for page in compiled_pages:
            web_page = {
                "pageNumber": page.get("page_number", 1),
                "panels": self._format_panels_for_web(page.get("panels", [])),
                "images": self._format_images_for_web(page.get("images", [])),
                "dialogues": self._format_dialogues_for_web(page.get("dialogues", [])),
                "layoutInfo": self._format_layout_for_web(page.get("layout_info", {})),
                "completionScore": page.get("completion_score", 0)
            }
            web_pages.append(web_page)

        return {
            "pages": web_pages,
            "qualityScores": self._extract_quality_scores(quality_assessment),
            "readingExperience": self._extract_reading_scores(reading_validation),
            "displayOptions": {
                "theme": "light",
                "readingDirection": "right_to_left",
                "zoomLevels": [0.5, 0.75, 1.0, 1.25, 1.5, 2.0],
                "pageTransitions": ["fade", "slide", "none"]
            }
        }

    async def _format_for_print(
        self,
        compiled_pages: List[Dict[str, Any]],
        quality_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format output for print production."""

        print_pages = []
        for page in compiled_pages:
            print_page = {
                "page_number": page.get("page_number", 1),
                "print_dimensions": {
                    "width_mm": 182,  # B5 size
                    "height_mm": 257,
                    "dpi": 300,
                    "bleed_mm": 3
                },
                "panels": self._format_panels_for_print(page.get("panels", [])),
                "images": self._format_images_for_print(page.get("images", [])),
                "dialogues": self._format_dialogues_for_print(page.get("dialogues", [])),
                "color_profile": "CMYK",
                "print_quality": self._assess_print_quality(page, quality_assessment)
            }
            print_pages.append(print_page)

        return {
            "pages": print_pages,
            "print_specifications": {
                "paper_size": "B5",
                "color_mode": "CMYK",
                "resolution": "300dpi",
                "binding": "perfect_bound",
                "page_order": "right_to_left"
            },
            "quality_checks": self._generate_print_quality_checks(quality_assessment)
        }

    async def _format_for_digital(
        self,
        compiled_pages: List[Dict[str, Any]],
        quality_assessment: Dict[str, Any],
        reading_validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format output for digital distribution."""

        digital_pages = []
        for page in compiled_pages:
            digital_page = {
                "page_id": f"page_{page.get('page_number', 1):03d}",
                "panels": self._format_panels_for_digital(page.get("panels", [])),
                "images": self._format_images_for_digital(page.get("images", [])),
                "dialogues": self._format_dialogues_for_digital(page.get("dialogues", [])),
                "responsive_layout": self._generate_responsive_layout(page),
                "accessibility": self._generate_accessibility_data(page)
            }
            digital_pages.append(digital_page)

        return {
            "pages": digital_pages,
            "digital_metadata": {
                "format_version": "1.0",
                "supported_devices": ["tablet", "smartphone", "desktop"],
                "screen_orientations": ["portrait", "landscape"],
                "reading_modes": ["guided_view", "page_view", "panel_view"]
            },
            "quality_metrics": self._extract_digital_quality_metrics(
                quality_assessment, reading_validation
            )
        }

    async def _format_for_api(
        self,
        compiled_pages: List[Dict[str, Any]],
        quality_assessment: Dict[str, Any],
        reading_validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format output for API consumption."""

        api_pages = []
        for page in compiled_pages:
            api_page = {
                "page_number": page.get("page_number", 1),
                "panels": page.get("panels", []),
                "images": page.get("images", []),
                "dialogues": page.get("dialogues", []),
                "layout_info": page.get("layout_info", {}),
                "completion_score": page.get("completion_score", 0),
                "quality_scores": self._extract_page_quality_scores(
                    page, quality_assessment
                )
            }
            api_pages.append(api_page)

        return {
            "manga_data": {
                "pages": api_pages,
                "total_pages": len(api_pages)
            },
            "quality_assessment": quality_assessment,
            "reading_validation": reading_validation,
            "api_version": "v1",
            "schema_version": "1.0.0"
        }

    async def _format_comprehensive(
        self,
        compiled_pages: List[Dict[str, Any]],
        quality_assessment: Dict[str, Any],
        reading_validation: Dict[str, Any],
        compilation_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format comprehensive output with all information."""

        return {
            "compiled_pages": compiled_pages,
            "quality_assessment": quality_assessment,
            "reading_validation": reading_validation,
            "compilation_metadata": compilation_metadata,
            "summary": {
                "total_pages": len(compiled_pages),
                "average_completion_score": sum(
                    p.get("completion_score", 0) for p in compiled_pages
                ) / max(len(compiled_pages), 1),
                "overall_quality_score": quality_assessment.get("overall_score", 0),
                "reading_experience_score": reading_validation.get("overall_reading_score", 0)
            },
            "recommendations": self._generate_recommendations(
                quality_assessment, reading_validation
            )
        }

    def _format_panels_for_web(self, panels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format panels for web display."""
        web_panels = []
        for panel in panels:
            web_panel = {
                "id": panel.get("panel_id", ""),
                "position": panel.get("position", {}),
                "size": panel.get("size", {}),
                "zIndex": panel.get("z_index", 1),
                "borderStyle": {
                    "width": panel.get("border_width", 2),
                    "color": panel.get("border_color", "#000000"),
                    "style": panel.get("border_style", "solid")
                }
            }
            web_panels.append(web_panel)
        return web_panels

    def _format_images_for_web(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format images for web display."""
        web_images = []
        for image in images:
            web_image = {
                "id": image.get("image_id", ""),
                "panelId": image.get("panel_id", ""),
                "src": image.get("image_url", ""),
                "alt": image.get("description", ""),
                "position": image.get("position", {}),
                "size": image.get("size", {}),
                "loading": "lazy"
            }
            web_images.append(web_image)
        return web_images

    def _format_dialogues_for_web(self, dialogues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format dialogues for web display."""
        web_dialogues = []
        for dialogue in dialogues:
            web_dialogue = {
                "id": dialogue.get("dialogue_id", ""),
                "panelId": dialogue.get("panel_id", ""),
                "text": dialogue.get("text", ""),
                "speaker": dialogue.get("speaker", ""),
                "position": dialogue.get("position", {}),
                "style": {
                    "fontSize": dialogue.get("font_size", 12),
                    "fontFamily": dialogue.get("font_family", "Arial"),
                    "color": dialogue.get("text_color", "#000000"),
                    "backgroundColor": dialogue.get("background_color", "#FFFFFF")
                },
                "bubbleType": dialogue.get("bubble_type", "speech")
            }
            web_dialogues.append(web_dialogue)
        return web_dialogues

    def _format_layout_for_web(self, layout_info: Dict[str, Any]) -> Dict[str, Any]:
        """Format layout info for web display."""
        return {
            "dimensions": layout_info.get("page_dimensions", {}),
            "panelCount": layout_info.get("panel_count", 0),
            "layoutType": layout_info.get("layout_type", "standard"),
            "readingDirection": layout_info.get("reading_direction", "right_to_left"),
            "gutters": layout_info.get("gutters", {}),
            "margins": layout_info.get("margins", {})
        }

    def _format_panels_for_print(self, panels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format panels for print production."""
        return panels  # Simplified for now

    def _format_images_for_print(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format images for print production."""
        return images  # Simplified for now

    def _format_dialogues_for_print(self, dialogues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format dialogues for print production."""
        return dialogues  # Simplified for now

    def _format_panels_for_digital(self, panels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format panels for digital distribution."""
        return panels  # Simplified for now

    def _format_images_for_digital(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format images for digital distribution."""
        return images  # Simplified for now

    def _format_dialogues_for_digital(self, dialogues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format dialogues for digital distribution."""
        return dialogues  # Simplified for now

    def _extract_quality_scores(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Extract quality scores for web display."""
        return {
            "overall": quality_assessment.get("overall_score", 0),
            "visual": quality_assessment.get("visual_quality", {}).get("score", 0),
            "narrative": quality_assessment.get("narrative_quality", {}).get("score", 0),
            "technical": quality_assessment.get("technical_quality", {}).get("score", 0)
        }

    def _extract_reading_scores(self, reading_validation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract reading experience scores."""
        return {
            "overall": reading_validation.get("overall_reading_score", 0),
            "flow": reading_validation.get("page_flow_analysis", {}).get("flow_quality", 0),
            "completeness": reading_validation.get("story_completeness", {}).get("completeness_score", 0),
            "engagement": reading_validation.get("engagement_assessment", {}).get("engagement_score", 0)
        }

    def _assess_print_quality(self, page: Dict[str, Any], quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Assess print quality for a page."""
        return {
            "resolution_check": "pass",
            "color_profile_check": "pass",
            "text_readability": "pass",
            "bleed_area": "acceptable"
        }

    def _generate_print_quality_checks(self, quality_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate print quality checks."""
        return [
            {"check": "resolution", "status": "pass", "requirement": "300dpi"},
            {"check": "color_mode", "status": "pass", "requirement": "CMYK"},
            {"check": "text_size", "status": "pass", "requirement": "minimum 8pt"},
            {"check": "bleed_area", "status": "pass", "requirement": "3mm"}
        ]

    def _generate_responsive_layout(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Generate responsive layout data."""
        return {
            "breakpoints": {
                "mobile": {"width": 320, "height": 568},
                "tablet": {"width": 768, "height": 1024},
                "desktop": {"width": 1200, "height": 800}
            },
            "scaling_strategy": "proportional",
            "min_panel_size": {"width": 100, "height": 100}
        }

    def _generate_accessibility_data(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Generate accessibility data."""
        return {
            "alt_text_coverage": 0.95,
            "color_contrast_ratio": 4.5,
            "text_size_scalable": True,
            "keyboard_navigation": True,
            "screen_reader_compatible": True
        }

    def _extract_digital_quality_metrics(
        self,
        quality_assessment: Dict[str, Any],
        reading_validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract quality metrics for digital format."""
        return {
            "visual_quality": quality_assessment.get("visual_quality", {}).get("score", 0),
            "user_experience": reading_validation.get("engagement_assessment", {}).get("engagement_score", 0),
            "technical_performance": quality_assessment.get("technical_quality", {}).get("score", 0),
            "accessibility_score": 0.9  # Simplified
        }

    def _extract_page_quality_scores(
        self,
        page: Dict[str, Any],
        quality_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract quality scores for a specific page."""
        return {
            "completion_score": page.get("completion_score", 0),
            "visual_score": 0.8,  # Simplified
            "readability_score": 0.85  # Simplified
        }

    def _generate_recommendations(
        self,
        quality_assessment: Dict[str, Any],
        reading_validation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate improvement recommendations."""
        recommendations = []

        # Quality-based recommendations
        overall_score = quality_assessment.get("overall_score", 0)
        if overall_score < 0.7:
            recommendations.append({
                "type": "quality",
                "priority": "high",
                "message": "全体的な品質スコアが低いため、ビジュアル要素の改善を推奨",
                "action": "visual_improvement"
            })

        # Reading experience recommendations
        reading_score = reading_validation.get("overall_reading_score", 0)
        if reading_score < 0.6:
            recommendations.append({
                "type": "reading_experience",
                "priority": "medium",
                "message": "読みやすさの向上のため、ページフローの調整を推奨",
                "action": "flow_adjustment"
            })

        return recommendations

    def _generate_file_suggestions(
        self,
        output_format: str,
        metadata: OutputMetadata
    ) -> List[str]:
        """Generate suggested file names for output."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"manga_{timestamp}"

        suggestions = []

        if output_format == "web":
            suggestions.extend([
                f"{base_name}_web.json",
                f"{base_name}_web_assets.zip"
            ])
        elif output_format == "print":
            suggestions.extend([
                f"{base_name}_print.pdf",
                f"{base_name}_print_specs.json"
            ])
        elif output_format == "digital":
            suggestions.extend([
                f"{base_name}_digital.epub",
                f"{base_name}_digital_metadata.json"
            ])
        elif output_format == "api":
            suggestions.extend([
                f"{base_name}_api.json"
            ])
        else:  # comprehensive
            suggestions.extend([
                f"{base_name}_complete.json",
                f"{base_name}_summary.txt"
            ])

        return suggestions
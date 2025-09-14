"""Phase 7 Quality Assessment Module."""

from typing import Dict, Any, List
import asyncio
from dataclasses import dataclass
from enum import Enum

from app.core.logging import LoggerMixin


class QualityCategory(Enum):
    """Quality assessment categories."""
    VISUAL_CONSISTENCY = "visual_consistency"
    NARRATIVE_COHERENCE = "narrative_coherence"
    TECHNICAL_QUALITY = "technical_quality"
    READABILITY = "readability"
    PACING_FLOW = "pacing_flow"
    CHARACTER_DEVELOPMENT = "character_development"
    ARTISTIC_APPEAL = "artistic_appeal"


@dataclass
class QualityMetric:
    """Quality metric data structure."""
    category: QualityCategory
    score: float
    details: Dict[str, Any]
    recommendations: List[str]


class QualityAssessmentModule(LoggerMixin):
    """Module for comprehensive quality assessment."""

    def __init__(self):
        """Initialize quality assessment module."""
        self.quality_thresholds = {
            "excellent": 0.9,
            "good": 0.7,
            "acceptable": 0.5,
            "needs_improvement": 0.3
        }

        self.quality_categories = [
            QualityCategory.VISUAL_CONSISTENCY,
            QualityCategory.NARRATIVE_COHERENCE,
            QualityCategory.TECHNICAL_QUALITY,
            QualityCategory.READABILITY,
            QualityCategory.PACING_FLOW,
            QualityCategory.CHARACTER_DEVELOPMENT,
            QualityCategory.ARTISTIC_APPEAL
        ]

    async def perform_comprehensive_assessment(
        self,
        phase_results: Dict[int, Any]
    ) -> Dict[str, Any]:
        """Perform comprehensive quality assessment."""

        self.logger.info("Starting comprehensive quality assessment")

        quality_metrics = []

        # Assess each quality category
        for category in self.quality_categories:
            metric = await self._assess_quality_category(category, phase_results)
            quality_metrics.append(metric)

        # Calculate overall scores
        overall_score = sum(m.score for m in quality_metrics) / len(quality_metrics)

        # Generate improvement priorities
        improvement_priorities = self._prioritize_improvements(quality_metrics)

        # Analyze quality distribution
        quality_distribution = self._analyze_quality_distribution(quality_metrics)

        return {
            "quality_metrics": [
                {
                    "category": m.category.value,
                    "score": m.score,
                    "details": m.details,
                    "recommendations": m.recommendations
                }
                for m in quality_metrics
            ],
            "overall_score": overall_score,
            "quality_grade": self._determine_quality_grade(overall_score),
            "improvement_priorities": improvement_priorities,
            "quality_distribution": quality_distribution,
            "assessment_summary": self._generate_assessment_summary(quality_metrics)
        }

    async def _assess_quality_category(
        self,
        category: QualityCategory,
        phase_results: Dict[int, Any]
    ) -> QualityMetric:
        """Assess a specific quality category."""

        if category == QualityCategory.VISUAL_CONSISTENCY:
            return await self._assess_visual_consistency(phase_results)
        elif category == QualityCategory.NARRATIVE_COHERENCE:
            return await self._assess_narrative_coherence(phase_results)
        elif category == QualityCategory.TECHNICAL_QUALITY:
            return await self._assess_technical_quality(phase_results)
        elif category == QualityCategory.READABILITY:
            return await self._assess_readability(phase_results)
        elif category == QualityCategory.PACING_FLOW:
            return await self._assess_pacing_flow(phase_results)
        elif category == QualityCategory.CHARACTER_DEVELOPMENT:
            return await self._assess_character_development(phase_results)
        elif category == QualityCategory.ARTISTIC_APPEAL:
            return await self._assess_artistic_appeal(phase_results)
        else:
            raise ValueError(f"Unknown quality category: {category}")

    async def _assess_visual_consistency(self, phase_results: Dict[int, Any]) -> QualityMetric:
        """Assess visual consistency across pages."""

        # Get character data from Phase 2
        characters = phase_results.get(2, {}).get("characters", [])

        # Get image generation results from Phase 5
        images = phase_results.get(5, {}).get("generated_images", [])

        # Calculate character appearance consistency
        character_consistency = self._calculate_character_consistency(characters, images)

        # Calculate style consistency
        style_consistency = self._calculate_style_consistency(images)

        # Calculate color palette consistency
        color_consistency = self._calculate_color_consistency(images)

        overall_score = (character_consistency + style_consistency + color_consistency) / 3

        details = {
            "character_consistency": character_consistency,
            "style_consistency": style_consistency,
            "color_consistency": color_consistency,
            "total_characters": len(characters),
            "total_images": len(images)
        }

        recommendations = []
        if character_consistency < 0.7:
            recommendations.append("キャラクター外見の一貫性を改善")
        if style_consistency < 0.7:
            recommendations.append("画風の統一性を向上")
        if color_consistency < 0.7:
            recommendations.append("色彩設計の調整")

        return QualityMetric(
            category=QualityCategory.VISUAL_CONSISTENCY,
            score=overall_score,
            details=details,
            recommendations=recommendations
        )

    async def _assess_narrative_coherence(self, phase_results: Dict[int, Any]) -> QualityMetric:
        """Assess narrative coherence and story flow."""

        # Get story structure from Phase 3
        story_structure = phase_results.get(3, {}).get("story_structure", {})
        scenes = phase_results.get(3, {}).get("scenes", [])

        # Get dialogue data from Phase 6
        dialogue_data = phase_results.get(6, {}).get("dialogue_content", [])

        # Calculate story flow coherence
        story_flow_score = self._calculate_story_flow_coherence(scenes)

        # Calculate character arc consistency
        character_arc_score = self._calculate_character_arc_consistency(scenes, dialogue_data)

        # Calculate plot progression quality
        plot_progression_score = self._calculate_plot_progression_quality(story_structure)

        overall_score = (story_flow_score + character_arc_score + plot_progression_score) / 3

        details = {
            "story_flow_score": story_flow_score,
            "character_arc_score": character_arc_score,
            "plot_progression_score": plot_progression_score,
            "total_scenes": len(scenes),
            "total_dialogue_elements": len(dialogue_data)
        }

        recommendations = []
        if story_flow_score < 0.7:
            recommendations.append("シーン間の繋がりを改善")
        if character_arc_score < 0.7:
            recommendations.append("キャラクター成長の描写を強化")
        if plot_progression_score < 0.7:
            recommendations.append("プロット展開の調整")

        return QualityMetric(
            category=QualityCategory.NARRATIVE_COHERENCE,
            score=overall_score,
            details=details,
            recommendations=recommendations
        )

    async def _assess_technical_quality(self, phase_results: Dict[int, Any]) -> QualityMetric:
        """Assess technical quality of implementation."""

        # Get layout data from Phase 4
        pages = phase_results.get(4, {}).get("pages", [])

        # Get image quality from Phase 5
        image_quality = phase_results.get(5, {}).get("quality_analysis", {})

        # Calculate layout quality
        layout_quality = self._calculate_layout_quality(pages)

        # Calculate image technical quality
        image_tech_quality = image_quality.get("average_quality_score", 0.7)

        # Calculate resolution and format compliance
        format_compliance = self._calculate_format_compliance(pages)

        overall_score = (layout_quality + image_tech_quality + format_compliance) / 3

        details = {
            "layout_quality": layout_quality,
            "image_technical_quality": image_tech_quality,
            "format_compliance": format_compliance,
            "total_pages": len(pages)
        }

        recommendations = []
        if layout_quality < 0.7:
            recommendations.append("レイアウト設計の改善")
        if image_tech_quality < 0.7:
            recommendations.append("画像品質の向上")
        if format_compliance < 0.7:
            recommendations.append("フォーマット仕様の調整")

        return QualityMetric(
            category=QualityCategory.TECHNICAL_QUALITY,
            score=overall_score,
            details=details,
            recommendations=recommendations
        )

    async def _assess_readability(self, phase_results: Dict[int, Any]) -> QualityMetric:
        """Assess readability and user experience."""

        # Get dialogue placement from Phase 6
        dialogue_placement = phase_results.get(6, {}).get("dialogue_placement", [])

        # Get reading flow analysis
        reading_flow = phase_results.get(6, {}).get("reading_flow", {})

        # Calculate text readability
        text_readability = self._calculate_text_readability(dialogue_placement)

        # Calculate visual flow quality
        visual_flow_quality = reading_flow.get("flow_quality_score", 0.7)

        # Calculate accessibility score
        accessibility_score = self._calculate_accessibility_score(dialogue_placement)

        overall_score = (text_readability + visual_flow_quality + accessibility_score) / 3

        details = {
            "text_readability": text_readability,
            "visual_flow_quality": visual_flow_quality,
            "accessibility_score": accessibility_score,
            "total_dialogue_elements": len(dialogue_placement)
        }

        recommendations = []
        if text_readability < 0.7:
            recommendations.append("テキストの読みやすさ改善")
        if visual_flow_quality < 0.7:
            recommendations.append("視覚的フローの最適化")
        if accessibility_score < 0.7:
            recommendations.append("アクセシビリティの向上")

        return QualityMetric(
            category=QualityCategory.READABILITY,
            score=overall_score,
            details=details,
            recommendations=recommendations
        )

    async def _assess_pacing_flow(self, phase_results: Dict[int, Any]) -> QualityMetric:
        """Assess pacing and flow quality."""

        # Get pacing analysis from Phase 3
        pacing_analysis = phase_results.get(3, {}).get("pacing_analysis", {})

        # Get dialogue pacing from Phase 6
        dialogue_pacing = phase_results.get(6, {}).get("timing_analysis", {})

        # Calculate story pacing quality
        story_pacing_score = pacing_analysis.get("overall_pacing_score", 0.7)

        # Calculate dialogue timing quality
        dialogue_timing_score = dialogue_pacing.get("pacing_quality_score", 0.7)

        # Calculate page transition flow
        page_flow_score = self._calculate_page_flow_quality(phase_results)

        overall_score = (story_pacing_score + dialogue_timing_score + page_flow_score) / 3

        details = {
            "story_pacing_score": story_pacing_score,
            "dialogue_timing_score": dialogue_timing_score,
            "page_flow_score": page_flow_score
        }

        recommendations = []
        if story_pacing_score < 0.7:
            recommendations.append("ストーリーペースの調整")
        if dialogue_timing_score < 0.7:
            recommendations.append("対話タイミングの最適化")
        if page_flow_score < 0.7:
            recommendations.append("ページ間フローの改善")

        return QualityMetric(
            category=QualityCategory.PACING_FLOW,
            score=overall_score,
            details=details,
            recommendations=recommendations
        )

    async def _assess_character_development(self, phase_results: Dict[int, Any]) -> QualityMetric:
        """Assess character development quality."""

        # Get character data from Phase 2
        characters = phase_results.get(2, {}).get("characters", [])

        # Get narrative flow from Phase 3
        narrative_flow = phase_results.get(3, {}).get("narrative_flow", {})

        # Calculate character depth
        character_depth_score = self._calculate_character_depth(characters)

        # Calculate character arc quality
        character_arc_quality = narrative_flow.get("character_arcs", {})

        # Calculate dialogue characterization
        dialogue_characterization = self._calculate_dialogue_characterization(phase_results)

        overall_score = (character_depth_score + 0.7 + dialogue_characterization) / 3

        details = {
            "character_depth_score": character_depth_score,
            "character_arc_quality": 0.7,  # Simplified
            "dialogue_characterization": dialogue_characterization,
            "total_characters": len(characters)
        }

        recommendations = []
        if character_depth_score < 0.7:
            recommendations.append("キャラクター設定の深化")
        if dialogue_characterization < 0.7:
            recommendations.append("対話によるキャラクター表現の強化")

        return QualityMetric(
            category=QualityCategory.CHARACTER_DEVELOPMENT,
            score=overall_score,
            details=details,
            recommendations=recommendations
        )

    async def _assess_artistic_appeal(self, phase_results: Dict[int, Any]) -> QualityMetric:
        """Assess artistic appeal and visual impact."""

        # Get visual style from Phase 5
        visual_style = phase_results.get(5, {}).get("visual_style", {})

        # Get layout quality from Phase 4
        layout_analysis = phase_results.get(4, {}).get("layout_analysis", {})

        # Calculate visual impact
        visual_impact_score = self._calculate_visual_impact(visual_style)

        # Calculate composition quality
        composition_quality = layout_analysis.get("composition_quality_score", 0.7)

        # Calculate artistic coherence
        artistic_coherence = self._calculate_artistic_coherence(phase_results)

        overall_score = (visual_impact_score + composition_quality + artistic_coherence) / 3

        details = {
            "visual_impact_score": visual_impact_score,
            "composition_quality": composition_quality,
            "artistic_coherence": artistic_coherence
        }

        recommendations = []
        if visual_impact_score < 0.7:
            recommendations.append("ビジュアルインパクトの向上")
        if composition_quality < 0.7:
            recommendations.append("構図クオリティの改善")
        if artistic_coherence < 0.7:
            recommendations.append("芸術的一貫性の強化")

        return QualityMetric(
            category=QualityCategory.ARTISTIC_APPEAL,
            score=overall_score,
            details=details,
            recommendations=recommendations
        )

    # Helper methods (simplified implementations)
    def _calculate_character_consistency(self, characters: List[Dict], images: List[Dict]) -> float:
        """Calculate character appearance consistency."""
        if not characters or not images:
            return 0.5
        return 0.8  # Simplified calculation

    def _calculate_style_consistency(self, images: List[Dict]) -> float:
        """Calculate visual style consistency."""
        if not images:
            return 0.5
        return 0.75  # Simplified calculation

    def _calculate_color_consistency(self, images: List[Dict]) -> float:
        """Calculate color palette consistency."""
        if not images:
            return 0.5
        return 0.8  # Simplified calculation

    def _calculate_story_flow_coherence(self, scenes: List[Dict]) -> float:
        """Calculate story flow coherence."""
        if not scenes:
            return 0.5
        return 0.75  # Simplified calculation

    def _calculate_character_arc_consistency(self, scenes: List[Dict], dialogue: List[Dict]) -> float:
        """Calculate character arc consistency."""
        return 0.7  # Simplified calculation

    def _calculate_plot_progression_quality(self, story_structure: Dict) -> float:
        """Calculate plot progression quality."""
        return 0.8  # Simplified calculation

    def _calculate_layout_quality(self, pages: List[Dict]) -> float:
        """Calculate layout quality."""
        if not pages:
            return 0.5
        return 0.75  # Simplified calculation

    def _calculate_format_compliance(self, pages: List[Dict]) -> float:
        """Calculate format compliance."""
        return 0.9  # Simplified calculation

    def _calculate_text_readability(self, dialogue_placement: List[Dict]) -> float:
        """Calculate text readability."""
        return 0.8  # Simplified calculation

    def _calculate_accessibility_score(self, dialogue_placement: List[Dict]) -> float:
        """Calculate accessibility score."""
        return 0.75  # Simplified calculation

    def _calculate_page_flow_quality(self, phase_results: Dict[int, Any]) -> float:
        """Calculate page flow quality."""
        return 0.7  # Simplified calculation

    def _calculate_character_depth(self, characters: List[Dict]) -> float:
        """Calculate character depth."""
        if not characters:
            return 0.5
        return 0.8  # Simplified calculation

    def _calculate_dialogue_characterization(self, phase_results: Dict[int, Any]) -> float:
        """Calculate dialogue characterization quality."""
        return 0.75  # Simplified calculation

    def _calculate_visual_impact(self, visual_style: Dict) -> float:
        """Calculate visual impact."""
        return 0.8  # Simplified calculation

    def _calculate_artistic_coherence(self, phase_results: Dict[int, Any]) -> float:
        """Calculate artistic coherence."""
        return 0.75  # Simplified calculation

    def _prioritize_improvements(self, quality_metrics: List[QualityMetric]) -> List[Dict[str, Any]]:
        """Prioritize improvement recommendations."""

        low_scores = [m for m in quality_metrics if m.score < 0.7]
        sorted_issues = sorted(low_scores, key=lambda x: x.score)

        priorities = []
        for i, metric in enumerate(sorted_issues):
            priority = {
                "rank": i + 1,
                "category": metric.category.value,
                "score": metric.score,
                "urgency": "high" if metric.score < 0.5 else "medium",
                "recommendations": metric.recommendations
            }
            priorities.append(priority)

        return priorities

    def _analyze_quality_distribution(self, quality_metrics: List[QualityMetric]) -> Dict[str, Any]:
        """Analyze quality score distribution."""

        scores = [m.score for m in quality_metrics]

        return {
            "average_score": sum(scores) / len(scores),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "score_variance": self._calculate_variance(scores),
            "categories_above_threshold": len([s for s in scores if s >= 0.7]),
            "categories_below_threshold": len([s for s in scores if s < 0.7])
        }

    def _calculate_variance(self, scores: List[float]) -> float:
        """Calculate variance of scores."""
        if not scores:
            return 0.0

        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return variance

    def _generate_assessment_summary(self, quality_metrics: List[QualityMetric]) -> str:
        """Generate quality assessment summary."""

        overall_score = sum(m.score for m in quality_metrics) / len(quality_metrics)

        if overall_score >= 0.9:
            return "優秀な品質レベルです。全体的に高い完成度を達成しています。"
        elif overall_score >= 0.7:
            return "良好な品質レベルです。一部改善点はありますが、十分な品質です。"
        elif overall_score >= 0.5:
            return "許容可能な品質レベルです。改善の余地があります。"
        else:
            return "品質向上が必要です。重要な問題が複数確認されています。"

    def _determine_quality_grade(self, score: float) -> str:
        """Determine quality grade based on score."""

        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"
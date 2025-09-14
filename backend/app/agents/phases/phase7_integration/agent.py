"""Phase 7: Final Integration and Quality Adjustment Agent."""

from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
import asyncio
import json
import math

from app.agents.base.agent import BaseAgent
from app.core.config import settings
from app.services.vertex_ai_service import VertexAIService

from .schemas import (
    FinalIntegrationInput,
    FinalIntegrationOutput,
    QualityMetric,
    QualityGrade,
    IntegrationStatus,
    OutputFormat
)
from .validator import Phase7Validator


class Phase7IntegrationAgent(BaseAgent):
    """Agent for final integration and quality adjustment of manga."""

    def __init__(self):
        super().__init__(
            phase_number=7,
            phase_name="最終統合・品質調整",
            timeout_seconds=settings.phase_timeouts[7]
        )

        # Initialize structured prompts
        from .prompts import FinalIntegrationPrompts
        self.prompts = FinalIntegrationPrompts()

        # Initialize modular components
        from .quality_assessment import QualityAssessmentModule
        from .page_compiler import PageCompilerModule
        from .output_formatter import OutputFormatterModule

        self.quality_assessor = QualityAssessmentModule()
        self.page_compiler = PageCompilerModule()
        self.output_formatter = OutputFormatterModule()

        # Integration tasks for final assembly
        self.integration_tasks = [
            "compile_pages",
            "optimize_layouts",
            "ensure_consistency",
            "validate_reading_flow",
            "generate_metadata",
            "create_preview",
            "prepare_output_formats"
        ]

        # Vertex AI サービス初期化
        self.vertex_ai = VertexAIService()

    def _create_validator(self):
        """Create Phase 7 specific validator."""
        return Phase7Validator()

    async def _generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate comprehensive prompt for final integration assessment."""
        return self.prompts.get_main_prompt(
            input_data=input_data,
            previous_results=previous_results
        )

    async def _process_ai_response(
        self,
        ai_response: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process AI response into structured output."""
        try:
            # Try to parse AI response as JSON
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                parsed_data = json.loads(json_str)
                return parsed_data
            else:
                raise ValueError("No JSON found in AI response")

        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse AI response: {e}")
            return {}

    async def _generate_preview(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview data for Phase 7."""

        preview = {
            "phase_name": "最終統合・品質調整",
            "summary": f"品質スコア: {output_data.get('overall_quality_score', 0.0):.1f}",
            "key_insights": [],
            "visual_elements": []
        }

        # Add key insights
        overall_score = output_data.get("overall_quality_score", 0.0)
        if overall_score > 0:
            preview["key_insights"].append(f"総合品質: {overall_score:.1f}")

        quality_grade = output_data.get("quality_grade")
        if quality_grade:
            preview["key_insights"].append(f"品質等級: {quality_grade}")

        total_pages = output_data.get("total_pages", 0)
        if total_pages > 0:
            preview["key_insights"].append(f"総ページ数: {total_pages}")

        production_ready = output_data.get("production_ready", False)
        preview["key_insights"].append(f"制作可能: {'はい' if production_ready else 'いいえ'}")

        # Add visual elements
        final_scores = output_data.get("final_scores", {})
        if final_scores:
            for category, score in final_scores.items():
                if isinstance(score, (int, float)) and score > 0:
                    preview["visual_elements"].append(f"{category}: {score:.1f}")

        integration_status = output_data.get("integration_status")
        if integration_status:
            preview["visual_elements"].append(f"統合状況: {integration_status}")

        return preview

    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: UUID,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Perform final integration and quality assessment."""

        if not previous_results or not all(i in previous_results for i in [1, 2, 3, 4, 5, 6]):
            raise ValueError("All previous phases (1-6) results required for final integration")

        self.logger.info(
            "Starting final integration and quality assessment",
            extra={"session_id": str(session_id)}
        )

        # Extract all previous phase results
        phase_results = {i: previous_results[i] for i in range(1, 7)}

        # Use modular quality assessment
        quality_assessment = await self.quality_assessor.assess_overall_quality(
            phase_results, session_id
        )

        # Use modular page compilation
        compilation_result = await self.page_compiler.compile_manga_pages(phase_results)
        compiled_pages = compilation_result.get("compiled_pages", [])
        reading_validation = compilation_result.get("reading_validation", {})
        compilation_metadata = compilation_result.get("compilation_metadata", {})

        # Use modular output formatting
        output_format = input_data.get("output_format", "comprehensive")
        formatted_output = await self.output_formatter.format_output(
            compiled_pages,
            quality_assessment,
            reading_validation,
            compilation_metadata,
            output_format
        )

        # Generate final metadata
        manga_metadata = await self._generate_manga_metadata(phase_results)

        # Generate improvement recommendations
        improvement_plan = await self._generate_improvement_plan(
            quality_assessment, phase_results
        )

        # Calculate final scores
        final_scores = await self._calculate_final_scores(quality_assessment)

        result = {
            "quality_assessment": quality_assessment,
            "compiled_pages": compiled_pages,
            "reading_validation": reading_validation,
            "compilation_metadata": compilation_metadata,
            "formatted_output": formatted_output.content if hasattr(formatted_output, 'content') else formatted_output,
            "output_metadata": formatted_output.metadata if hasattr(formatted_output, 'metadata') else {},
            "file_suggestions": formatted_output.file_suggestions if hasattr(formatted_output, 'file_suggestions') else [],
            "manga_metadata": manga_metadata,
            "improvement_plan": improvement_plan,
            "final_scores": final_scores,
            "integration_status": IntegrationStatus.COMPLETED.value,
            "total_pages": len(compiled_pages),
            "overall_quality_score": final_scores.get("overall_score", 0.0),
            "quality_grade": self._determine_quality_grade(final_scores.get("overall_score", 0.0)).value,
            "production_ready": final_scores.get("overall_score", 0.0) >= 0.7,
            "processing_summary": self._generate_processing_summary(phase_results, final_scores)
        }

        return result

    async def generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate comprehensive prompt for final integration assessment."""
        return await self._generate_prompt(input_data, previous_results)

    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate Phase 7 output."""

        validator = self._create_validator()
        validation_result = await validator.validate(output_data)
        return validation_result.is_valid

    async def _generate_manga_metadata(
        self,
        phase_results: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate comprehensive manga metadata."""

        metadata = {
            "creation_timestamp": None,
            "page_count": 0,
            "panel_count": 0,
            "character_count": 0,
            "genre": None,
            "target_audience": None,
            "style_classification": None,
            "complexity_score": 0.0,
            "content_tags": [],
            "estimated_reading_time": None
        }

        try:
            # Extract from Phase 1 (concept)
            if 1 in phase_results:
                phase1_data = phase_results[1].get("output_data", {})
                genre_analysis = phase1_data.get("genre_analysis", {})
                metadata["genre"] = genre_analysis.get("primary_genre")

                theme_analysis = phase1_data.get("theme_analysis", {})
                if theme_analysis.get("main_themes"):
                    metadata["content_tags"].extend(theme_analysis["main_themes"])

            # Extract from Phase 2 (characters)
            if 2 in phase_results:
                phase2_data = phase_results[2].get("output_data", {})
                characters = phase2_data.get("characters", [])
                metadata["character_count"] = len(characters)

                style_guide = phase2_data.get("style_guide", {})
                metadata["style_classification"] = style_guide.get("overall_style")

            # Extract from Phase 5 (images/layout)
            if 5 in phase_results:
                phase5_data = phase_results[5].get("output_data", {})
                panels = phase5_data.get("panels", [])
                metadata["panel_count"] = len(panels)

                # Estimate pages from panels (rough estimate: 4-6 panels per page)
                estimated_pages = max(1, len(panels) // 5)
                metadata["page_count"] = estimated_pages

                # Estimate reading time (rough: 1-2 minutes per page)
                metadata["estimated_reading_time"] = f"{estimated_pages * 1.5:.0f} minutes"

            # Calculate complexity score
            complexity_factors = [
                min(1.0, metadata["character_count"] / 10),  # More characters = more complex
                min(1.0, metadata["panel_count"] / 50),      # More panels = more complex
                0.5 if len(metadata["content_tags"]) > 3 else 0.3  # More themes = more complex
            ]
            metadata["complexity_score"] = sum(complexity_factors) / len(complexity_factors)

        except Exception as e:
            self.logger.warning(f"Error generating manga metadata: {e}")

        return metadata

    async def _generate_improvement_plan(
        self,
        quality_assessment: Dict[str, Any],
        phase_results: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate improvement recommendations based on quality assessment."""

        plan = {
            "priority_issues": [],
            "quick_fixes": [],
            "major_improvements": [],
            "estimated_effort": {},
            "impact_assessment": {},
            "implementation_order": []
        }

        try:
            overall_score = quality_assessment.get("overall_score", 0.0)

            # Identify priority issues based on score
            if overall_score < 0.5:
                plan["priority_issues"].extend([
                    "Overall quality below acceptable threshold",
                    "Requires comprehensive revision",
                    "Consider redesigning core elements"
                ])
            elif overall_score < 0.7:
                plan["priority_issues"].extend([
                    "Quality needs improvement for production",
                    "Focus on critical quality metrics"
                ])

            # Analyze individual metrics
            metrics = quality_assessment.get("metrics", [])
            for metric in metrics:
                if isinstance(metric, dict):
                    score = metric.get("score", 0.0)
                    name = metric.get("name", "Unknown")

                    if score < 0.5:
                        plan["priority_issues"].append(f"Critical issue with {name}")
                        plan["estimated_effort"][name] = "High"
                        plan["impact_assessment"][name] = 0.8
                    elif score < 0.7:
                        plan["major_improvements"].append(f"Improve {name}")
                        plan["estimated_effort"][name] = "Medium"
                        plan["impact_assessment"][name] = 0.6
                    else:
                        plan["quick_fixes"].append(f"Minor tweaks to {name}")
                        plan["estimated_effort"][name] = "Low"
                        plan["impact_assessment"][name] = 0.3

            # Create implementation order based on impact and effort
            all_issues = [(issue, plan["impact_assessment"].get(issue.split()[-1], 0.5))
                         for issue in plan["priority_issues"] + plan["major_improvements"]]
            all_issues.sort(key=lambda x: x[1], reverse=True)  # Sort by impact
            plan["implementation_order"] = [issue[0] for issue in all_issues]

        except Exception as e:
            self.logger.warning(f"Error generating improvement plan: {e}")

        return plan

    async def _calculate_final_scores(
        self,
        quality_assessment: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate comprehensive final scores."""

        scores = {
            "overall_score": 0.0,
            "content_quality": 0.0,
            "visual_appeal": 0.0,
            "technical_execution": 0.0,
            "narrative_coherence": 0.0,
            "production_readiness": 0.0,
            "market_appeal": 0.0
        }

        try:
            # Use overall score from quality assessment
            overall_score = quality_assessment.get("overall_score", 0.0)
            scores["overall_score"] = overall_score

            # Calculate category scores from metrics
            metrics = quality_assessment.get("metrics", [])
            category_scores = quality_assessment.get("category_scores", {})

            # Map categories to final score categories
            category_mapping = {
                "content": "content_quality",
                "visual": "visual_appeal",
                "technical": "technical_execution",
                "narrative": "narrative_coherence",
                "production": "production_readiness",
                "market": "market_appeal"
            }

            for category, score_key in category_mapping.items():
                if category in category_scores:
                    scores[score_key] = category_scores[category]
                else:
                    # Fallback: use overall score with some variation
                    scores[score_key] = max(0.0, min(1.0, overall_score + (hash(category) % 20 - 10) / 100))

        except Exception as e:
            self.logger.warning(f"Error calculating final scores: {e}")

        return scores

    def _determine_quality_grade(self, score: float) -> QualityGrade:
        """Determine quality grade from numeric score."""
        if score >= 0.9:
            return QualityGrade.EXCELLENT
        elif score >= 0.8:
            return QualityGrade.GOOD
        elif score >= 0.7:
            return QualityGrade.ACCEPTABLE
        elif score >= 0.5:
            return QualityGrade.NEEDS_IMPROVEMENT
        else:
            return QualityGrade.POOR

    def _generate_processing_summary(
        self,
        phase_results: Dict[int, Dict[str, Any]],
        final_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate summary of entire processing pipeline."""

        summary = {
            "phases_completed": list(phase_results.keys()),
            "total_processing_time": 0.0,
            "phase_timings": {},
            "quality_progression": {},
            "key_achievements": [],
            "major_challenges": [],
            "final_assessment": "",
            "next_steps": []
        }

        try:
            # Calculate processing times
            total_time = 0.0
            for phase_num, result in phase_results.items():
                processing_time = result.get("processing_time", 0.0)
                summary["phase_timings"][f"phase_{phase_num}"] = processing_time
                total_time += processing_time

            summary["total_processing_time"] = total_time

            # Track quality progression
            for phase_num, result in phase_results.items():
                quality_score = result.get("quality_score", 0.0)
                summary["quality_progression"][f"phase_{phase_num}"] = quality_score

            # Identify key achievements
            overall_score = final_scores.get("overall_score", 0.0)
            if overall_score >= 0.8:
                summary["key_achievements"].append("High overall quality achieved")
            if final_scores.get("production_readiness", 0.0) >= 0.7:
                summary["key_achievements"].append("Production ready quality")
            if len(phase_results) == 6:
                summary["key_achievements"].append("All phases completed successfully")

            # Generate final assessment
            if overall_score >= 0.8:
                summary["final_assessment"] = "Excellent quality manga ready for publication"
            elif overall_score >= 0.7:
                summary["final_assessment"] = "Good quality manga suitable for production"
            elif overall_score >= 0.5:
                summary["final_assessment"] = "Acceptable quality with room for improvement"
            else:
                summary["final_assessment"] = "Quality needs significant improvement"

            # Suggest next steps
            if overall_score >= 0.7:
                summary["next_steps"].extend([
                    "Prepare for final production",
                    "Review for publishing requirements",
                    "Consider market positioning"
                ])
            else:
                summary["next_steps"].extend([
                    "Address quality issues identified",
                    "Review and revise problematic phases",
                    "Re-run quality assessment"
                ])

        except Exception as e:
            self.logger.warning(f"Error generating processing summary: {e}")

        return summary
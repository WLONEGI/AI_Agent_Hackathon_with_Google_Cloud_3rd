"""Validator for Phase 7: Final Integration and Quality Adjustment."""

from typing import Dict, Any, List
from app.agents.base.validator import BaseValidator, ValidationResult
from .schemas import (
    FinalIntegrationOutput,
    QualityGrade,
    IntegrationStatus,
    OutputFormat
)


class Phase7Validator(BaseValidator):
    """Validator for Phase 7 final integration output."""

    def __init__(self):
        super().__init__("Final Integration and Quality Adjustment")

        # Phase 7 specific required fields
        self.required_fields.extend([
            "quality_assessment",
            "compiled_pages",
            "reading_validation",
            "compilation_metadata",
            "formatted_output",
            "manga_metadata",
            "final_scores",
            "integration_status",
            "total_pages",
            "overall_quality_score",
            "quality_grade",
            "production_ready"
        ])

        # Quality thresholds
        self.min_quality_score = 0.0
        self.production_ready_threshold = 0.7
        self.min_pages = 1
        self.max_pages = 200

    async def validate(self, output_data: Dict[str, Any]) -> ValidationResult:
        """Validate Phase 7 output with comprehensive checks."""

        result = ValidationResult()
        result.phase_name = "Phase 7: Final Integration and Quality Adjustment"
        result.is_valid = True

        # Basic field validation
        basic_validation = self._validate_required_fields(output_data)
        if not basic_validation.is_valid:
            result.merge(basic_validation)
            return result

        # Integration-specific validations
        await self._validate_phase_specific(output_data, result)

        return result

    async def _validate_phase_specific(
        self,
        output: Dict[str, Any],
        result: ValidationResult
    ):
        """Validate Phase 7 specific requirements."""

        # Validate quality assessment
        await self._validate_quality_assessment(output.get("quality_assessment", {}), result)

        # Validate compiled pages
        await self._validate_compiled_pages(output.get("compiled_pages", []), result)

        # Validate final scores
        self._validate_final_scores(output.get("final_scores", {}), result)

        # Validate integration status
        self._validate_integration_status(output, result)

        # Validate production readiness
        self._validate_production_readiness(output, result)

        # Validate metadata consistency
        self._validate_metadata_consistency(output, result)

    async def _validate_quality_assessment(self, quality_assessment: Dict[str, Any], result: ValidationResult):
        """Validate quality assessment structure."""

        if not quality_assessment:
            result.add_error("Quality assessment is required")
            return

        required_qa_fields = ["overall_score", "metrics", "category_scores", "recommendations"]
        missing_fields = [field for field in required_qa_fields if not quality_assessment.get(field)]
        if missing_fields:
            result.add_error(f"Quality assessment missing fields: {missing_fields}")

        # Validate overall score
        overall_score = quality_assessment.get("overall_score")
        if overall_score is not None:
            if not isinstance(overall_score, (int, float)):
                result.add_error("Quality assessment overall_score must be numeric")
            elif not (0.0 <= overall_score <= 1.0):
                result.add_error(f"Quality assessment overall_score out of range: {overall_score}")

        # Validate metrics
        metrics = quality_assessment.get("metrics", [])
        if not isinstance(metrics, list):
            result.add_error("Quality metrics must be a list")
        else:
            for i, metric in enumerate(metrics):
                if not isinstance(metric, dict):
                    result.add_error(f"Metric {i} must be a dictionary")
                    continue

                required_metric_fields = ["name", "score", "weight"]
                missing_metric_fields = [field for field in required_metric_fields if field not in metric]
                if missing_metric_fields:
                    result.add_error(f"Metric {i} missing fields: {missing_metric_fields}")

                # Validate metric scores
                score = metric.get("score")
                if score is not None and not (0.0 <= score <= 1.0):
                    result.add_error(f"Metric {i} score out of range: {score}")

                weight = metric.get("weight")
                if weight is not None and not (0.0 <= weight <= 1.0):
                    result.add_error(f"Metric {i} weight out of range: {weight}")

    async def _validate_compiled_pages(self, compiled_pages: List[Dict[str, Any]], result: ValidationResult):
        """Validate compiled pages structure."""

        if not compiled_pages:
            result.add_error("Compiled pages are required")
            return

        if len(compiled_pages) < self.min_pages:
            result.add_error(f"Too few pages: {len(compiled_pages)} (minimum: {self.min_pages})")

        if len(compiled_pages) > self.max_pages:
            result.add_warning(f"Many pages: {len(compiled_pages)} (maximum recommended: {self.max_pages})")

        # Validate individual pages
        for i, page in enumerate(compiled_pages):
            if not isinstance(page, dict):
                result.add_error(f"Page {i} must be a dictionary")
                continue

            required_page_fields = ["page_number", "panels", "layout_type"]
            missing_page_fields = [field for field in required_page_fields if not page.get(field)]
            if missing_page_fields:
                result.add_error(f"Page {i} missing fields: {missing_page_fields}")

            # Validate page number
            page_number = page.get("page_number")
            if page_number is not None and page_number != i + 1:
                result.add_warning(f"Page {i} has inconsistent page_number: {page_number}")

            # Validate panels
            panels = page.get("panels", [])
            if not isinstance(panels, list):
                result.add_error(f"Page {i} panels must be a list")
            elif len(panels) == 0:
                result.add_warning(f"Page {i} has no panels")

    def _validate_final_scores(self, final_scores: Dict[str, Any], result: ValidationResult):
        """Validate final scores structure."""

        if not final_scores:
            result.add_error("Final scores are required")
            return

        expected_scores = [
            "overall_score", "content_quality", "visual_appeal",
            "technical_execution", "narrative_coherence", "production_readiness"
        ]

        for score_name in expected_scores:
            score = final_scores.get(score_name)
            if score is None:
                result.add_warning(f"Missing final score: {score_name}")
            elif not isinstance(score, (int, float)):
                result.add_error(f"Final score {score_name} must be numeric")
            elif not (0.0 <= score <= 1.0):
                result.add_error(f"Final score {score_name} out of range: {score}")

    def _validate_integration_status(self, output: Dict[str, Any], result: ValidationResult):
        """Validate integration status."""

        integration_status = output.get("integration_status")
        if not integration_status:
            result.add_error("Integration status is required")
            return

        try:
            IntegrationStatus(integration_status)
        except ValueError:
            result.add_error(f"Invalid integration status: {integration_status}")

        # Check status consistency
        if integration_status == IntegrationStatus.COMPLETED:
            if not output.get("compiled_pages"):
                result.add_error("Completed integration must have compiled pages")
            if not output.get("quality_assessment"):
                result.add_error("Completed integration must have quality assessment")

    def _validate_production_readiness(self, output: Dict[str, Any], result: ValidationResult):
        """Validate production readiness assessment."""

        production_ready = output.get("production_ready")
        overall_quality_score = output.get("overall_quality_score", 0.0)

        if production_ready is None:
            result.add_error("Production readiness flag is required")
            return

        if not isinstance(production_ready, bool):
            result.add_error("Production readiness must be boolean")
            return

        # Check consistency with quality score
        if production_ready and overall_quality_score < self.production_ready_threshold:
            result.add_warning(
                f"Production ready flag inconsistent with quality score: "
                f"{overall_quality_score} < {self.production_ready_threshold}"
            )

        if not production_ready and overall_quality_score >= self.production_ready_threshold:
            result.add_warning(
                f"Production not ready despite high quality score: {overall_quality_score}"
            )

    def _validate_metadata_consistency(self, output: Dict[str, Any], result: ValidationResult):
        """Validate metadata consistency across output."""

        # Check page count consistency
        compiled_pages = output.get("compiled_pages", [])
        total_pages = output.get("total_pages", 0)
        manga_metadata = output.get("manga_metadata", {})

        if len(compiled_pages) != total_pages:
            result.add_error(f"Page count inconsistency: {len(compiled_pages)} vs {total_pages}")

        # Check metadata page count
        metadata_page_count = manga_metadata.get("page_count", 0)
        if metadata_page_count != total_pages:
            result.add_warning(f"Metadata page count inconsistency: {metadata_page_count} vs {total_pages}")

        # Validate quality grade consistency
        quality_grade = output.get("quality_grade")
        overall_quality_score = output.get("overall_quality_score", 0.0)

        if quality_grade:
            expected_grade = self._determine_quality_grade(overall_quality_score)
            try:
                actual_grade = QualityGrade(quality_grade)
                if actual_grade != expected_grade:
                    result.add_warning(
                        f"Quality grade inconsistent with score: {quality_grade} vs expected {expected_grade.value}"
                    )
            except ValueError:
                result.add_error(f"Invalid quality grade: {quality_grade}")

    def _determine_quality_grade(self, score: float) -> QualityGrade:
        """Determine quality grade from score."""
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

    def calculate_quality_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate quality score for Phase 7 output."""

        if not output_data:
            return 0.0

        score = 1.0

        # Check overall quality score
        overall_quality = output_data.get("overall_quality_score", 0.0)
        if overall_quality < 0.7:
            score -= 0.2

        # Check integration completeness
        if not output_data.get("compiled_pages"):
            score -= 0.3

        if not output_data.get("quality_assessment"):
            score -= 0.2

        # Check production readiness
        if not output_data.get("production_ready", False):
            score -= 0.1

        # Check metadata presence
        if not output_data.get("manga_metadata"):
            score -= 0.1

        # Check final scores completeness
        final_scores = output_data.get("final_scores", {})
        if len(final_scores) < 5:  # Expected minimum score categories
            score -= 0.1

        return max(0.0, score)
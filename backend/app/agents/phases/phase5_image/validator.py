"""Phase 5: Image Generation - Validation Logic."""

from typing import Dict, Any, List, Optional, Union
import math
from app.agents.base.validator import BaseValidator, ValidationResult, ValidationError
from .schemas import (
    ImageGenerationOutput,
    ImageGenerationResult,
    QualityAnalysis,
    ConsistencyAnalysis,
    CacheUtilization,
    ConsistencyLevel,
    QualityLevel
)

class Phase5Validator(BaseValidator):
    """Validator for Phase 5 image generation output."""

    def __init__(self):
        super().__init__(phase_name="画像生成")

        # Override required fields for Phase 5
        self.required_fields.extend([
            "generated_images",
            "scene_image_mapping",
            "quality_analysis",
            "consistency_report",
            "generation_stats",
            "total_images_generated",
            "successful_generations",
            "failed_generations"
        ])

        # Override quality weights for Phase 5
        self.quality_weights = {
            "completeness": 0.25,           # All required images generated
            "accuracy": 0.25,               # Images match specifications
            "consistency": 0.20,            # Style and character consistency
            "format_compliance": 0.15,      # Output format compliance
            "efficiency": 0.15              # Generation efficiency
        }

        # Phase 5 specific validation thresholds
        self.validation_thresholds = {
            "minimum_success_rate": 0.5,           # 50% minimum success rate
            "minimum_quality_score": 0.6,          # 60% minimum average quality
            "maximum_retry_rate": 0.3,             # 30% max retry rate
            "minimum_cache_efficiency": 0.1,       # 10% minimum cache hit rate
            "maximum_generation_time": 60000,      # 60 seconds max per image
            "minimum_consistency_score": 0.6,      # 60% minimum consistency
            "minimum_parallel_efficiency": 0.3     # 30% minimum parallel efficiency
        }

    async def validate_output(self, output_data: Dict[str, Any]) -> ValidationResult:
        """Validate Phase 5 image generation output."""

        errors = []
        warnings = []

        try:
            # Validate basic structure
            structure_errors = await self._validate_basic_structure(output_data)
            errors.extend(structure_errors)

            # Validate generated images
            image_errors = await self._validate_generated_images(output_data)
            errors.extend(image_errors)

            # Validate quality analysis
            quality_errors = await self._validate_quality_analysis(output_data)
            errors.extend(quality_errors)

            # Validate consistency report
            consistency_errors = await self._validate_consistency_report(output_data)
            errors.extend(consistency_errors)

            # Validate generation statistics
            stats_errors = await self._validate_generation_statistics(output_data)
            errors.extend(stats_errors)

            # Validate cache utilization
            cache_errors = await self._validate_cache_utilization(output_data)
            errors.extend(cache_errors)

            # Performance validation warnings
            performance_warnings = await self._validate_performance_metrics(output_data)
            warnings.extend(performance_warnings)

        except Exception as e:
            errors.append(ValidationError("validation_error", f"Validation process failed: {str(e)}", "error"))

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    async def _validate_basic_structure(self, output_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate basic output structure."""
        errors = []

        # Check for required fields
        for field in self.required_fields:
            if field not in output_data:
                errors.append(ValidationError(field, f"Missing required field: {field}", "error"))

        # Validate data types
        if "generated_images" in output_data:
            if not isinstance(output_data["generated_images"], list):
                errors.append(ValidationError("generated_images", "generated_images must be a list", "error"))

        if "total_images_generated" in output_data:
            if not isinstance(output_data["total_images_generated"], int) or output_data["total_images_generated"] < 0:
                errors.append(ValidationError("total_images_generated", "total_images_generated must be a non-negative integer", "error"))

        if "successful_generations" in output_data:
            if not isinstance(output_data["successful_generations"], int) or output_data["successful_generations"] < 0:
                errors.append(ValidationError("successful_generations", "successful_generations must be a non-negative integer", "error"))

        if "failed_generations" in output_data:
            if not isinstance(output_data["failed_generations"], int) or output_data["failed_generations"] < 0:
                errors.append(ValidationError("failed_generations", "failed_generations must be a non-negative integer", "error"))

        return errors

    async def _validate_generated_images(self, output_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate generated images data."""
        errors = []

        generated_images = output_data.get("generated_images", [])

        # Check if any images were generated
        if not generated_images:
            errors.append(ValidationError("generated_images", "No images generated", "error"))
            return errors

        # Validate individual image results
        successful_images = []
        failed_images = []

        for i, img_data in enumerate(generated_images):
            # Convert dict to ImageGenerationResult if needed
            if isinstance(img_data, dict):
                try:
                    img_result = ImageGenerationResult(**img_data)
                except Exception as e:
                    errors.append(ValidationError(f"image_{i}", f"Invalid image result format: {str(e)}", "error"))
                    continue
            else:
                img_result = img_data

            # Validate image result structure
            if not hasattr(img_result, 'panel_id') or not img_result.panel_id:
                errors.append(ValidationError(f"image_{i}", f"Image {i}: Missing or empty panel_id", "error"))

            if not hasattr(img_result, 'success'):
                errors.append(ValidationError(f"image_{i}", f"Image {i}: Missing success status", "error"))
                continue

            # Track successful/failed images
            if img_result.success:
                successful_images.append(img_result)

                # Validate successful image data
                if not hasattr(img_result, 'image_url') or not img_result.image_url:
                    errors.append(ValidationError(f"image_{i}", f"Image {i}: Missing image_url for successful generation", "error"))

                # Check quality score
                if hasattr(img_result, 'quality_score') and img_result.quality_score is not None:
                    if not (0 <= img_result.quality_score <= 1):
                        errors.append(ValidationError(f"image_{i}", f"Image {i}: Quality score out of range [0,1]: {img_result.quality_score}", "warning"))
            else:
                failed_images.append(img_result)

                # Failed images should have error message
                if not hasattr(img_result, 'error_message') or not img_result.error_message:
                    errors.append(ValidationError(f"image_{i}", f"Image {i}: Missing error_message for failed generation", "warning"))

        # Check overall success rate
        total_images = len(generated_images)
        success_rate = len(successful_images) / total_images if total_images > 0 else 0

        if success_rate < self.validation_thresholds["minimum_success_rate"]:
            errors.append(ValidationError(
                "success_rate",
                f"Low image generation success rate: {success_rate:.2%} < {self.validation_thresholds['minimum_success_rate']:.2%}",
                "error"
            ))

        # Validate total counts consistency
        total_generated = output_data.get("total_images_generated", 0)
        successful_count = output_data.get("successful_generations", 0)
        failed_count = output_data.get("failed_generations", 0)

        if total_generated != total_images:
            errors.append(ValidationError("count_mismatch", f"total_images_generated ({total_generated}) != len(generated_images) ({total_images})", "warning"))

        if successful_count != len(successful_images):
            errors.append(ValidationError("count_mismatch", f"successful_generations ({successful_count}) != actual successful count ({len(successful_images)})", "warning"))

        if failed_count != len(failed_images):
            errors.append(ValidationError("count_mismatch", f"failed_generations ({failed_count}) != actual failed count ({len(failed_images)})", "warning"))

        return errors

    async def _validate_quality_analysis(self, output_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate quality analysis data."""
        errors = []

        quality_analysis = output_data.get("quality_analysis", {})

        if not quality_analysis:
            errors.append(ValidationError("quality_analysis", "Missing quality_analysis data", "error"))
            return errors

        # Validate success rate
        success_rate = quality_analysis.get("success_rate")
        if success_rate is None:
            errors.append(ValidationError("quality_analysis.success_rate", "Missing success_rate in quality_analysis", "error"))
        elif not (0 <= success_rate <= 1):
            errors.append(ValidationError("quality_analysis.success_rate", f"Success rate out of range [0,1]: {success_rate}", "error"))

        # Validate average quality score
        avg_quality = quality_analysis.get("average_quality_score")
        if avg_quality is None:
            errors.append(ValidationError("quality_analysis.average_quality_score", "Missing average_quality_score in quality_analysis", "error"))
        elif not (0 <= avg_quality <= 1):
            errors.append(ValidationError("quality_analysis.average_quality_score", f"Average quality score out of range [0,1]: {avg_quality}", "error"))
        elif avg_quality < self.validation_thresholds["minimum_quality_score"]:
            errors.append(ValidationError(
                "quality_analysis.average_quality_score",
                f"Average quality score below threshold: {avg_quality:.3f} < {self.validation_thresholds['minimum_quality_score']:.3f}",
                "warning"
            ))

        # Validate generation time
        avg_time = quality_analysis.get("average_generation_time_ms")
        if avg_time is not None and avg_time > self.validation_thresholds["maximum_generation_time"]:
            errors.append(ValidationError(
                "quality_analysis.average_generation_time_ms",
                f"Average generation time exceeds threshold: {avg_time}ms > {self.validation_thresholds['maximum_generation_time']}ms",
                "warning"
            ))

        # Validate recommendations exist
        recommendations = quality_analysis.get("recommendations", [])
        if not isinstance(recommendations, list):
            errors.append(ValidationError("quality_analysis.recommendations", "recommendations must be a list", "warning"))

        return errors

    async def _validate_consistency_report(self, output_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate consistency report data."""
        errors = []

        consistency_report = output_data.get("consistency_report", {})

        if not consistency_report:
            errors.append(ValidationError("consistency_report", "Missing consistency_report data", "error"))
            return errors

        # Validate overall consistency score
        overall_score = consistency_report.get("overall_consistency_score")
        if overall_score is None:
            errors.append(ValidationError("consistency_report.overall_consistency_score", "Missing overall_consistency_score", "error"))
        elif not (0 <= overall_score <= 1):
            errors.append(ValidationError("consistency_report.overall_consistency_score", f"Overall consistency score out of range [0,1]: {overall_score}", "error"))
        elif overall_score < self.validation_thresholds["minimum_consistency_score"]:
            errors.append(ValidationError(
                "consistency_report.overall_consistency_score",
                f"Overall consistency score below threshold: {overall_score:.3f} < {self.validation_thresholds['minimum_consistency_score']:.3f}",
                "warning"
            ))

        # Validate character consistency
        char_consistency = consistency_report.get("character_consistency", {})
        if char_consistency:
            char_score = char_consistency.get("overall_character_consistency", 0)
            if char_score < 0.6:
                errors.append(ValidationError(
                    "consistency_report.character_consistency",
                    f"Character consistency below recommended level: {char_score:.3f}",
                    "warning"
                ))

        # Validate style consistency
        style_consistency = consistency_report.get("style_consistency", {})
        if style_consistency:
            style_score = style_consistency.get("style_consistency_score", 0)
            if style_score < 0.6:
                errors.append(ValidationError(
                    "consistency_report.style_consistency",
                    f"Style consistency below recommended level: {style_score:.3f}",
                    "warning"
                ))

        return errors

    async def _validate_generation_statistics(self, output_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate generation statistics."""
        errors = []

        generation_stats = output_data.get("generation_stats", {})

        if not generation_stats:
            errors.append(ValidationError("generation_stats", "Missing generation_stats data", "error"))
            return errors

        # Validate basic statistics
        total_generated = generation_stats.get("total_generated", 0)
        successful_generations = generation_stats.get("successful_generations", 0)

        if total_generated < 0:
            errors.append(ValidationError("generation_stats.total_generated", "total_generated cannot be negative", "error"))

        if successful_generations < 0:
            errors.append(ValidationError("generation_stats.successful_generations", "successful_generations cannot be negative", "error"))

        if successful_generations > total_generated:
            errors.append(ValidationError("generation_stats.consistency", "successful_generations cannot exceed total_generated", "error"))

        # Validate cache statistics
        cache_hits = generation_stats.get("cache_hits", 0)
        if cache_hits < 0:
            errors.append(ValidationError("generation_stats.cache_hits", "cache_hits cannot be negative", "error"))

        if cache_hits > total_generated:
            errors.append(ValidationError("generation_stats.cache_hits", "cache_hits cannot exceed total_generated", "error"))

        # Validate average generation time
        avg_time = generation_stats.get("average_generation_time", 0)
        if avg_time < 0:
            errors.append(ValidationError("generation_stats.average_generation_time", "average_generation_time cannot be negative", "error"))

        return errors

    async def _validate_cache_utilization(self, output_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate cache utilization data."""
        errors = []

        cache_utilization = output_data.get("cache_utilization", {})

        if not cache_utilization:
            errors.append(ValidationError("cache_utilization", "Missing cache_utilization data", "warning"))
            return errors

        # Validate cache hit rate
        cache_hit_rate = cache_utilization.get("cache_hit_rate")
        if cache_hit_rate is not None:
            if not (0 <= cache_hit_rate <= 1):
                errors.append(ValidationError("cache_utilization.cache_hit_rate", f"Cache hit rate out of range [0,1]: {cache_hit_rate}", "error"))

        # Validate cache efficiency
        cache_efficiency = cache_utilization.get("cache_efficiency")
        if cache_efficiency is not None:
            valid_efficiency_levels = ["low", "medium", "high"]
            if cache_efficiency not in valid_efficiency_levels:
                errors.append(ValidationError("cache_utilization.cache_efficiency", f"Invalid cache efficiency level: {cache_efficiency}", "warning"))

        # Validate cache counts
        total_cache_entries = cache_utilization.get("total_cache_entries", 0)
        cache_hits = cache_utilization.get("cache_hits", 0)
        total_requests = cache_utilization.get("total_requests", 0)

        if total_cache_entries < 0:
            errors.append(ValidationError("cache_utilization.total_cache_entries", "total_cache_entries cannot be negative", "error"))

        if cache_hits < 0:
            errors.append(ValidationError("cache_utilization.cache_hits", "cache_hits cannot be negative", "error"))

        if total_requests < 0:
            errors.append(ValidationError("cache_utilization.total_requests", "total_requests cannot be negative", "error"))

        if cache_hits > total_requests:
            errors.append(ValidationError("cache_utilization.consistency", "cache_hits cannot exceed total_requests", "error"))

        return errors

    async def _validate_performance_metrics(self, output_data: Dict[str, Any]) -> List[ValidationError]:
        """Validate performance metrics and generate warnings."""
        warnings = []

        # Check parallel efficiency
        parallel_efficiency = output_data.get("parallel_efficiency_score", 0)
        if parallel_efficiency < self.validation_thresholds["minimum_parallel_efficiency"]:
            warnings.append(ValidationError(
                "performance.parallel_efficiency",
                f"Low parallel efficiency: {parallel_efficiency:.3f} < {self.validation_thresholds['minimum_parallel_efficiency']:.3f}",
                "warning"
            ))

        # Check generation time
        avg_generation_time = output_data.get("average_generation_time", 0)
        if avg_generation_time > self.validation_thresholds["maximum_generation_time"]:
            warnings.append(ValidationError(
                "performance.generation_time",
                f"High average generation time: {avg_generation_time:.0f}ms > {self.validation_thresholds['maximum_generation_time']}ms",
                "warning"
            ))

        # Check cache utilization
        cache_utilization = output_data.get("cache_utilization", {})
        cache_hit_rate = cache_utilization.get("cache_hit_rate", 0)
        if cache_hit_rate < self.validation_thresholds["minimum_cache_efficiency"]:
            warnings.append(ValidationError(
                "performance.cache_efficiency",
                f"Low cache hit rate: {cache_hit_rate:.3f} < {self.validation_thresholds['minimum_cache_efficiency']:.3f}",
                "warning"
            ))

        return warnings

    async def _validate_phase_specific(self, output_data: Dict[str, Any]) -> List[ValidationError]:
        """Phase 5 specific validation."""
        errors = []

        # Check scene image mapping
        scene_mapping = output_data.get("scene_image_mapping", {})
        if scene_mapping:
            scene_to_images = scene_mapping.get("scene_to_images", {})
            if not scene_to_images:
                errors.append(ValidationError("scene_image_mapping", "No scene to image mappings found", "warning"))

            # Validate mapping completeness
            total_mapped_scenes = scene_mapping.get("total_mapped_scenes", 0)
            if total_mapped_scenes == 0:
                errors.append(ValidationError("scene_image_mapping.completeness", "No scenes mapped to images", "warning"))

        # Check AI response metadata
        ai_metadata = output_data.get("ai_response_metadata")
        if ai_metadata:
            if "original_response" not in ai_metadata:
                errors.append(ValidationError("ai_response_metadata", "Missing original_response in AI metadata", "warning"))

        # Validate quality metrics
        quality_metrics = output_data.get("quality_metrics", {})
        if quality_metrics:
            for metric_name, metric_value in quality_metrics.items():
                if not isinstance(metric_value, (int, float)):
                    errors.append(ValidationError(f"quality_metrics.{metric_name}", f"Quality metric {metric_name} must be numeric", "warning"))
                elif metric_value < 0 or metric_value > 1:
                    errors.append(ValidationError(f"quality_metrics.{metric_name}", f"Quality metric {metric_name} out of range [0,1]: {metric_value}", "warning"))

        return errors

    def calculate_quality_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate overall quality score for Phase 5 output."""

        scores = {}

        # Completeness score
        generated_images = output_data.get("generated_images", [])
        total_expected = output_data.get("total_images_generated", len(generated_images))
        completeness_score = len(generated_images) / max(1, total_expected)
        scores["completeness"] = min(1.0, completeness_score)

        # Accuracy score (based on success rate)
        quality_analysis = output_data.get("quality_analysis", {})
        success_rate = quality_analysis.get("success_rate", 0)
        scores["accuracy"] = success_rate

        # Consistency score
        consistency_report = output_data.get("consistency_report", {})
        consistency_score = consistency_report.get("overall_consistency_score", 0)
        scores["consistency"] = consistency_score

        # Format compliance score
        format_score = 1.0  # Start with perfect score
        # Deduct for missing required fields
        required_fields = ["generated_images", "quality_analysis", "consistency_report"]
        missing_fields = sum(1 for field in required_fields if field not in output_data)
        format_score = max(0.0, 1.0 - (missing_fields * 0.2))
        scores["format_compliance"] = format_score

        # Efficiency score
        parallel_efficiency = output_data.get("parallel_efficiency_score", 0)
        cache_utilization = output_data.get("cache_utilization", {})
        cache_hit_rate = cache_utilization.get("cache_hit_rate", 0)
        efficiency_score = (parallel_efficiency + cache_hit_rate) / 2
        scores["efficiency"] = efficiency_score

        # Calculate weighted average
        total_score = sum(scores[key] * self.quality_weights[key] for key in scores)

        return round(min(1.0, max(0.0, total_score)), 3)

    def get_validation_summary(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive validation summary for Phase 5."""

        summary = {
            "phase": 5,
            "phase_name": "画像生成",
            "overall_quality_score": self.calculate_quality_score(output_data),
            "validation_details": {}
        }

        # Generation statistics summary
        generated_images = output_data.get("generated_images", [])
        successful_count = len([img for img in generated_images if getattr(img, 'success', False)])

        summary["validation_details"] = {
            "total_images": len(generated_images),
            "successful_images": successful_count,
            "success_rate": successful_count / len(generated_images) if generated_images else 0,
            "average_quality": self._calculate_average_quality(generated_images),
            "consistency_score": output_data.get("consistency_report", {}).get("overall_consistency_score", 0),
            "parallel_efficiency": output_data.get("parallel_efficiency_score", 0),
            "cache_efficiency": output_data.get("cache_utilization", {}).get("cache_hit_rate", 0)
        }

        return summary

    def _calculate_average_quality(self, generated_images: List) -> float:
        """Calculate average quality score from generated images."""

        quality_scores = []
        for img in generated_images:
            if hasattr(img, 'success') and img.success:
                if hasattr(img, 'quality_score') and img.quality_score is not None:
                    quality_scores.append(img.quality_score)

        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
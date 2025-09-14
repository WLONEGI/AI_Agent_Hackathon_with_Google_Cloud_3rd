"""Phase 5: Image Generation - Style Processing and Analysis."""

from typing import Dict, Any, List, Optional, Union
import statistics
from ..schemas import (
    StyleTemplate,
    StyleParameters,
    QualityCriteria,
    ImageGenerationResult,
    QualityAnalysis,
    ConsistencyAnalysis,
    CacheUtilization,
    ParallelEfficiency,
    EmphasisType,
    EnergyLevel,
    LineWeight,
    ConsistencyLevel,
    GenerationStatistics
)

class StyleProcessor:
    """Style processing and analysis for image generation."""

    def __init__(self):
        """Initialize style processor with templates and criteria."""

        # Default style templates
        self.style_templates = {
            EmphasisType.CHARACTER_FOCUS: StyleTemplate(
                name="character_focus",
                base_style="manga style, clean lines, detailed character",
                emphasis="character expression and detail",
                background="simple or blurred background",
                suitable_genres=["romance", "drama", "slice_of_life"],
                energy_level=EnergyLevel.GENTLE,
                line_weight=LineWeight.SOFT
            ),
            EmphasisType.ENVIRONMENT_FOCUS: StyleTemplate(
                name="environment_focus",
                base_style="manga style, detailed environment",
                emphasis="atmospheric background and setting",
                background="detailed environmental elements",
                suitable_genres=["adventure", "fantasy", "sci-fi"],
                energy_level=EnergyLevel.MODERATE,
                line_weight=LineWeight.STANDARD
            ),
            EmphasisType.ACTION_SCENE: StyleTemplate(
                name="action_scene",
                base_style="dynamic manga style, motion effects",
                emphasis="movement and energy",
                background="dynamic backgrounds with motion blur",
                suitable_genres=["action", "sports", "shounen"],
                energy_level=EnergyLevel.HIGH,
                line_weight=LineWeight.BOLD
            ),
            EmphasisType.EMOTIONAL_SCENE: StyleTemplate(
                name="emotional_scene",
                base_style="soft manga style, emotional lighting",
                emphasis="mood and atmosphere",
                background="mood-supporting backgrounds",
                suitable_genres=["romance", "drama", "psychological"],
                energy_level=EnergyLevel.GENTLE,
                line_weight=LineWeight.SOFT
            )
        }

        # Quality assessment criteria
        self.quality_criteria = QualityCriteria(
            character_accuracy=0.25,
            style_consistency=0.20,
            composition_quality=0.20,
            technical_quality=0.15,
            narrative_clarity=0.10,
            artistic_appeal=0.10
        )

    def get_style_template(self, emphasis_type: EmphasisType) -> StyleTemplate:
        """Get style template for emphasis type."""
        return self.style_templates.get(emphasis_type, self.style_templates[EmphasisType.BALANCED])

    def analyze_generation_quality(
        self,
        generation_results: List[ImageGenerationResult]
    ) -> QualityAnalysis:
        """Analyze overall generation quality."""

        successful_results = [r for r in generation_results if r.success]
        failed_results = [r for r in generation_results if not r.success]

        if not generation_results:
            return QualityAnalysis(
                success_rate=0.0,
                average_quality_score=0.0,
                average_generation_time_ms=0.0,
                quality_distribution={},
                retry_statistics={},
                failure_analysis={},
                total_generated=0,
                successful_generations=0,
                failed_generations=0,
                recommendations=["No generation results to analyze"]
            )

        # Calculate success rate
        success_rate = len(successful_results) / len(generation_results)

        # Calculate average quality score
        quality_scores = [r.quality_score for r in successful_results if r.quality_score]
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        # Calculate average generation time
        generation_times = [r.generation_time_ms for r in successful_results if r.generation_time_ms]
        average_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0

        # Quality distribution
        quality_distribution = {"high": 0, "medium": 0, "low": 0}
        for score in quality_scores:
            if score >= 0.8:
                quality_distribution["high"] += 1
            elif score >= 0.6:
                quality_distribution["medium"] += 1
            else:
                quality_distribution["low"] += 1

        # Retry analysis
        retry_stats = {"no_retry": 0, "single_retry": 0, "multiple_retry": 0}
        for result in generation_results:
            if result.retry_count == 0:
                retry_stats["no_retry"] += 1
            elif result.retry_count == 1:
                retry_stats["single_retry"] += 1
            else:
                retry_stats["multiple_retry"] += 1

        # Failure analysis
        failure_reasons = {}
        for failed in failed_results:
            reason = failed.error_message or "Unknown error"
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

        # Generate recommendations
        recommendations = self._generate_quality_recommendations(
            success_rate, average_quality, failure_reasons
        )

        return QualityAnalysis(
            success_rate=round(success_rate, 3),
            average_quality_score=round(average_quality, 3),
            average_generation_time_ms=round(average_generation_time, 0),
            quality_distribution=quality_distribution,
            retry_statistics=retry_stats,
            failure_analysis=failure_reasons,
            total_generated=len(generation_results),
            successful_generations=len(successful_results),
            failed_generations=len(failed_results),
            recommendations=recommendations
        )

    def _generate_quality_recommendations(
        self,
        success_rate: float,
        average_quality: float,
        failure_reasons: Dict[str, int]
    ) -> List[str]:
        """Generate quality improvement recommendations."""

        recommendations = []

        if success_rate < 0.8:
            recommendations.append("生成成功率の改善が必要（プロンプトの最適化を推奨）")

        if average_quality < 0.7:
            recommendations.append("品質スコアの向上が必要（スタイルパラメータの調整を推奨）")

        # Analyze common failure reasons
        if "validation failed" in str(failure_reasons).lower():
            recommendations.append("バリデーション基準の見直しまたはプロンプト改善")

        if "generation failed" in str(failure_reasons).lower():
            recommendations.append("生成パラメータの最適化またはリトライ戦略の改善")

        if not recommendations:
            recommendations.append("現在の品質基準を満たしています")

        return recommendations

    def generate_consistency_report(
        self,
        generation_results: List[ImageGenerationResult],
        phase2_result: Dict[str, Any]
    ) -> ConsistencyAnalysis:
        """Generate comprehensive consistency analysis."""

        successful_results = [r for r in generation_results if r.success]

        # Character consistency analysis
        characters = phase2_result.get("characters", [])
        character_consistency = self._analyze_character_consistency(successful_results, characters)

        # Style consistency analysis
        style_consistency = self._analyze_style_consistency(successful_results)

        # Quality consistency analysis
        quality_consistency = self._analyze_quality_consistency(successful_results)

        # Calculate overall consistency score
        overall_score = self._calculate_overall_consistency_score(
            character_consistency, style_consistency, quality_consistency
        )

        # Generate recommendations
        recommendations = self._generate_consistency_recommendations(
            character_consistency, style_consistency, quality_consistency
        )

        return ConsistencyAnalysis(
            character_consistency=character_consistency,
            style_consistency=style_consistency,
            quality_consistency=quality_consistency,
            overall_consistency_score=overall_score,
            consistency_recommendations=recommendations
        )

    def _analyze_character_consistency(
        self,
        generation_results: List[ImageGenerationResult],
        characters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze character visual consistency across images."""

        character_scores = {}

        for char in characters:
            char_name = char.get("name", "")

            # Find images featuring this character (simple heuristic)
            char_images = [
                r for r in generation_results
                if char_name.lower() in r.panel_id.lower()
            ]

            if char_images:
                # Calculate consistency score based on quality scores
                quality_scores = [r.quality_score for r in char_images if r.quality_score]
                if quality_scores:
                    avg_quality = sum(quality_scores) / len(quality_scores)
                    quality_variance = statistics.variance(quality_scores) if len(quality_scores) > 1 else 0
                    consistency_score = avg_quality * (1 - min(0.3, quality_variance))

                    character_scores[char_name] = {
                        "consistency_score": round(consistency_score, 3),
                        "image_count": len(char_images),
                        "average_quality": round(avg_quality, 3),
                        "quality_variance": round(quality_variance, 3)
                    }

        # Overall character consistency
        if character_scores:
            overall_score = sum(data["consistency_score"] for data in character_scores.values()) / len(character_scores)
        else:
            overall_score = 0.0

        return {
            "character_scores": character_scores,
            "overall_character_consistency": round(overall_score, 3),
            "characters_analyzed": len(character_scores),
            "consistency_issues": self._identify_character_consistency_issues(character_scores)
        }

    def _identify_character_consistency_issues(
        self,
        character_scores: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Identify character consistency issues."""

        issues = []

        for char_name, data in character_scores.items():
            consistency_score = data.get("consistency_score", 0)
            quality_variance = data.get("quality_variance", 0)

            if consistency_score < 0.7:
                issues.append(f"{char_name}の視覚的一貫性が低い（スコア: {consistency_score:.2f}）")

            if quality_variance > 0.1:
                issues.append(f"{char_name}の品質にばらつきがある（分散: {quality_variance:.2f}）")

        return issues

    def _analyze_style_consistency(
        self,
        generation_results: List[ImageGenerationResult]
    ) -> Dict[str, Any]:
        """Analyze style consistency across all images."""

        quality_scores = [r.quality_score for r in generation_results if r.quality_score]

        if not quality_scores:
            return {"style_consistency_score": 0.0, "analysis": "No quality scores available"}

        # Use quality score variance as a proxy for style consistency
        avg_quality = sum(quality_scores) / len(quality_scores)
        quality_variance = statistics.variance(quality_scores) if len(quality_scores) > 1 else 0

        # Style consistency is inversely related to variance
        style_consistency_score = max(0.0, 1.0 - quality_variance * 2)

        return {
            "style_consistency_score": round(style_consistency_score, 3),
            "average_quality": round(avg_quality, 3),
            "quality_variance": round(quality_variance, 3),
            "style_uniformity": self._classify_consistency_level(style_consistency_score),
            "images_analyzed": len(quality_scores)
        }

    def _analyze_quality_consistency(
        self,
        generation_results: List[ImageGenerationResult]
    ) -> Dict[str, Any]:
        """Analyze quality consistency across images."""

        quality_scores = [r.quality_score for r in generation_results if r.quality_score]
        generation_times = [r.generation_time_ms for r in generation_results if r.generation_time_ms]

        if not quality_scores:
            return {"quality_consistency_score": 0.0}

        # Calculate quality statistics
        avg_quality = sum(quality_scores) / len(quality_scores)
        min_quality = min(quality_scores)
        max_quality = max(quality_scores)
        quality_range = max_quality - min_quality

        # Quality consistency score (lower range = higher consistency)
        quality_consistency_score = max(0.0, 1.0 - quality_range)

        # Generation time consistency
        avg_time = sum(generation_times) / len(generation_times) if generation_times else 0

        return {
            "quality_consistency_score": round(quality_consistency_score, 3),
            "average_quality": round(avg_quality, 3),
            "quality_range": round(quality_range, 3),
            "min_quality": round(min_quality, 3),
            "max_quality": round(max_quality, 3),
            "average_generation_time_ms": round(avg_time, 0),
            "quality_stability": self._classify_quality_stability(quality_range)
        }

    def _classify_consistency_level(self, score: float) -> str:
        """Classify consistency level based on score."""
        if score > 0.8:
            return "high"
        elif score > 0.6:
            return "medium"
        else:
            return "low"

    def _classify_quality_stability(self, quality_range: float) -> str:
        """Classify quality stability based on range."""
        if quality_range < 0.2:
            return "stable"
        elif quality_range < 0.4:
            return "moderate"
        else:
            return "variable"

    def _calculate_overall_consistency_score(
        self,
        character_consistency: Dict[str, Any],
        style_consistency: Dict[str, Any],
        quality_consistency: Dict[str, Any]
    ) -> float:
        """Calculate overall consistency score."""

        scores = []

        char_score = character_consistency.get("overall_character_consistency", 0.0)
        if char_score > 0:
            scores.append(char_score * 0.4)  # 40% weight

        style_score = style_consistency.get("style_consistency_score", 0.0)
        scores.append(style_score * 0.35)  # 35% weight

        quality_score = quality_consistency.get("quality_consistency_score", 0.0)
        scores.append(quality_score * 0.25)  # 25% weight

        return round(sum(scores), 3)

    def _generate_consistency_recommendations(
        self,
        character_consistency: Dict[str, Any],
        style_consistency: Dict[str, Any],
        quality_consistency: Dict[str, Any]
    ) -> List[str]:
        """Generate consistency improvement recommendations."""

        recommendations = []

        # Character consistency recommendations
        char_score = character_consistency.get("overall_character_consistency", 0.0)
        if char_score < 0.7:
            recommendations.append("キャラクターの視覚的一貫性を向上（参考画像やスタイルガイドの活用）")

        # Style consistency recommendations
        style_score = style_consistency.get("style_consistency_score", 0.0)
        if style_score < 0.7:
            recommendations.append("スタイルの統一性を改善（プロンプトテンプレートの標準化）")

        # Quality consistency recommendations
        quality_range = quality_consistency.get("quality_range", 0.0)
        if quality_range > 0.3:
            recommendations.append("品質のばらつきを軽減（生成パラメータの最適化）")

        if not recommendations:
            recommendations.append("現在の一貫性レベルは良好です")

        return recommendations

    def create_scene_image_mapping(
        self,
        generation_results: List[ImageGenerationResult],
        phase4_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create mapping between scenes and generated images."""

        successful_results = [r for r in generation_results if r.success]

        # Get panel specifications from phase 4
        panel_specifications = phase4_result.get("panel_specifications", [])

        # Create mapping
        scene_mapping = {}
        page_mapping = {}

        for result in successful_results:
            panel_id = result.panel_id

            # Find corresponding panel specification
            panel_spec = next(
                (spec for spec in panel_specifications if spec.get("panel_id") == panel_id),
                {}
            )

            scene_number = panel_spec.get("scene_number", 0)
            page_number = panel_spec.get("page_number", 0)

            # Add to scene mapping
            if scene_number not in scene_mapping:
                scene_mapping[scene_number] = []

            scene_mapping[scene_number].append({
                "panel_id": panel_id,
                "image_url": result.image_url,
                "thumbnail_url": result.thumbnail_url,
                "quality_score": result.quality_score,
                "panel_spec": panel_spec
            })

            # Add to page mapping
            if page_number not in page_mapping:
                page_mapping[page_number] = []

            page_mapping[page_number].append({
                "panel_id": panel_id,
                "image_url": result.image_url,
                "thumbnail_url": result.thumbnail_url,
                "quality_score": result.quality_score,
                "panel_number": panel_spec.get("panel_number", 0)
            })

        # Sort page mappings by panel number
        for page_images in page_mapping.values():
            page_images.sort(key=lambda x: x.get("panel_number", 0))

        return {
            "scene_to_images": scene_mapping,
            "page_to_images": page_mapping,
            "total_mapped_scenes": len(scene_mapping),
            "total_mapped_pages": len(page_mapping),
            "images_per_scene": {
                scene: len(images) for scene, images in scene_mapping.items()
            },
            "images_per_page": {
                page: len(images) for page, images in page_mapping.items()
            }
        }

    def calculate_parallel_efficiency_score(
        self,
        generation_tasks_count: int,
        generation_results: List[ImageGenerationResult],
        max_concurrent_generations: int
    ) -> float:
        """Calculate parallel processing efficiency score."""

        if not generation_results:
            return 0.0

        # Calculate theoretical vs actual time
        generation_times = [r.generation_time_ms for r in generation_results if r.generation_time_ms]
        if not generation_times:
            return 0.0

        avg_single_time = sum(generation_times) / len(generation_times)

        # Theoretical sequential time
        theoretical_sequential_time = generation_tasks_count * avg_single_time

        # Actual parallel time (use max generation time as proxy)
        actual_parallel_time = max(generation_times)

        # Efficiency score
        if theoretical_sequential_time == 0:
            return 0.0

        efficiency_score = 1.0 - (actual_parallel_time / theoretical_sequential_time)

        # Account for concurrency benefits
        concurrency_benefit = min(1.0, max_concurrent_generations / generation_tasks_count)
        adjusted_score = efficiency_score * (0.5 + 0.5 * concurrency_benefit)

        return round(max(0.0, min(1.0, adjusted_score)), 3)

    def calculate_cache_utilization(
        self,
        generation_stats: GenerationStatistics
    ) -> CacheUtilization:
        """Calculate cache utilization statistics."""

        total_requests = generation_stats.total_generated
        cache_hits = generation_stats.cache_hits

        cache_hit_rate = cache_hits / total_requests if total_requests > 0 else 0.0

        # Determine efficiency level
        if cache_hit_rate > 0.3:
            efficiency = ConsistencyLevel.HIGH
        elif cache_hit_rate > 0.1:
            efficiency = ConsistencyLevel.MEDIUM
        else:
            efficiency = ConsistencyLevel.LOW

        return CacheUtilization(
            cache_hit_rate=round(cache_hit_rate, 3),
            total_cache_entries=0,  # Would need to be provided by cache manager
            cache_hits=cache_hits,
            total_requests=total_requests,
            cache_efficiency=efficiency
        )

    def validate_generated_image(self, result: ImageGenerationResult) -> Dict[str, Any]:
        """Validate generated image quality and content."""

        if not result.image_url:
            return {"valid": False, "reason": "No image URL provided"}

        if result.quality_score and result.quality_score < 0.6:
            return {"valid": False, "reason": "Quality score too low"}

        # Simulate content validation (would be replaced with actual image analysis)
        import random
        if random.random() > 0.95:  # 5% validation failure rate
            return {"valid": False, "reason": "Content validation failed"}

        return {"valid": True, "reason": "Validation passed"}

    def get_quality_criteria(self) -> QualityCriteria:
        """Get current quality criteria."""
        return self.quality_criteria

    def update_quality_criteria(self, new_criteria: QualityCriteria):
        """Update quality criteria."""
        self.quality_criteria = new_criteria
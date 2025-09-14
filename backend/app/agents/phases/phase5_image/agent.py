"""Phase 5: Image Generation Agent - Main Orchestration Logic."""

import json
import time
from typing import Dict, Any, Optional, List
from uuid import UUID

from app.agents.base.agent import BaseAgent
from app.core.config import settings
from app.services.vertex_ai_service import VertexAIService

from .validator import Phase5Validator
from .schemas import (
    ImageGenerationInput,
    ImageGenerationOutput,
    ImageGenerationTask,
    ImageGenerationResult,
    QualityAnalysis,
    ConsistencyAnalysis,
    CacheUtilization,
    ParallelEfficiency,
    GenerationStatistics
)
from .processors import ImageGenerator, StyleProcessor

class Phase5ImageAgent(BaseAgent):
    """Agent for Phase 5: Scene Image Generation with parallel processing."""

    def __init__(self, phase_number: int = 5, phase_name: str = "シーン画像生成", timeout_seconds: int = None):
        """Initialize Phase 5 Image Generation Agent."""

        if timeout_seconds is None:
            timeout_seconds = 120  # Default timeout

        super().__init__(
            phase_number=phase_number,
            phase_name=phase_name,
            timeout_seconds=timeout_seconds
        )

        # Initialize processors
        try:
            max_parallel = getattr(settings.ai_models, 'max_parallel_image_generation', 3)
        except (AttributeError, TypeError):
            max_parallel = 3

        self.image_generator = ImageGenerator(max_concurrent_generations=max_parallel)
        self.style_processor = StyleProcessor()

        # Vertex AI service for prompt generation
        self.vertex_ai = VertexAIService()

        # Initialize structured prompts if available
        try:
            from .prompts import ImageGenerationPrompts
            self.prompts = ImageGenerationPrompts()
        except ImportError:
            self.prompts = None

    def _create_validator(self) -> Phase5Validator:
        """Create phase-specific validator for Phase 5."""
        return Phase5Validator()

    async def _generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate AI prompt for Phase 5 image generation."""

        if self.prompts:
            return self.prompts.get_main_prompt(
                input_data=input_data,
                previous_results=previous_results
            )

        # Fallback prompt generation
        story_data = previous_results.get(3, {}) if previous_results else {}
        character_data = previous_results.get(2, {}) if previous_results else {}
        panels = input_data.get("panels", [])

        prompt_parts = [
            "Generate manga-style images for the following panels:",
            f"Total panels to generate: {len(panels)}",
            ""
        ]

        # Add character information if available
        if character_data:
            prompt_parts.extend([
                "Character Information:",
                str(character_data),
                ""
            ])

        # Add story context if available
        if story_data:
            prompt_parts.extend([
                "Story Context:",
                str(story_data),
                ""
            ])

        # Add panel details
        prompt_parts.append("Panel Details:")
        for i, panel in enumerate(panels):
            prompt_parts.append(f"Panel {i+1}: {panel}")

        return "\n".join(prompt_parts)

    async def _process_ai_response(
        self,
        ai_response: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process AI response into structured Phase 5 output."""

        try:
            # Parse AI response if it's JSON
            if ai_response.strip().startswith('{'):
                response_data = json.loads(ai_response)
            else:
                response_data = {"raw_response": ai_response}

            # Get previous results from accumulated context
            previous_results = input_data.get("accumulated_context", {})

            if not previous_results or not all(i in previous_results for i in [1, 2, 3, 4]):
                raise ValueError("Phases 1-4 results required for image generation")

            # Extract session information from input_data
            session_id = input_data.get("session_id", "test_session")
            if isinstance(session_id, str) and session_id != "test_session":
                try:
                    session_uuid = UUID(session_id)
                except ValueError:
                    session_uuid = UUID('12345678-1234-5678-9012-123456789abc')
            else:
                session_uuid = UUID('12345678-1234-5678-9012-123456789abc')

            # Extract previous phase results
            phase1_result = previous_results[1]
            phase2_result = previous_results[2]
            phase3_result = previous_results[3]
            phase4_result = previous_results[4]

            # Create image generation tasks
            generation_tasks = await self.image_generator.create_generation_tasks(
                phase1_result, phase2_result, phase3_result, phase4_result
            )

            self.logger.info(f"Created {len(generation_tasks)} generation tasks for session {session_id}")

            # Execute parallel generation with semaphore control
            generation_results = await self.image_generator.execute_parallel_generation(
                generation_tasks, session_uuid
            )

            # Process and validate results
            processed_results = await self._process_generation_results(
                generation_results, generation_tasks, {
                    "previous_results": previous_results,
                    "session_id": session_id
                }
            )

            # Add AI response metadata
            processed_results["ai_response_metadata"] = {
                "original_response": ai_response,
                "processed_data": response_data,
                "processing_method": "phase5_image_generation"
            }

            self.logger.info(
                f"Completed Phase 5 image generation for session {session_id}",
                extra={
                    "successful": processed_results.get("successful_generations", 0),
                    "failed": processed_results.get("failed_generations", 0)
                }
            )

            return processed_results

        except Exception as e:
            self.logger.error(f"Error in Phase 5 processing: {str(e)}")
            # Fallback: return minimal structure
            return {
                "generated_images": [],
                "scene_image_mapping": {},
                "quality_analysis": QualityAnalysis(
                    success_rate=0.0,
                    average_quality_score=0.0,
                    average_generation_time_ms=0.0,
                    quality_distribution={},
                    retry_statistics={},
                    failure_analysis={},
                    total_generated=0,
                    successful_generations=0,
                    failed_generations=0,
                    recommendations=[f"Processing failed: {str(e)}"]
                ).dict(),
                "consistency_report": ConsistencyAnalysis(
                    character_consistency={},
                    style_consistency={},
                    quality_consistency={},
                    overall_consistency_score=0.0,
                    consistency_recommendations=[f"Processing failed: {str(e)}"]
                ).dict(),
                "generation_stats": GenerationStatistics().dict(),
                "total_images_generated": 0,
                "successful_generations": 0,
                "failed_generations": 0,
                "average_generation_time": 0.0,
                "parallel_efficiency_score": 0.0,
                "cache_utilization": CacheUtilization(
                    cache_hit_rate=0.0,
                    total_cache_entries=0,
                    cache_hits=0,
                    total_requests=0,
                    cache_efficiency="low"
                ).dict(),
                "ai_response_metadata": {
                    "original_response": ai_response,
                    "error": str(e)
                }
            }

    async def _process_from_previous_results(
        self,
        previous_results: Dict[int, Any],
        session_id: str,
        response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process generation based on previous phase results."""

        if not all(i in previous_results for i in [1, 2, 3, 4]):
            raise ValueError("Phases 1-4 results required for image generation")

        # Extract previous phase results
        phase1_result = previous_results[1]
        phase2_result = previous_results[2]
        phase3_result = previous_results[3]
        phase4_result = previous_results[4]

        # Create image generation tasks
        generation_tasks = await self.image_generator.create_generation_tasks(
            phase1_result, phase2_result, phase3_result, phase4_result
        )

        # Execute parallel generation
        generation_results = await self.image_generator.execute_parallel_generation(
            generation_tasks, UUID(session_id) if session_id != "test_session" else UUID('12345678-1234-5678-9012-123456789abc')
        )

        # Process and analyze results
        return await self._process_generation_results(
            generation_results, generation_tasks, {
                "previous_results": previous_results,
                "session_id": session_id
            }
        )

    async def _create_generation_tasks_from_input(
        self,
        panels: List[Dict[str, Any]],
        session_id: str,
        input_data: Dict[str, Any]
    ) -> List[ImageGenerationTask]:
        """Create simple generation tasks from input panels."""

        tasks = []
        for i, panel in enumerate(panels):
            task = ImageGenerationTask(
                panel_id=f"panel_{i}",
                prompt=f"manga style illustration: {panel}",
                negative_prompt="low quality, blurry, distorted",
                style_parameters={
                    "art_style": "manga",
                    "quality_level": "high",
                    "aspect_ratio": "4:3",
                    "color_mode": "black_and_white",
                    "emphasis": "balanced",
                    "detail_level": "standard"
                },
                priority=5
            )
            tasks.append(task)

        return tasks


    async def _process_generation_results(
        self,
        generation_results: List[ImageGenerationResult],
        generation_tasks: List[ImageGenerationTask],
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and analyze generation results."""

        # Validate results
        processed_results = []
        for result in generation_results:
            if result.success:
                validation_result = self.style_processor.validate_generated_image(result)
                if validation_result["valid"]:
                    processed_results.append(result)
                else:
                    # Mark as failed due to validation
                    failed_result = ImageGenerationResult(
                        panel_id=result.panel_id,
                        success=False,
                        error_message=f"Validation failed: {validation_result['reason']}",
                        generation_time_ms=result.generation_time_ms,
                        retry_count=result.retry_count
                    )
                    processed_results.append(failed_result)
            else:
                processed_results.append(result)

        # Generate quality analysis
        quality_analysis = self.style_processor.analyze_generation_quality(processed_results)

        # Create scene image mapping
        previous_results = context_data.get("previous_results", {})
        phase4_result = previous_results.get(4, {})
        scene_image_mapping = self.style_processor.create_scene_image_mapping(
            processed_results, phase4_result
        )

        # Generate consistency report
        phase2_result = previous_results.get(2, {})
        consistency_report = self.style_processor.generate_consistency_report(
            processed_results, phase2_result
        )

        # Calculate parallel efficiency
        parallel_efficiency = self.style_processor.calculate_parallel_efficiency_score(
            len(generation_tasks),
            processed_results,
            self.image_generator.max_concurrent_generations
        )

        # Get generation statistics and cache utilization
        generation_stats = self.image_generator.get_generation_statistics()
        cache_utilization = self.style_processor.calculate_cache_utilization(generation_stats)

        # Calculate metrics
        successful_count = len([r for r in processed_results if r.success])
        failed_count = len([r for r in processed_results if not r.success])
        avg_generation_time = self._calculate_average_generation_time(processed_results)

        # Create output structure
        result = ImageGenerationOutput(
            generated_images=processed_results,
            scene_image_mapping=scene_image_mapping,
            quality_analysis=quality_analysis,
            consistency_report=consistency_report,
            generation_stats=generation_stats,
            total_images_generated=len(processed_results),
            successful_generations=successful_count,
            failed_generations=failed_count,
            average_generation_time=avg_generation_time,
            parallel_efficiency_score=parallel_efficiency,
            cache_utilization=cache_utilization,
            quality_metrics=self._calculate_quality_metrics(processed_results, quality_analysis),
            recommendations=self._generate_recommendations(
                quality_analysis, consistency_report, parallel_efficiency
            )
        )

        return result.dict()

    def _calculate_average_generation_time(
        self,
        generation_results: List[ImageGenerationResult]
    ) -> float:
        """Calculate average generation time."""

        times = [r.generation_time_ms for r in generation_results if r.generation_time_ms]
        return sum(times) / len(times) if times else 0.0

    def _calculate_quality_metrics(
        self,
        generation_results: List[ImageGenerationResult],
        quality_analysis: QualityAnalysis
    ) -> Dict[str, float]:
        """Calculate comprehensive quality metrics."""

        successful_results = [r for r in generation_results if r.success]

        metrics = {
            "success_rate": quality_analysis.success_rate,
            "average_quality": quality_analysis.average_quality_score,
            "generation_efficiency": 1.0 - (quality_analysis.average_generation_time_ms / 60000),  # Normalize by max expected time
            "retry_efficiency": 1.0 - (len([r for r in generation_results if r.retry_count > 0]) / len(generation_results)) if generation_results else 0
        }

        # Quality distribution score
        dist = quality_analysis.quality_distribution
        total_images = sum(dist.values()) if dist else 1
        quality_dist_score = (
            (dist.get("high", 0) * 1.0 + dist.get("medium", 0) * 0.7 + dist.get("low", 0) * 0.3) / total_images
        ) if total_images > 0 else 0

        metrics["quality_distribution_score"] = quality_dist_score

        return metrics

    def _generate_recommendations(
        self,
        quality_analysis: QualityAnalysis,
        consistency_report: ConsistencyAnalysis,
        parallel_efficiency: float
    ) -> List[str]:
        """Generate comprehensive recommendations."""

        recommendations = []

        # Add quality recommendations
        recommendations.extend(quality_analysis.recommendations)

        # Add consistency recommendations
        recommendations.extend(consistency_report.consistency_recommendations)

        # Add efficiency recommendations
        if parallel_efficiency < 0.5:
            recommendations.append("並列処理効率の改善を検討（リソース配分やタスク分散の最適化）")

        # Remove duplicates
        return list(set(recommendations))

    async def generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate comprehensive prompt for image generation phase."""

        return await self._generate_prompt(input_data, previous_results)

    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate Phase 5 output."""

        required_keys = [
            "generated_images", "scene_image_mapping", "quality_analysis",
            "total_images_generated", "successful_generations"
        ]

        for key in required_keys:
            if key not in output_data:
                self.log_warning(f"Missing required key: {key}")
                return False

        generated_images = output_data.get("generated_images", [])

        # Must have at least 1 successful generation
        successful = [img for img in generated_images if getattr(img, 'success', False)]
        if len(successful) < 1:
            self.log_warning("No successful image generations")
            return False

        # Check image result completeness
        for img in generated_images:
            if isinstance(img, dict):
                success = img.get('success', False)
                image_url = img.get('image_url')
            else:
                success = getattr(img, 'success', False)
                image_url = getattr(img, 'image_url', None)

            if success and not image_url:
                self.log_warning(f"Missing image URL for successful generation")
                return False

        return True

    async def _generate_preview(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate preview data for Phase 5 image generation."""

        generated_images = output_data.get("generated_images", [])
        successful_images = []

        # Safe extraction of successful images
        for img in generated_images:
            if isinstance(img, dict):
                if img.get('success', False):
                    successful_images.append(img)
            else:
                if getattr(img, 'success', False):
                    successful_images.append(img)

        # Safe attribute access helper
        def safe_get_attr(obj, attr, default=None):
            if isinstance(obj, dict):
                return obj.get(attr, default)
            return getattr(obj, attr, default) if hasattr(obj, attr) else default

        preview_data = {
            "phase": 5,
            "phase_name": "画像生成",
            "total_images": len(generated_images),
            "successful_images": len(successful_images),
            "preview_images": [],
            "generation_summary": {
                "success_rate": len(successful_images) / len(generated_images) if generated_images else 0,
                "average_quality": 0.0,
                "total_processing_time": 0.0
            }
        }

        # Calculate quality scores
        if successful_images:
            quality_scores = [safe_get_attr(img, 'quality_score', 0) for img in successful_images]
            valid_quality_scores = [score for score in quality_scores if score is not None and score > 0]
            preview_data["generation_summary"]["average_quality"] = sum(valid_quality_scores) / len(valid_quality_scores) if valid_quality_scores else 0

        # Calculate processing times
        if successful_images:
            processing_times = [safe_get_attr(img, 'generation_time_ms', 0) for img in successful_images]
            valid_processing_times = [time for time in processing_times if time is not None and time > 0]
            preview_data["generation_summary"]["total_processing_time"] = sum(valid_processing_times) / 1000 if valid_processing_times else 0

        # Preview images (up to 3)
        for img in successful_images[:3]:
            preview_data["preview_images"].append({
                "panel_id": safe_get_attr(img, 'panel_id', ''),
                "image_url": safe_get_attr(img, 'image_url', ''),
                "thumbnail_url": safe_get_attr(img, 'thumbnail_url', ''),
                "quality_score": safe_get_attr(img, 'quality_score', 0.0)
            })

        return preview_data
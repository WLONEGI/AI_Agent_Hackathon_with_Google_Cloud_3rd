"""Quality assessment domain service."""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re
import json

from app.domain.manga.entities.generated_content import GeneratedContent, ContentType
from app.domain.manga.entities.phase_result import PhaseResult
from app.domain.manga.value_objects.quality_metrics import (
    QualityScore, QualityMetric, QualityMetricType
)
from app.domain.manga.value_objects.generation_params import GenerationParameters


class QualityAssessmentService:
    """Domain service for quality assessment and validation."""
    
    def __init__(self):
        """Initialize quality assessment service."""
        pass
    
    async def assess_phase_quality(
        self,
        phase_result: PhaseResult,
        generation_params: GenerationParameters,
        input_context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """Assess quality of a phase result."""
        phase_number = phase_result.phase_number
        output_data = phase_result.output_data
        
        # Phase-specific quality assessment
        if phase_number == 1:  # Concept Analysis
            return await self._assess_concept_quality(output_data, generation_params, input_context)
        elif phase_number == 2:  # Character Design
            return await self._assess_character_quality(output_data, generation_params, input_context)
        elif phase_number == 3:  # Plot Structure
            return await self._assess_plot_quality(output_data, generation_params, input_context)
        elif phase_number == 4:  # Name Generation
            return await self._assess_name_quality(output_data, generation_params, input_context)
        elif phase_number == 5:  # Image Generation
            return await self._assess_image_quality(output_data, generation_params, input_context)
        elif phase_number == 6:  # Dialogue Generation
            return await self._assess_dialogue_quality(output_data, generation_params, input_context)
        elif phase_number == 7:  # Integration
            return await self._assess_integration_quality(output_data, generation_params, input_context)
        else:
            # Generic quality assessment
            return QualityScore.create_phase_specific(phase_number, 0.5, "unknown")
    
    async def assess_content_quality(
        self,
        content: GeneratedContent,
        generation_params: GenerationParameters,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """Assess quality of generated content."""
        content_type = content.content_type
        content_data = content.content_data
        phase_number = content.phase_number
        
        if content_type == ContentType.TEXT:
            return await self._assess_text_content_quality(
                content_data, phase_number, generation_params, context
            )
        elif content_type == ContentType.IMAGE:
            return await self._assess_image_content_quality(
                content_data, phase_number, generation_params, context
            )
        elif content_type == ContentType.DIALOGUE:
            return await self._assess_dialogue_content_quality(
                content_data, phase_number, generation_params, context
            )
        else:
            # Generic assessment
            return QualityScore.create_phase_specific(phase_number, 0.6, str(content_type.value))
    
    async def validate_phase_output(
        self,
        phase_number: int,
        output_data: Dict[str, Any],
        generation_params: GenerationParameters
    ) -> Tuple[bool, List[str]]:
        """Validate phase output meets requirements."""
        errors = []
        
        # Phase-specific validation
        if phase_number == 1:  # Concept Analysis
            errors.extend(await self._validate_concept_output(output_data, generation_params))
        elif phase_number == 2:  # Character Design
            errors.extend(await self._validate_character_output(output_data, generation_params))
        elif phase_number == 3:  # Plot Structure
            errors.extend(await self._validate_plot_output(output_data, generation_params))
        elif phase_number == 4:  # Name Generation
            errors.extend(await self._validate_name_output(output_data, generation_params))
        elif phase_number == 5:  # Image Generation
            errors.extend(await self._validate_image_output(output_data, generation_params))
        elif phase_number == 6:  # Dialogue Generation
            errors.extend(await self._validate_dialogue_output(output_data, generation_params))
        elif phase_number == 7:  # Integration
            errors.extend(await self._validate_integration_output(output_data, generation_params))
        
        return len(errors) == 0, errors
    
    async def compare_quality_scores(
        self,
        score1: QualityScore,
        score2: QualityScore
    ) -> Dict[str, Any]:
        """Compare two quality scores."""
        return {
            "overall_comparison": {
                "score1": score1.overall_score,
                "score2": score2.overall_score,
                "difference": score2.overall_score - score1.overall_score,
                "improvement": score2.overall_score > score1.overall_score
            },
            "metric_comparisons": {
                metric_type.value: {
                    "score1": score1.get_metric_score(metric_type) or 0.0,
                    "score2": score2.get_metric_score(metric_type) or 0.0,
                    "difference": (score2.get_metric_score(metric_type) or 0.0) - 
                                 (score1.get_metric_score(metric_type) or 0.0)
                }
                for metric_type in set(score1.metrics.keys()) | set(score2.metrics.keys())
            },
            "summary": {
                "improved_metrics": len([
                    m for m in set(score1.metrics.keys()) & set(score2.metrics.keys())
                    if score2.get_metric_score(m) > score1.get_metric_score(m)
                ]),
                "degraded_metrics": len([
                    m for m in set(score1.metrics.keys()) & set(score2.metrics.keys())
                    if score2.get_metric_score(m) < score1.get_metric_score(m)
                ]),
                "grade_change": f"{score1.get_grade()} → {score2.get_grade()}"
            }
        }
    
    # Phase-specific quality assessment methods
    
    async def _assess_concept_quality(
        self,
        output_data: Dict[str, Any],
        generation_params: GenerationParameters,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """Assess concept analysis quality."""
        metrics = []
        
        # Relevance to input
        relevance_score = await self._calculate_relevance_score(output_data, context)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.RELEVANCE,
            score=relevance_score,
            weight=0.3
        ))
        
        # Genre appropriateness
        genre_score = await self._calculate_genre_appropriateness(output_data, generation_params)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.GENRE_APPROPRIATENESS,
            score=genre_score,
            weight=0.25
        ))
        
        # Coherence
        coherence_score = await self._calculate_coherence_score(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.COHERENCE,
            score=coherence_score,
            weight=0.25
        ))
        
        # Creativity
        creativity_score = await self._calculate_creativity_score(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.CREATIVITY,
            score=creativity_score,
            weight=0.2
        ))
        
        return QualityScore.create_from_metrics(metrics, 1, "concept")
    
    async def _assess_character_quality(
        self,
        output_data: Dict[str, Any],
        generation_params: GenerationParameters,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """Assess character design quality."""
        metrics = []
        
        # Character consistency
        consistency_score = await self._calculate_character_consistency(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.CHARACTER_CONSISTENCY,
            score=consistency_score,
            weight=0.3
        ))
        
        # Visual appeal (for character designs)
        visual_score = await self._calculate_visual_appeal_score(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.VISUAL_APPEAL,
            score=visual_score,
            weight=0.25
        ))
        
        # Creativity
        creativity_score = await self._calculate_creativity_score(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.CREATIVITY,
            score=creativity_score,
            weight=0.2
        ))
        
        # Technical quality
        technical_score = await self._calculate_technical_quality(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.TECHNICAL_QUALITY,
            score=technical_score,
            weight=0.25
        ))
        
        return QualityScore.create_from_metrics(metrics, 2, "character")
    
    async def _assess_plot_quality(
        self,
        output_data: Dict[str, Any],
        generation_params: GenerationParameters,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """Assess plot structure quality."""
        metrics = []
        
        # Plot consistency
        plot_consistency = await self._calculate_plot_consistency(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.PLOT_CONSISTENCY,
            score=plot_consistency,
            weight=0.3
        ))
        
        # Coherence
        coherence_score = await self._calculate_coherence_score(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.COHERENCE,
            score=coherence_score,
            weight=0.25
        ))
        
        # Emotional impact
        emotional_score = await self._calculate_emotional_impact(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.EMOTIONAL_IMPACT,
            score=emotional_score,
            weight=0.2
        ))
        
        # Originality
        originality_score = await self._calculate_originality_score(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.ORIGINALITY,
            score=originality_score,
            weight=0.25
        ))
        
        return QualityScore.create_from_metrics(metrics, 3, "plot")
    
    async def _assess_name_quality(
        self,
        output_data: Dict[str, Any],
        generation_params: GenerationParameters,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """Assess name generation quality."""
        metrics = []
        
        # Character consistency
        consistency_score = await self._calculate_name_consistency(output_data, context)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.CHARACTER_CONSISTENCY,
            score=consistency_score,
            weight=0.3
        ))
        
        # Genre appropriateness
        genre_score = await self._calculate_genre_appropriateness(output_data, generation_params)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.GENRE_APPROPRIATENESS,
            score=genre_score,
            weight=0.25
        ))
        
        # Creativity
        creativity_score = await self._calculate_name_creativity(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.CREATIVITY,
            score=creativity_score,
            weight=0.2
        ))
        
        # Relevance
        relevance_score = await self._calculate_relevance_score(output_data, context)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.RELEVANCE,
            score=relevance_score,
            weight=0.25
        ))
        
        return QualityScore.create_from_metrics(metrics, 4, "names")
    
    async def _assess_image_quality(
        self,
        output_data: Dict[str, Any],
        generation_params: GenerationParameters,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """Assess image generation quality."""
        metrics = []
        
        # Visual appeal
        visual_score = await self._calculate_visual_appeal_score(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.VISUAL_APPEAL,
            score=visual_score,
            weight=0.3
        ))
        
        # Technical quality
        technical_score = await self._calculate_image_technical_quality(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.TECHNICAL_QUALITY,
            score=technical_score,
            weight=0.25
        ))
        
        # Character consistency
        consistency_score = await self._calculate_image_consistency(output_data, context)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.CHARACTER_CONSISTENCY,
            score=consistency_score,
            weight=0.2
        ))
        
        # Coherence
        coherence_score = await self._calculate_coherence_score(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.COHERENCE,
            score=coherence_score,
            weight=0.25
        ))
        
        return QualityScore.create_from_metrics(metrics, 5, "image")
    
    async def _assess_dialogue_quality(
        self,
        output_data: Dict[str, Any],
        generation_params: GenerationParameters,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """Assess dialogue generation quality."""
        metrics = []
        
        # Dialogue naturalness
        naturalness_score = await self._calculate_dialogue_naturalness(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.DIALOGUE_NATURALNESS,
            score=naturalness_score,
            weight=0.3
        ))
        
        # Character consistency
        consistency_score = await self._calculate_dialogue_consistency(output_data, context)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.CHARACTER_CONSISTENCY,
            score=consistency_score,
            weight=0.25
        ))
        
        # Emotional impact
        emotional_score = await self._calculate_emotional_impact(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.EMOTIONAL_IMPACT,
            score=emotional_score,
            weight=0.2
        ))
        
        # Readability
        readability_score = await self._calculate_readability_score(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.READABILITY,
            score=readability_score,
            weight=0.25
        ))
        
        return QualityScore.create_from_metrics(metrics, 6, "dialogue")
    
    async def _assess_integration_quality(
        self,
        output_data: Dict[str, Any],
        generation_params: GenerationParameters,
        context: Optional[Dict[str, Any]] = None
    ) -> QualityScore:
        """Assess integration quality."""
        metrics = []
        
        # Coherence
        coherence_score = await self._calculate_overall_coherence(output_data, context)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.COHERENCE,
            score=coherence_score,
            weight=0.3
        ))
        
        # Technical quality
        technical_score = await self._calculate_technical_quality(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.TECHNICAL_QUALITY,
            score=technical_score,
            weight=0.25
        ))
        
        # Readability
        readability_score = await self._calculate_readability_score(output_data)
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.READABILITY,
            score=readability_score,
            weight=0.25
        ))
        
        # Overall quality (composite)
        overall_score = await self._calculate_composite_quality(output_data, context)
        # Note: Using COHERENCE as placeholder since OVERALL_QUALITY doesn't exist in enum
        metrics.append(QualityMetric(
            metric_type=QualityMetricType.COHERENCE,  
            score=overall_score,
            weight=0.2
        ))
        
        return QualityScore.create_from_metrics(metrics, 7, "integration")
    
    # Quality calculation helper methods (simplified implementations)
    
    async def _calculate_relevance_score(
        self, 
        output_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate relevance score."""
        # Simplified implementation - would use NLP/semantic analysis in practice
        if not context or not output_data:
            return 0.5
        
        # Basic keyword matching
        input_text = context.get("input_text", "").lower()
        output_text = str(output_data).lower()
        
        if not input_text or not output_text:
            return 0.5
        
        # Count matching words (simplified)
        input_words = set(input_text.split())
        output_words = set(output_text.split())
        common_words = input_words & output_words
        
        if len(input_words) == 0:
            return 0.5
        
        return min(1.0, len(common_words) / len(input_words))
    
    async def _calculate_coherence_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate coherence score."""
        # Simplified implementation
        if not output_data:
            return 0.0
        
        # Check for required fields and structure
        required_fields = ["content", "description", "details"]
        present_fields = sum(1 for field in required_fields if field in output_data)
        
        return min(1.0, present_fields / len(required_fields))
    
    async def _calculate_creativity_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate creativity score."""
        # Simplified implementation - would use AI models in practice
        if not output_data:
            return 0.0
        
        # Look for creative elements
        text = str(output_data).lower()
        creative_keywords = ["unique", "original", "innovative", "creative", "unusual", "special"]
        
        creativity_indicators = sum(1 for keyword in creative_keywords if keyword in text)
        return min(1.0, creativity_indicators / 3)  # Normalize to 0-1
    
    async def _calculate_genre_appropriateness(
        self, 
        output_data: Dict[str, Any], 
        generation_params: GenerationParameters
    ) -> float:
        """Calculate genre appropriateness score."""
        # Simplified implementation
        genre = generation_params.primary_genre.value.lower()
        text = str(output_data).lower()
        
        # Genre-specific keywords
        genre_keywords = {
            "shonen": ["adventure", "battle", "friendship", "courage"],
            "shojo": ["romance", "love", "relationship", "emotion"],
            "seinen": ["complex", "mature", "realistic", "psychological"],
            "comedy": ["funny", "humor", "laugh", "joke"],
            "action": ["fight", "battle", "combat", "hero"],
            "horror": ["scary", "fear", "dark", "mystery"]
        }
        
        keywords = genre_keywords.get(genre, [])
        if not keywords:
            return 0.7  # Default score for unknown genres
        
        matches = sum(1 for keyword in keywords if keyword in text)
        return min(1.0, matches / len(keywords))
    
    # Additional helper methods would be implemented here
    # For brevity, I'll add simplified placeholder implementations
    
    async def _calculate_character_consistency(self, output_data: Dict[str, Any]) -> float:
        return 0.8  # Placeholder
    
    async def _calculate_visual_appeal_score(self, output_data: Dict[str, Any]) -> float:
        return 0.7  # Placeholder
    
    async def _calculate_technical_quality(self, output_data: Dict[str, Any]) -> float:
        return 0.8  # Placeholder
    
    async def _calculate_plot_consistency(self, output_data: Dict[str, Any]) -> float:
        return 0.75  # Placeholder
    
    async def _calculate_emotional_impact(self, output_data: Dict[str, Any]) -> float:
        return 0.7  # Placeholder
    
    async def _calculate_originality_score(self, output_data: Dict[str, Any]) -> float:
        return 0.6  # Placeholder
    
    async def _calculate_name_consistency(
        self, 
        output_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> float:
        return 0.8  # Placeholder
    
    async def _calculate_name_creativity(self, output_data: Dict[str, Any]) -> float:
        return 0.7  # Placeholder
    
    async def _calculate_image_technical_quality(self, output_data: Dict[str, Any]) -> float:
        return 0.8  # Placeholder
    
    async def _calculate_image_consistency(
        self, 
        output_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> float:
        return 0.8  # Placeholder
    
    async def _calculate_dialogue_naturalness(self, output_data: Dict[str, Any]) -> float:
        return 0.8  # Placeholder
    
    async def _calculate_dialogue_consistency(
        self, 
        output_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> float:
        return 0.8  # Placeholder
    
    async def _calculate_readability_score(self, output_data: Dict[str, Any]) -> float:
        return 0.8  # Placeholder
    
    async def _calculate_overall_coherence(
        self, 
        output_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> float:
        return 0.8  # Placeholder
    
    async def _calculate_composite_quality(
        self, 
        output_data: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> float:
        return 0.8  # Placeholder
    
    # Content quality assessment methods
    
    async def _assess_text_content_quality(
        self,
        content_data: Any,
        phase_number: int,
        generation_params: GenerationParameters,
        context: Optional[Dict[str, Any]]
    ) -> QualityScore:
        """Assess text content quality."""
        return QualityScore.create_phase_specific(phase_number, 0.7, "text")
    
    async def _assess_image_content_quality(
        self,
        content_data: Any,
        phase_number: int,
        generation_params: GenerationParameters,
        context: Optional[Dict[str, Any]]
    ) -> QualityScore:
        """Assess image content quality."""
        return QualityScore.create_phase_specific(phase_number, 0.7, "image")
    
    async def _assess_dialogue_content_quality(
        self,
        content_data: Any,
        phase_number: int,
        generation_params: GenerationParameters,
        context: Optional[Dict[str, Any]]
    ) -> QualityScore:
        """Assess dialogue content quality."""
        return QualityScore.create_phase_specific(phase_number, 0.7, "dialogue")
    
    # Validation methods
    
    async def _validate_concept_output(
        self, 
        output_data: Dict[str, Any], 
        generation_params: GenerationParameters
    ) -> List[str]:
        """Validate concept analysis output."""
        errors = []
        
        if "concept" not in output_data:
            errors.append("Missing concept field")
        
        if "genre" not in output_data:
            errors.append("Missing genre field")
        
        if "tone" not in output_data:
            errors.append("Missing tone field")
        
        return errors
    
    async def _validate_character_output(
        self, 
        output_data: Dict[str, Any], 
        generation_params: GenerationParameters
    ) -> List[str]:
        """Validate character design output."""
        errors = []
        
        if "characters" not in output_data:
            errors.append("Missing characters field")
        
        return errors
    
    async def _validate_plot_output(
        self, 
        output_data: Dict[str, Any], 
        generation_params: GenerationParameters
    ) -> List[str]:
        """Validate plot structure output."""
        errors = []
        
        if "plot_structure" not in output_data:
            errors.append("Missing plot_structure field")
        
        return errors
    
    async def _validate_name_output(
        self, 
        output_data: Dict[str, Any], 
        generation_params: GenerationParameters
    ) -> List[str]:
        """Validate name generation output."""
        errors = []
        
        if "names" not in output_data:
            errors.append("Missing names field")
        
        return errors
    
    async def _validate_image_output(
        self, 
        output_data: Dict[str, Any], 
        generation_params: GenerationParameters
    ) -> List[str]:
        """Validate image generation output."""
        errors = []
        
        if "image_url" not in output_data and "image_data" not in output_data:
            errors.append("Missing image URL or data")
        
        return errors
    
    async def _validate_dialogue_output(
        self, 
        output_data: Dict[str, Any], 
        generation_params: GenerationParameters
    ) -> List[str]:
        """Validate dialogue generation output."""
        errors = []
        
        if "dialogue" not in output_data:
            errors.append("Missing dialogue field")
        
        return errors
    
    async def _validate_integration_output(
        self, 
        output_data: Dict[str, Any], 
        generation_params: GenerationParameters
    ) -> List[str]:
        """Validate integration output."""
        errors = []
        
        if "final_output" not in output_data:
            errors.append("Missing final_output field")
        
        return errors
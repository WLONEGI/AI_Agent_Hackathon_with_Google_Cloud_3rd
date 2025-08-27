"""Unit tests for Quality Metrics value objects."""

import pytest
from typing import Dict, Any

from app.domain.manga.value_objects.quality_metrics import (
    QualityMetric,
    QualityScore,
    QualityMetricType
)


class TestQualityMetric:
    """Test cases for QualityMetric value object."""
    
    def test_quality_metric_creation(self):
        """Test basic quality metric creation."""
        metric = QualityMetric(
            metric_type=QualityMetricType.RELEVANCE,
            score=0.85,
            weight=0.8,
            description="Story relevance assessment"
        )
        
        assert metric.metric_type == QualityMetricType.RELEVANCE
        assert metric.score == 0.85
        assert metric.weight == 0.8
        assert metric.description == "Story relevance assessment"
    
    def test_quality_metric_validation(self):
        """Test quality metric validation."""
        # Valid metric
        metric = QualityMetric(
            metric_type=QualityMetricType.CREATIVITY,
            score=0.9,
            weight=0.7
        )
        assert metric.score == 0.9
        
        # Invalid score (too high)
        with pytest.raises(ValueError, match="Score must be between 0.0 and 1.0"):
            QualityMetric(
                metric_type=QualityMetricType.CREATIVITY,
                score=1.5,
                weight=0.5
            )
        
        # Invalid score (too low)
        with pytest.raises(ValueError, match="Score must be between 0.0 and 1.0"):
            QualityMetric(
                metric_type=QualityMetricType.CREATIVITY,
                score=-0.1,
                weight=0.5
            )
        
        # Invalid weight
        with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
            QualityMetric(
                metric_type=QualityMetricType.CREATIVITY,
                score=0.5,
                weight=1.5
            )
    
    def test_weighted_score_calculation(self):
        """Test weighted score calculation."""
        metric = QualityMetric(
            metric_type=QualityMetricType.COHERENCE,
            score=0.8,
            weight=0.6
        )
        
        expected_weighted = 0.8 * 0.6
        assert metric.weighted_score() == expected_weighted
    
    def test_quality_threshold_check(self):
        """Test quality threshold checking."""
        high_quality = QualityMetric(
            metric_type=QualityMetricType.VISUAL_APPEAL,
            score=0.85,
            weight=1.0
        )
        
        low_quality = QualityMetric(
            metric_type=QualityMetricType.VISUAL_APPEAL,
            score=0.45,
            weight=1.0
        )
        
        # Default threshold (0.6)
        assert high_quality.is_passing() is True
        assert low_quality.is_passing() is False
        
        # Custom threshold
        assert high_quality.is_passing(0.9) is False
        assert low_quality.is_passing(0.4) is True
    
    def test_grade_assignment(self):
        """Test letter grade assignment."""
        test_cases = [
            (0.95, "A"),
            (0.85, "B"), 
            (0.75, "C"),
            (0.65, "D"),
            (0.45, "F")
        ]
        
        for score, expected_grade in test_cases:
            metric = QualityMetric(
                metric_type=QualityMetricType.TECHNICAL_QUALITY,
                score=score,
                weight=1.0
            )
            assert metric.get_grade() == expected_grade
    
    def test_metric_with_details(self):
        """Test metric with detailed breakdown."""
        details = {
            "grammar": 0.9,
            "vocabulary": 0.8,
            "structure": 0.85
        }
        
        metric = QualityMetric(
            metric_type=QualityMetricType.DIALOGUE_NATURALNESS,
            score=0.85,
            weight=0.8,
            details=details
        )
        
        assert metric.details == details
        assert metric.details["grammar"] == 0.9


class TestQualityScore:
    """Test cases for QualityScore value object."""
    
    def test_quality_score_creation_from_metrics(self):
        """Test quality score creation from individual metrics."""
        metrics = [
            QualityMetric(QualityMetricType.RELEVANCE, 0.8, 0.3),
            QualityMetric(QualityMetricType.CREATIVITY, 0.9, 0.4),
            QualityMetric(QualityMetricType.COHERENCE, 0.7, 0.3)
        ]
        
        quality_score = QualityScore.create_from_metrics(
            metrics=metrics,
            phase_number=1,
            content_type="concept_analysis"
        )
        
        # Calculate expected overall score
        # (0.8 * 0.3 + 0.9 * 0.4 + 0.7 * 0.3) / (0.3 + 0.4 + 0.3)
        expected_overall = (0.24 + 0.36 + 0.21) / 1.0
        
        assert quality_score.overall_score == expected_overall
        assert quality_score.phase_number == 1
        assert quality_score.content_type == "concept_analysis"
        assert len(quality_score.metrics) == 3
    
    def test_quality_score_validation(self):
        """Test quality score validation."""
        metrics = [
            QualityMetric(QualityMetricType.RELEVANCE, 0.8, 1.0)
        ]
        
        # Valid score
        quality_score = QualityScore.create_from_metrics(
            metrics, phase_number=3, content_type="test"
        )
        assert quality_score.overall_score == 0.8
        
        # Invalid phase number
        with pytest.raises(ValueError, match="Phase number must be between 1 and 7"):
            QualityScore(
                metrics={QualityMetricType.RELEVANCE: metrics[0]},
                overall_score=0.8,
                phase_number=8,
                content_type="test"
            )
    
    def test_phase_specific_quality_score(self):
        """Test phase-specific quality score creation."""
        # Test Phase 1 (Concept Analysis)
        phase1_score = QualityScore.create_phase_specific(
            phase_number=1,
            base_score=0.8,
            content_type="concept_analysis"
        )
        
        assert phase1_score.phase_number == 1
        assert phase1_score.content_type == "concept_analysis"
        
        # Should have phase 1 specific metrics
        expected_phase1_metrics = {
            QualityMetricType.RELEVANCE,
            QualityMetricType.COHERENCE,
            QualityMetricType.CREATIVITY,
            QualityMetricType.GENRE_APPROPRIATENESS
        }
        
        assert set(phase1_score.metrics.keys()) == expected_phase1_metrics
        
        # Test Phase 5 (Image Generation) 
        phase5_score = QualityScore.create_phase_specific(
            phase_number=5,
            base_score=0.75,
            content_type="image_generation"
        )
        
        expected_phase5_metrics = {
            QualityMetricType.VISUAL_APPEAL,
            QualityMetricType.TECHNICAL_QUALITY,
            QualityMetricType.CHARACTER_CONSISTENCY,
            QualityMetricType.COHERENCE
        }
        
        assert set(phase5_score.metrics.keys()) == expected_phase5_metrics
    
    def test_custom_metric_override(self):
        """Test custom metric score override in phase-specific creation."""
        custom_metrics = {
            QualityMetricType.CREATIVITY: 0.95,
            QualityMetricType.VISUAL_APPEAL: 0.85
        }
        
        quality_score = QualityScore.create_phase_specific(
            phase_number=2,  # Character Design
            base_score=0.7,
            content_type="character_design",
            custom_metrics=custom_metrics
        )
        
        # Custom metrics should override base score
        creativity_metric = quality_score.metrics[QualityMetricType.CREATIVITY]
        assert creativity_metric.score == 0.95
        
        # Visual appeal should be overridden if it exists in phase 2
        if QualityMetricType.VISUAL_APPEAL in quality_score.metrics:
            visual_metric = quality_score.metrics[QualityMetricType.VISUAL_APPEAL]
            assert visual_metric.score == 0.85
    
    def test_metric_score_retrieval(self):
        """Test retrieving specific metric scores."""
        metrics = [
            QualityMetric(QualityMetricType.RELEVANCE, 0.8, 0.5),
            QualityMetric(QualityMetricType.CREATIVITY, 0.9, 0.5)
        ]
        
        quality_score = QualityScore.create_from_metrics(
            metrics, phase_number=1, content_type="test"
        )
        
        # Test individual metric score retrieval
        assert quality_score.get_metric_score(QualityMetricType.RELEVANCE) == 0.8
        assert quality_score.get_metric_score(QualityMetricType.CREATIVITY) == 0.9
        assert quality_score.get_metric_score(QualityMetricType.COHERENCE) is None
        
        # Test weighted metric score retrieval
        assert quality_score.get_weighted_metric_score(QualityMetricType.RELEVANCE) == 0.4
        assert quality_score.get_weighted_metric_score(QualityMetricType.CREATIVITY) == 0.45
    
    def test_failing_metrics_identification(self):
        """Test identification of failing metrics."""
        metrics = [
            QualityMetric(QualityMetricType.RELEVANCE, 0.8, 1.0),  # Passing
            QualityMetric(QualityMetricType.CREATIVITY, 0.5, 1.0),  # Failing
            QualityMetric(QualityMetricType.COHERENCE, 0.4, 1.0)   # Failing
        ]
        
        quality_score = QualityScore.create_from_metrics(
            metrics, phase_number=1, content_type="test"
        )
        
        failing_metrics = quality_score.get_failing_metrics(threshold=0.6)
        
        assert len(failing_metrics) == 2
        failing_types = {m.metric_type for m in failing_metrics}
        assert failing_types == {QualityMetricType.CREATIVITY, QualityMetricType.COHERENCE}
    
    def test_overall_grade_calculation(self):
        """Test overall letter grade calculation."""
        test_cases = [
            (0.95, "A"),
            (0.85, "B"),
            (0.75, "C"), 
            (0.65, "D"),
            (0.45, "F")
        ]
        
        for score, expected_grade in test_cases:
            metrics = [QualityMetric(QualityMetricType.RELEVANCE, score, 1.0)]
            quality_score = QualityScore.create_from_metrics(
                metrics, phase_number=1, content_type="test"
            )
            assert quality_score.get_grade() == expected_grade
    
    def test_improvement_suggestions(self):
        """Test improvement suggestion generation."""
        metrics = [
            QualityMetric(QualityMetricType.CREATIVITY, 0.5, 1.0),     # Failing
            QualityMetric(QualityMetricType.COHERENCE, 0.4, 1.0),      # Failing
            QualityMetric(QualityMetricType.RELEVANCE, 0.8, 1.0)       # Passing
        ]
        
        quality_score = QualityScore.create_from_metrics(
            metrics, phase_number=1, content_type="test"
        )
        
        suggestions = quality_score.get_improvement_suggestions()
        
        assert len(suggestions) == 2  # Only failing metrics get suggestions
        
        # Check that suggestions contain relevant text
        suggestion_text = " ".join(suggestions)
        assert "創造" in suggestion_text or "クリエイティ" in suggestion_text  # Creativity
        assert "一貫" in suggestion_text or "コヒーレンス" in suggestion_text   # Coherence
    
    def test_quality_score_serialization(self):
        """Test quality score dictionary conversion."""
        metrics = [
            QualityMetric(QualityMetricType.RELEVANCE, 0.8, 0.6),
            QualityMetric(QualityMetricType.CREATIVITY, 0.9, 0.4)
        ]
        
        quality_score = QualityScore.create_from_metrics(
            metrics, phase_number=2, content_type="character_design"
        )
        
        score_dict = quality_score.to_dict()
        
        # Check top-level fields
        assert "overall_score" in score_dict
        assert "phase_number" in score_dict
        assert "content_type" in score_dict
        assert "grade" in score_dict
        assert "is_passing" in score_dict
        assert "metrics" in score_dict
        assert "improvement_suggestions" in score_dict
        
        # Check metrics structure
        metrics_dict = score_dict["metrics"]
        assert "relevance" in metrics_dict
        assert "creativity" in metrics_dict
        
        relevance_data = metrics_dict["relevance"]
        assert "score" in relevance_data
        assert "weight" in relevance_data
        assert "weighted_score" in relevance_data
        assert "grade" in relevance_data
        assert "is_passing" in relevance_data
    
    def test_empty_metrics_handling(self):
        """Test handling of empty metrics list."""
        with pytest.raises(ValueError, match="At least one metric is required"):
            QualityScore.create_from_metrics(
                metrics=[],
                phase_number=1,
                content_type="test"
            )
    
    def test_zero_weight_metrics(self):
        """Test handling of metrics with zero weight."""
        metrics = [
            QualityMetric(QualityMetricType.RELEVANCE, 0.8, 0.0),  # Zero weight
            QualityMetric(QualityMetricType.CREATIVITY, 0.9, 0.0)  # Zero weight
        ]
        
        quality_score = QualityScore.create_from_metrics(
            metrics, phase_number=1, content_type="test"
        )
        
        # Overall score should be 0.0 when all weights are 0
        assert quality_score.overall_score == 0.0


class TestQualityMetricTypeEnum:
    """Test cases for QualityMetricType enumeration."""
    
    def test_all_metric_types_defined(self):
        """Test that all expected metric types are defined."""
        expected_types = [
            "relevance", "coherence", "creativity", "technical_quality",
            "visual_appeal", "character_consistency", "plot_consistency",
            "dialogue_naturalness", "genre_appropriateness", "originality",
            "emotional_impact", "readability"
        ]
        
        actual_types = [metric_type.value for metric_type in QualityMetricType]
        
        for expected_type in expected_types:
            assert expected_type in actual_types
    
    def test_metric_type_string_values(self):
        """Test metric type string values."""
        assert QualityMetricType.RELEVANCE.value == "relevance"
        assert QualityMetricType.CREATIVITY.value == "creativity"
        assert QualityMetricType.VISUAL_APPEAL.value == "visual_appeal"
        assert QualityMetricType.CHARACTER_CONSISTENCY.value == "character_consistency"


class TestQualityMetricsEdgeCases:
    """Test edge cases for quality metrics."""
    
    def test_boundary_scores(self):
        """Test boundary score values (0.0 and 1.0)."""
        # Minimum score
        min_metric = QualityMetric(
            metric_type=QualityMetricType.RELEVANCE,
            score=0.0,
            weight=1.0
        )
        assert min_metric.score == 0.0
        assert min_metric.get_grade() == "F"
        assert not min_metric.is_passing()
        
        # Maximum score
        max_metric = QualityMetric(
            metric_type=QualityMetricType.RELEVANCE,
            score=1.0,
            weight=1.0
        )
        assert max_metric.score == 1.0
        assert max_metric.get_grade() == "A"
        assert max_metric.is_passing()
    
    def test_phase_number_boundaries(self):
        """Test phase number boundary validation."""
        metrics = [QualityMetric(QualityMetricType.RELEVANCE, 0.8, 1.0)]
        
        # Valid boundary cases
        phase_1 = QualityScore.create_from_metrics(
            metrics, phase_number=1, content_type="test"
        )
        assert phase_1.phase_number == 1
        
        phase_7 = QualityScore.create_from_metrics(
            metrics, phase_number=7, content_type="test"
        )
        assert phase_7.phase_number == 7
        
        # Invalid boundary cases
        with pytest.raises(ValueError):
            QualityScore.create_from_metrics(
                metrics, phase_number=0, content_type="test"
            )
        
        with pytest.raises(ValueError):
            QualityScore.create_from_metrics(
                metrics, phase_number=8, content_type="test"
            )
    
    def test_complex_weighted_calculation(self):
        """Test complex weighted score calculation."""
        metrics = [
            QualityMetric(QualityMetricType.RELEVANCE, 0.9, 0.1),      # Low weight, high score
            QualityMetric(QualityMetricType.CREATIVITY, 0.3, 0.8),     # High weight, low score
            QualityMetric(QualityMetricType.COHERENCE, 0.7, 0.1)       # Low weight, medium score
        ]
        
        quality_score = QualityScore.create_from_metrics(
            metrics, phase_number=1, content_type="test"
        )
        
        # Manual calculation: (0.9*0.1 + 0.3*0.8 + 0.7*0.1) / (0.1+0.8+0.1)
        expected = (0.09 + 0.24 + 0.07) / 1.0
        
        assert abs(quality_score.overall_score - expected) < 1e-10
    
    def test_unicode_content_type(self):
        """Test Unicode handling in content type."""
        metrics = [QualityMetric(QualityMetricType.RELEVANCE, 0.8, 1.0)]
        
        quality_score = QualityScore.create_from_metrics(
            metrics, 
            phase_number=1, 
            content_type="キャラクター分析"  # Japanese text
        )
        
        assert quality_score.content_type == "キャラクター分析"
        
        score_dict = quality_score.to_dict()
        assert score_dict["content_type"] == "キャラクター分析"
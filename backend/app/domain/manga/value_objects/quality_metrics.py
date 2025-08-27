"""Quality metrics value objects."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class QualityMetricType(str, Enum):
    """Quality metric type enumeration."""
    RELEVANCE = "relevance"
    COHERENCE = "coherence"
    CREATIVITY = "creativity"
    TECHNICAL_QUALITY = "technical_quality"
    VISUAL_APPEAL = "visual_appeal"
    CHARACTER_CONSISTENCY = "character_consistency"
    PLOT_CONSISTENCY = "plot_consistency"
    DIALOGUE_NATURALNESS = "dialogue_naturalness"
    GENRE_APPROPRIATENESS = "genre_appropriateness"
    ORIGINALITY = "originality"
    EMOTIONAL_IMPACT = "emotional_impact"
    READABILITY = "readability"


@dataclass(frozen=True)
class QualityMetric:
    """Individual quality metric value object."""
    
    metric_type: QualityMetricType
    score: float  # 0.0 to 1.0
    weight: float = 1.0
    description: Optional[str] = None
    details: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        """Validate metric values."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")
        
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {self.weight}")
    
    def weighted_score(self) -> float:
        """Get weighted score for this metric."""
        return self.score * self.weight
    
    def is_passing(self, threshold: float = 0.6) -> bool:
        """Check if metric meets quality threshold."""
        return self.score >= threshold
    
    def get_grade(self) -> str:
        """Get letter grade for this metric."""
        if self.score >= 0.9:
            return "A"
        elif self.score >= 0.8:
            return "B"
        elif self.score >= 0.7:
            return "C"
        elif self.score >= 0.6:
            return "D"
        else:
            return "F"


@dataclass(frozen=True)
class QualityScore:
    """Comprehensive quality score value object."""
    
    metrics: Dict[QualityMetricType, QualityMetric]
    overall_score: float
    phase_number: int
    content_type: str
    
    def __post_init__(self):
        """Validate quality score."""
        if not 0.0 <= self.overall_score <= 1.0:
            raise ValueError(f"Overall score must be between 0.0 and 1.0, got {self.overall_score}")
        
        if self.phase_number < 1 or self.phase_number > 7:
            raise ValueError(f"Phase number must be between 1 and 7, got {self.phase_number}")
    
    @classmethod
    def create_from_metrics(
        cls,
        metrics: List[QualityMetric],
        phase_number: int,
        content_type: str
    ) -> "QualityScore":
        """Create quality score from individual metrics."""
        if not metrics:
            raise ValueError("At least one metric is required")
        
        metrics_dict = {metric.metric_type: metric for metric in metrics}
        
        # Calculate weighted overall score
        total_weighted_score = sum(metric.weighted_score() for metric in metrics)
        total_weight = sum(metric.weight for metric in metrics)
        
        if total_weight == 0:
            overall_score = 0.0
        else:
            overall_score = total_weighted_score / total_weight
        
        return cls(
            metrics=metrics_dict,
            overall_score=overall_score,
            phase_number=phase_number,
            content_type=content_type
        )
    
    @classmethod
    def create_phase_specific(
        cls,
        phase_number: int,
        base_score: float,
        content_type: str,
        custom_metrics: Optional[Dict[QualityMetricType, float]] = None
    ) -> "QualityScore":
        """Create phase-specific quality score."""
        # Define phase-specific metrics and weights
        phase_metrics = {
            1: {  # Concept Analysis
                QualityMetricType.RELEVANCE: 0.3,
                QualityMetricType.COHERENCE: 0.25,
                QualityMetricType.CREATIVITY: 0.2,
                QualityMetricType.GENRE_APPROPRIATENESS: 0.25
            },
            2: {  # Character Design
                QualityMetricType.CHARACTER_CONSISTENCY: 0.3,
                QualityMetricType.VISUAL_APPEAL: 0.25,
                QualityMetricType.CREATIVITY: 0.2,
                QualityMetricType.TECHNICAL_QUALITY: 0.25
            },
            3: {  # Plot Structure
                QualityMetricType.PLOT_CONSISTENCY: 0.3,
                QualityMetricType.COHERENCE: 0.25,
                QualityMetricType.EMOTIONAL_IMPACT: 0.2,
                QualityMetricType.ORIGINALITY: 0.25
            },
            4: {  # Name Generation
                QualityMetricType.CHARACTER_CONSISTENCY: 0.3,
                QualityMetricType.GENRE_APPROPRIATENESS: 0.25,
                QualityMetricType.CREATIVITY: 0.2,
                QualityMetricType.RELEVANCE: 0.25
            },
            5: {  # Image Generation
                QualityMetricType.VISUAL_APPEAL: 0.3,
                QualityMetricType.TECHNICAL_QUALITY: 0.25,
                QualityMetricType.CHARACTER_CONSISTENCY: 0.2,
                QualityMetricType.COHERENCE: 0.25
            },
            6: {  # Dialogue Generation
                QualityMetricType.DIALOGUE_NATURALNESS: 0.3,
                QualityMetricType.CHARACTER_CONSISTENCY: 0.25,
                QualityMetricType.EMOTIONAL_IMPACT: 0.2,
                QualityMetricType.READABILITY: 0.25
            },
            7: {  # Integration
                QualityMetricType.COHERENCE: 0.3,
                QualityMetricType.TECHNICAL_QUALITY: 0.25,
                QualityMetricType.OVERALL_QUALITY: 0.2,
                QualityMetricType.READABILITY: 0.25
            }
        }
        
        # Get metrics for this phase
        phase_weights = phase_metrics.get(phase_number, {
            QualityMetricType.RELEVANCE: 0.5,
            QualityMetricType.TECHNICAL_QUALITY: 0.5
        })
        
        # Create metrics with custom scores or base score
        metrics = []
        for metric_type, weight in phase_weights.items():
            score = base_score
            if custom_metrics and metric_type in custom_metrics:
                score = custom_metrics[metric_type]
            
            # Add some variance based on metric type
            if metric_type == QualityMetricType.CREATIVITY:
                score = min(1.0, score + 0.1)  # Creativity bonus
            elif metric_type == QualityMetricType.TECHNICAL_QUALITY:
                score = max(0.0, score - 0.05)  # Technical penalty
            
            metrics.append(QualityMetric(
                metric_type=metric_type,
                score=score,
                weight=weight
            ))
        
        return cls.create_from_metrics(metrics, phase_number, content_type)
    
    def get_metric_score(self, metric_type: QualityMetricType) -> Optional[float]:
        """Get score for specific metric type."""
        metric = self.metrics.get(metric_type)
        return metric.score if metric else None
    
    def get_weighted_metric_score(self, metric_type: QualityMetricType) -> Optional[float]:
        """Get weighted score for specific metric type."""
        metric = self.metrics.get(metric_type)
        return metric.weighted_score() if metric else None
    
    def is_passing(self, threshold: float = 0.6) -> bool:
        """Check if overall quality meets threshold."""
        return self.overall_score >= threshold
    
    def get_failing_metrics(self, threshold: float = 0.6) -> List[QualityMetric]:
        """Get list of metrics that don't meet threshold."""
        return [
            metric for metric in self.metrics.values()
            if not metric.is_passing(threshold)
        ]
    
    def get_grade(self) -> str:
        """Get letter grade for overall quality."""
        if self.overall_score >= 0.9:
            return "A"
        elif self.overall_score >= 0.8:
            return "B"
        elif self.overall_score >= 0.7:
            return "C"
        elif self.overall_score >= 0.6:
            return "D"
        else:
            return "F"
    
    def get_improvement_suggestions(self) -> List[str]:
        """Get suggestions for quality improvement."""
        suggestions = []
        failing_metrics = self.get_failing_metrics()
        
        if not failing_metrics:
            return suggestions
        
        improvement_map = {
            QualityMetricType.RELEVANCE: "内容をテーマにより適合させてください",
            QualityMetricType.COHERENCE: "一貫性と論理性を改善してください",
            QualityMetricType.CREATIVITY: "より創造的で独創的な要素を追加してください",
            QualityMetricType.TECHNICAL_QUALITY: "技術的品質を向上させてください",
            QualityMetricType.VISUAL_APPEAL: "視覚的魅力を高めてください",
            QualityMetricType.CHARACTER_CONSISTENCY: "キャラクター設定の一貫性を保ってください",
            QualityMetricType.PLOT_CONSISTENCY: "プロット構造を改善してください",
            QualityMetricType.DIALOGUE_NATURALNESS: "台詞をより自然にしてください",
            QualityMetricType.GENRE_APPROPRIATENESS: "ジャンルに適した表現を使用してください",
            QualityMetricType.ORIGINALITY: "独創性を高めてください",
            QualityMetricType.EMOTIONAL_IMPACT: "感情的インパクトを強化してください",
            QualityMetricType.READABILITY: "読みやすさを改善してください"
        }
        
        for metric in failing_metrics:
            suggestion = improvement_map.get(
                metric.metric_type,
                f"{metric.metric_type.value}の品質を改善してください"
            )
            suggestions.append(f"{suggestion} (現在: {metric.score:.2f})")
        
        return suggestions
    
    def to_dict(self) -> Dict[str, any]:
        """Convert quality score to dictionary."""
        return {
            "overall_score": self.overall_score,
            "phase_number": self.phase_number,
            "content_type": self.content_type,
            "grade": self.get_grade(),
            "is_passing": self.is_passing(),
            "metrics": {
                metric_type.value: {
                    "score": metric.score,
                    "weight": metric.weight,
                    "weighted_score": metric.weighted_score(),
                    "grade": metric.get_grade(),
                    "is_passing": metric.is_passing()
                }
                for metric_type, metric in self.metrics.items()
            },
            "improvement_suggestions": self.get_improvement_suggestions()
        }
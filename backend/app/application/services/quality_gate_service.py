"""
Quality Gate Service - Phase 2 Quality Gate Integration.

This module provides quality assessment and validation services
integrated with the preview system for comprehensive quality control.

Implements quality gates, automated assessments, and feedback validation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from uuid import UUID
from dataclasses import dataclass
from enum import Enum

from app.domain.manga.repositories.preview_repository import PreviewRepository
from app.domain.common.preview_entities import (
    PreviewVersionEntity,
    PreviewInteractionEntity,
    PreviewQualitySettingsEntity
)

logger = logging.getLogger(__name__)


class QualityGateResult(Enum):
    """Quality gate assessment results."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NEEDS_REVIEW = "needs_review"


class QualityMetric(Enum):
    """Quality assessment metrics."""
    VISUAL_QUALITY = "visual_quality"
    TECHNICAL_QUALITY = "technical_quality"
    CONTENT_ACCURACY = "content_accuracy"
    USER_FEEDBACK = "user_feedback"
    PERFORMANCE = "performance"
    CONSISTENCY = "consistency"


@dataclass
class QualityAssessment:
    """Quality assessment result for a preview version."""
    version_id: UUID
    overall_score: float  # 0.0 - 1.0
    metric_scores: Dict[QualityMetric, float]
    gate_result: QualityGateResult
    issues: List[str]
    recommendations: List[str]
    confidence_level: float
    assessed_at: datetime
    assessment_details: Dict[str, Any]


@dataclass
class QualityGateConfig:
    """Configuration for quality gate thresholds and rules."""
    min_overall_score: float = 0.7
    min_metric_scores: Dict[QualityMetric, float] = None
    max_allowed_issues: int = 5
    require_user_approval: bool = True
    auto_promote_threshold: float = 0.95
    feedback_weight: float = 0.3
    performance_weight: float = 0.2
    visual_weight: float = 0.3
    technical_weight: float = 0.2
    
    def __post_init__(self):
        if self.min_metric_scores is None:
            self.min_metric_scores = {
                QualityMetric.VISUAL_QUALITY: 0.7,
                QualityMetric.TECHNICAL_QUALITY: 0.8,
                QualityMetric.CONTENT_ACCURACY: 0.75,
                QualityMetric.USER_FEEDBACK: 0.6,
                QualityMetric.PERFORMANCE: 0.7,
                QualityMetric.CONSISTENCY: 0.8
            }


class QualityGateService:
    """
    Service for quality gate operations and assessments.
    
    Provides comprehensive quality assessment capabilities integrated
    with the preview system for automated quality control.
    """
    
    def __init__(self, preview_repository: PreviewRepository, config: Optional[QualityGateConfig] = None):
        self.preview_repository = preview_repository
        self.config = config or QualityGateConfig()
        self.assessment_cache: Dict[UUID, QualityAssessment] = {}
    
    async def assess_version_quality(
        self, 
        version_id: UUID,
        include_interactions: bool = True,
        use_cache: bool = True
    ) -> QualityAssessment:
        """
        Perform comprehensive quality assessment on a preview version.
        
        Args:
            version_id: Version to assess
            include_interactions: Whether to include user interactions in assessment
            use_cache: Whether to use cached assessment if available
            
        Returns:
            Quality assessment result
        """
        # Check cache first
        if use_cache and version_id in self.assessment_cache:
            cached_assessment = self.assessment_cache[version_id]
            if (datetime.utcnow() - cached_assessment.assessed_at).total_seconds() < 300:  # 5 min cache
                logger.debug(f"Using cached quality assessment for version {version_id}")
                return cached_assessment
        
        logger.info(
            f"Performing quality assessment for version: {version_id}",
            extra={
                "service": "QualityGate",
                "operation": "assess_version_quality",
                "version_id": str(version_id),
                "include_interactions": include_interactions
            }
        )
        
        try:
            # Get version data
            version = await self.preview_repository.find_preview_version_by_id(version_id)
            if not version:
                raise ValueError(f"Version not found: {version_id}")
            
            # Initialize metric scores
            metric_scores = {}
            assessment_details = {}
            issues = []
            recommendations = []
            
            # Assess visual quality
            visual_score, visual_details = await self._assess_visual_quality(version)
            metric_scores[QualityMetric.VISUAL_QUALITY] = visual_score
            assessment_details["visual"] = visual_details
            
            # Assess technical quality
            technical_score, technical_details = await self._assess_technical_quality(version)
            metric_scores[QualityMetric.TECHNICAL_QUALITY] = technical_score
            assessment_details["technical"] = technical_details
            
            # Assess content accuracy
            content_score, content_details = await self._assess_content_accuracy(version)
            metric_scores[QualityMetric.CONTENT_ACCURACY] = content_score
            assessment_details["content"] = content_details
            
            # Assess performance
            performance_score, performance_details = await self._assess_performance(version)
            metric_scores[QualityMetric.PERFORMANCE] = performance_score
            assessment_details["performance"] = performance_details
            
            # Assess consistency
            consistency_score, consistency_details = await self._assess_consistency(version)
            metric_scores[QualityMetric.CONSISTENCY] = consistency_score
            assessment_details["consistency"] = consistency_details
            
            # Assess user feedback if requested
            if include_interactions:
                feedback_score, feedback_details = await self._assess_user_feedback(version)
                metric_scores[QualityMetric.USER_FEEDBACK] = feedback_score
                assessment_details["user_feedback"] = feedback_details
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(metric_scores)
            
            # Determine gate result
            gate_result = self._determine_gate_result(overall_score, metric_scores)
            
            # Generate issues and recommendations
            issues = self._identify_issues(metric_scores, assessment_details)
            recommendations = self._generate_recommendations(metric_scores, assessment_details, version)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(metric_scores, assessment_details)
            
            # Create assessment result
            assessment = QualityAssessment(
                version_id=version_id,
                overall_score=overall_score,
                metric_scores=metric_scores,
                gate_result=gate_result,
                issues=issues,
                recommendations=recommendations,
                confidence_level=confidence_level,
                assessed_at=datetime.utcnow(),
                assessment_details=assessment_details
            )
            
            # Cache the assessment
            self.assessment_cache[version_id] = assessment
            
            logger.info(
                f"Quality assessment completed for version {version_id}",
                extra={
                    "service": "QualityGate",
                    "version_id": str(version_id),
                    "overall_score": overall_score,
                    "gate_result": gate_result.value,
                    "issues_count": len(issues),
                    "confidence_level": confidence_level
                }
            )
            
            return assessment
            
        except Exception as e:
            logger.error(
                f"Failed to assess version quality: {str(e)}",
                extra={
                    "service": "QualityGate",
                    "version_id": str(version_id),
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def validate_interactions(
        self, 
        version_id: UUID,
        interaction_ids: Optional[List[UUID]] = None
    ) -> Dict[str, Any]:
        """
        Validate user interactions for quality and consistency.
        
        Args:
            version_id: Version containing the interactions
            interaction_ids: Specific interactions to validate (all if None)
            
        Returns:
            Validation results with scores and recommendations
        """
        logger.info(
            f"Validating interactions for version: {version_id}",
            extra={
                "service": "QualityGate",
                "operation": "validate_interactions",
                "version_id": str(version_id),
                "interaction_count": len(interaction_ids) if interaction_ids else "all"
            }
        )
        
        try:
            # Get interactions to validate
            if interaction_ids:
                interactions = []
                for interaction_id in interaction_ids:
                    interaction = await self.preview_repository.find_preview_interaction_by_id(interaction_id)
                    if interaction:
                        interactions.append(interaction)
            else:
                interactions = await self.preview_repository.find_interactions_by_version(version_id)
            
            if not interactions:
                return {
                    "validation_score": 1.0,
                    "validated_interactions": 0,
                    "issues": [],
                    "recommendations": [],
                    "details": {"message": "No interactions to validate"}
                }
            
            validation_results = []
            total_impact_score = 0.0
            consistency_score = 0.0
            conflict_count = 0
            
            # Validate each interaction
            for interaction in interactions:
                result = await self._validate_single_interaction(interaction, interactions)
                validation_results.append(result)
                total_impact_score += result.get("impact_score", 0.0)
                consistency_score += result.get("consistency_score", 0.0)
                if result.get("has_conflicts", False):
                    conflict_count += 1
            
            # Calculate overall validation metrics
            avg_impact = total_impact_score / len(interactions)
            avg_consistency = consistency_score / len(interactions)
            conflict_ratio = conflict_count / len(interactions)
            
            # Determine overall validation score
            validation_score = (avg_consistency * 0.6 + (1.0 - conflict_ratio) * 0.4)
            
            # Generate issues and recommendations
            issues = []
            recommendations = []
            
            if conflict_ratio > 0.1:
                issues.append(f"High conflict rate: {conflict_ratio:.1%} of interactions have conflicts")
                recommendations.append("Review conflicting interactions and resolve inconsistencies")
            
            if avg_consistency < 0.7:
                issues.append(f"Low consistency score: {avg_consistency:.2f}")
                recommendations.append("Improve interaction consistency with established patterns")
            
            if avg_impact < 0.5:
                issues.append(f"Low impact score: {avg_impact:.2f}")
                recommendations.append("Focus on high-impact changes for better user experience")
            
            result = {
                "validation_score": validation_score,
                "validated_interactions": len(interactions),
                "average_impact_score": avg_impact,
                "average_consistency_score": avg_consistency,
                "conflict_ratio": conflict_ratio,
                "issues": issues,
                "recommendations": recommendations,
                "interaction_results": validation_results,
                "details": {
                    "total_interactions": len(interactions),
                    "conflicting_interactions": conflict_count,
                    "validation_timestamp": datetime.utcnow().isoformat()
                }
            }
            
            logger.info(
                f"Interaction validation completed for version {version_id}",
                extra={
                    "service": "QualityGate",
                    "version_id": str(version_id),
                    "validation_score": validation_score,
                    "interactions_count": len(interactions),
                    "conflict_count": conflict_count
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to validate interactions: {str(e)}",
                extra={
                    "service": "QualityGate",
                    "version_id": str(version_id),
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def recommend_quality_improvements(
        self, 
        version_id: UUID,
        target_score: float = 0.85
    ) -> Dict[str, Any]:
        """
        Generate quality improvement recommendations for a version.
        
        Args:
            version_id: Version to improve
            target_score: Target quality score to achieve
            
        Returns:
            Improvement recommendations and action plan
        """
        logger.info(
            f"Generating quality improvement recommendations for version: {version_id}",
            extra={
                "service": "QualityGate",
                "operation": "recommend_improvements",
                "version_id": str(version_id),
                "target_score": target_score
            }
        )
        
        try:
            # Get current quality assessment
            assessment = await self.assess_version_quality(version_id)
            
            if assessment.overall_score >= target_score:
                return {
                    "current_score": assessment.overall_score,
                    "target_score": target_score,
                    "improvement_needed": False,
                    "message": "Version already meets target quality score",
                    "recommendations": []
                }
            
            # Identify improvement opportunities
            score_gap = target_score - assessment.overall_score
            improvement_plan = []
            
            # Analyze each metric for improvement potential
            for metric, current_score in assessment.metric_scores.items():
                min_required = self.config.min_metric_scores.get(metric, 0.7)
                
                if current_score < min_required:
                    improvement_plan.append({
                        "metric": metric.value,
                        "current_score": current_score,
                        "target_score": min_required,
                        "priority": "high",
                        "improvement_potential": min_required - current_score,
                        "actions": self._get_improvement_actions(metric, current_score)
                    })
                elif current_score < target_score:
                    improvement_plan.append({
                        "metric": metric.value,
                        "current_score": current_score,
                        "target_score": target_score,
                        "priority": "medium",
                        "improvement_potential": target_score - current_score,
                        "actions": self._get_improvement_actions(metric, current_score)
                    })
            
            # Sort by improvement potential (prioritize high-impact improvements)
            improvement_plan.sort(key=lambda x: x["improvement_potential"], reverse=True)
            
            # Generate consolidated recommendations
            recommendations = []
            for item in improvement_plan[:5]:  # Top 5 improvements
                recommendations.extend(item["actions"])
            
            result = {
                "current_score": assessment.overall_score,
                "target_score": target_score,
                "score_gap": score_gap,
                "improvement_needed": True,
                "improvement_plan": improvement_plan,
                "recommendations": recommendations,
                "estimated_effort": self._estimate_improvement_effort(improvement_plan),
                "expected_timeline": self._estimate_improvement_timeline(improvement_plan),
                "details": {
                    "assessment_id": str(assessment.version_id),
                    "current_issues": assessment.issues,
                    "confidence_level": assessment.confidence_level,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
            logger.info(
                f"Generated improvement recommendations for version {version_id}",
                extra={
                    "service": "QualityGate",
                    "version_id": str(version_id),
                    "current_score": assessment.overall_score,
                    "target_score": target_score,
                    "recommendations_count": len(recommendations)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to generate improvement recommendations: {str(e)}",
                extra={
                    "service": "QualityGate",
                    "version_id": str(version_id),
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    async def get_quality_trends(
        self, 
        request_id: UUID,
        phase: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze quality trends for a generation request.
        
        Args:
            request_id: Request to analyze
            phase: Specific phase to analyze (all phases if None)
            
        Returns:
            Quality trend analysis and insights
        """
        logger.info(
            f"Analyzing quality trends for request: {request_id}",
            extra={
                "service": "QualityGate",
                "operation": "get_quality_trends",
                "request_id": str(request_id),
                "phase": phase
            }
        )
        
        try:
            # Get versions for analysis
            versions = await self.preview_repository.find_preview_versions_by_request(request_id, phase)
            
            if not versions:
                return {
                    "request_id": str(request_id),
                    "phase": phase,
                    "versions_analyzed": 0,
                    "trends": {},
                    "message": "No versions available for trend analysis"
                }
            
            # Assess quality for each version
            assessments = []
            for version in versions:
                try:
                    assessment = await self.assess_version_quality(version.version_id)
                    assessments.append(assessment)
                except Exception as e:
                    logger.warning(f"Failed to assess version {version.version_id}: {e}")
                    continue
            
            if not assessments:
                return {
                    "request_id": str(request_id),
                    "phase": phase,
                    "versions_analyzed": 0,
                    "trends": {},
                    "message": "No successful quality assessments available"
                }
            
            # Analyze trends
            trends = self._analyze_quality_trends(assessments)
            
            result = {
                "request_id": str(request_id),
                "phase": phase,
                "versions_analyzed": len(assessments),
                "trends": trends,
                "latest_assessment": {
                    "overall_score": assessments[-1].overall_score,
                    "gate_result": assessments[-1].gate_result.value,
                    "assessed_at": assessments[-1].assessed_at.isoformat()
                },
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Quality trend analysis completed for request {request_id}",
                extra={
                    "service": "QualityGate",
                    "request_id": str(request_id),
                    "versions_analyzed": len(assessments),
                    "trend_direction": trends.get("overall_trend", "unknown")
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to analyze quality trends: {str(e)}",
                extra={
                    "service": "QualityGate",
                    "request_id": str(request_id),
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    # ===== Private Helper Methods =====
    
    async def _assess_visual_quality(self, version: PreviewVersionEntity) -> Tuple[float, Dict[str, Any]]:
        """Assess visual quality of version."""
        # Placeholder implementation - in production would use AI/ML models
        base_score = version.quality_score or 0.8
        
        # Adjust based on file size (larger files often mean higher quality)
        if version.file_size_bytes:
            size_factor = min(1.0, version.file_size_bytes / (1024 * 1024))  # 1MB baseline
            base_score *= (0.8 + 0.2 * size_factor)
        
        # Adjust based on generation time (more time often means better quality)
        if version.generation_time_ms:
            time_factor = min(1.0, version.generation_time_ms / 30000)  # 30s baseline
            base_score *= (0.9 + 0.1 * time_factor)
        
        visual_score = min(1.0, max(0.0, base_score))
        
        details = {
            "base_quality_score": version.quality_score,
            "size_factor": version.file_size_bytes / (1024 * 1024) if version.file_size_bytes else None,
            "time_factor": version.generation_time_ms / 1000 if version.generation_time_ms else None,
            "assessed_score": visual_score
        }
        
        return visual_score, details
    
    async def _assess_technical_quality(self, version: PreviewVersionEntity) -> Tuple[float, Dict[str, Any]]:
        """Assess technical quality of version."""
        score = 0.8  # Base technical score
        
        # Check version data structure completeness
        if version.version_data:
            required_keys = ['content', 'metadata', 'layout']
            present_keys = [key for key in required_keys if key in version.version_data]
            completeness = len(present_keys) / len(required_keys)
            score *= (0.7 + 0.3 * completeness)
        
        # Check asset availability
        if version.asset_urls:
            asset_count = len(version.asset_urls)
            score *= min(1.0, 0.8 + 0.2 * (asset_count / 5))  # 5 assets as optimal
        
        technical_score = min(1.0, max(0.0, score))
        
        details = {
            "version_data_completeness": len(version.version_data) if version.version_data else 0,
            "asset_count": len(version.asset_urls) if version.asset_urls else 0,
            "has_thumbnail": version.thumbnail_url is not None,
            "assessed_score": technical_score
        }
        
        return technical_score, details
    
    async def _assess_content_accuracy(self, version: PreviewVersionEntity) -> Tuple[float, Dict[str, Any]]:
        """Assess content accuracy of version."""
        # Placeholder implementation - would use NLP/content analysis in production
        score = 0.75
        
        if version.version_data:
            # Simulate content analysis
            complexity = version.calculate_complexity_score()
            score *= (0.8 + 0.2 * (1.0 - complexity))  # Lower complexity = higher accuracy
        
        content_score = min(1.0, max(0.0, score))
        
        details = {
            "complexity_score": version.calculate_complexity_score(),
            "content_size": len(str(version.version_data)) if version.version_data else 0,
            "assessed_score": content_score
        }
        
        return content_score, details
    
    async def _assess_performance(self, version: PreviewVersionEntity) -> Tuple[float, Dict[str, Any]]:
        """Assess performance characteristics of version."""
        score = 0.8
        
        # Generation time assessment (faster is better)
        if version.generation_time_ms:
            if version.generation_time_ms < 10000:  # < 10 seconds is excellent
                time_score = 1.0
            elif version.generation_time_ms < 30000:  # < 30 seconds is good
                time_score = 0.8
            elif version.generation_time_ms < 60000:  # < 1 minute is acceptable
                time_score = 0.6
            else:
                time_score = 0.4
            
            score *= time_score
        
        # File size efficiency (smaller relative to quality is better)
        if version.file_size_bytes and version.quality_level:
            expected_size = version.quality_level * 500000  # 500KB per quality level
            if version.file_size_bytes <= expected_size:
                size_score = 1.0
            else:
                size_score = max(0.4, expected_size / version.file_size_bytes)
            
            score *= size_score
        
        performance_score = min(1.0, max(0.0, score))
        
        details = {
            "generation_time_ms": version.generation_time_ms,
            "file_size_bytes": version.file_size_bytes,
            "quality_level": version.quality_level,
            "assessed_score": performance_score
        }
        
        return performance_score, details
    
    async def _assess_consistency(self, version: PreviewVersionEntity) -> Tuple[float, Dict[str, Any]]:
        """Assess consistency with other versions in the same phase."""
        score = 0.8  # Base consistency score
        
        # Get other versions in the same phase for comparison
        try:
            other_versions = await self.preview_repository.find_preview_versions_by_request(
                version.request_id,
                version.phase
            )
            
            if len(other_versions) > 1:
                # Compare quality levels
                quality_levels = [v.quality_level for v in other_versions]
                quality_variance = max(quality_levels) - min(quality_levels)
                consistency_factor = 1.0 - (quality_variance / 4.0)  # Max variance is 4 (levels 1-5)
                score *= max(0.6, consistency_factor)
        except:
            pass  # Use base score if comparison fails
        
        consistency_score = min(1.0, max(0.0, score))
        
        details = {
            "phase": version.phase,
            "quality_level": version.quality_level,
            "assessed_score": consistency_score
        }
        
        return consistency_score, details
    
    async def _assess_user_feedback(self, version: PreviewVersionEntity) -> Tuple[float, Dict[str, Any]]:
        """Assess user feedback for the version."""
        try:
            interactions = await self.preview_repository.find_interactions_by_version(version.version_id)
            
            if not interactions:
                return 0.7, {"interaction_count": 0, "message": "No user interactions available"}
            
            # Calculate feedback metrics
            total_interactions = len(interactions)
            positive_interactions = len([i for i in interactions if i.interaction_type == "approval"])
            negative_interactions = len([i for i in interactions if i.interaction_type == "rejection"])
            
            # Calculate average impact score
            impact_scores = [i.calculate_impact_score() for i in interactions]
            avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0.5
            
            # Calculate feedback score
            if total_interactions == 0:
                feedback_score = 0.7  # Neutral score for no feedback
            else:
                approval_ratio = positive_interactions / total_interactions
                rejection_ratio = negative_interactions / total_interactions
                feedback_score = approval_ratio - (rejection_ratio * 0.5) + (avg_impact * 0.3)
            
            feedback_score = min(1.0, max(0.0, feedback_score))
            
            details = {
                "total_interactions": total_interactions,
                "positive_interactions": positive_interactions,
                "negative_interactions": negative_interactions,
                "average_impact_score": avg_impact,
                "assessed_score": feedback_score
            }
            
            return feedback_score, details
            
        except Exception as e:
            logger.warning(f"Failed to assess user feedback: {e}")
            return 0.7, {"error": str(e), "assessed_score": 0.7}
    
    def _calculate_overall_score(self, metric_scores: Dict[QualityMetric, float]) -> float:
        """Calculate weighted overall quality score."""
        weights = {
            QualityMetric.VISUAL_QUALITY: self.config.visual_weight,
            QualityMetric.TECHNICAL_QUALITY: self.config.technical_weight,
            QualityMetric.CONTENT_ACCURACY: 0.2,
            QualityMetric.USER_FEEDBACK: self.config.feedback_weight,
            QualityMetric.PERFORMANCE: self.config.performance_weight,
            QualityMetric.CONSISTENCY: 0.1
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric, score in metric_scores.items():
            weight = weights.get(metric, 0.1)
            weighted_sum += score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _determine_gate_result(
        self, 
        overall_score: float, 
        metric_scores: Dict[QualityMetric, float]
    ) -> QualityGateResult:
        """Determine quality gate result based on scores and thresholds."""
        # Check if any metric fails minimum threshold
        for metric, score in metric_scores.items():
            min_threshold = self.config.min_metric_scores.get(metric, 0.6)
            if score < min_threshold:
                return QualityGateResult.FAILED
        
        # Check overall score
        if overall_score >= self.config.auto_promote_threshold:
            return QualityGateResult.PASSED
        elif overall_score >= self.config.min_overall_score:
            return QualityGateResult.NEEDS_REVIEW if self.config.require_user_approval else QualityGateResult.PASSED
        elif overall_score >= 0.6:
            return QualityGateResult.WARNING
        else:
            return QualityGateResult.FAILED
    
    def _identify_issues(
        self, 
        metric_scores: Dict[QualityMetric, float], 
        assessment_details: Dict[str, Any]
    ) -> List[str]:
        """Identify quality issues based on assessment results."""
        issues = []
        
        for metric, score in metric_scores.items():
            min_threshold = self.config.min_metric_scores.get(metric, 0.6)
            if score < min_threshold:
                issues.append(f"Low {metric.value} score: {score:.2f} (minimum: {min_threshold:.2f})")
        
        return issues
    
    def _generate_recommendations(
        self, 
        metric_scores: Dict[QualityMetric, float], 
        assessment_details: Dict[str, Any],
        version: PreviewVersionEntity
    ) -> List[str]:
        """Generate improvement recommendations based on assessment."""
        recommendations = []
        
        for metric, score in metric_scores.items():
            if score < 0.8:  # Below good threshold
                recommendations.extend(self._get_improvement_actions(metric, score))
        
        return recommendations
    
    def _get_improvement_actions(self, metric: QualityMetric, current_score: float) -> List[str]:
        """Get specific improvement actions for a metric."""
        actions = {
            QualityMetric.VISUAL_QUALITY: [
                "Increase generation quality level",
                "Review and adjust visual parameters",
                "Consider re-generating with higher resolution"
            ],
            QualityMetric.TECHNICAL_QUALITY: [
                "Ensure all required data fields are present",
                "Add missing asset references",
                "Validate data structure completeness"
            ],
            QualityMetric.CONTENT_ACCURACY: [
                "Review content against original requirements",
                "Validate text and dialogue accuracy",
                "Check character and scene consistency"
            ],
            QualityMetric.USER_FEEDBACK: [
                "Address user feedback and suggestions",
                "Implement approved user modifications",
                "Gather additional user input"
            ],
            QualityMetric.PERFORMANCE: [
                "Optimize generation parameters",
                "Consider quality vs speed trade-offs",
                "Review system resource usage"
            ],
            QualityMetric.CONSISTENCY: [
                "Ensure consistency with other versions",
                "Review style and format standards",
                "Validate against project guidelines"
            ]
        }
        
        return actions.get(metric, ["Review and improve this quality aspect"])
    
    def _calculate_confidence_level(
        self, 
        metric_scores: Dict[QualityMetric, float], 
        assessment_details: Dict[str, Any]
    ) -> float:
        """Calculate confidence level in the assessment."""
        # Base confidence on score consistency and data availability
        score_variance = max(metric_scores.values()) - min(metric_scores.values())
        consistency_factor = 1.0 - (score_variance / 2.0)
        
        # Factor in data completeness
        data_factors = []
        for details in assessment_details.values():
            if isinstance(details, dict) and 'assessed_score' in details:
                data_factors.append(0.9)  # High confidence when assessment succeeded
            else:
                data_factors.append(0.5)  # Lower confidence when assessment was limited
        
        data_completeness = sum(data_factors) / len(data_factors) if data_factors else 0.5
        
        confidence = (consistency_factor * 0.4 + data_completeness * 0.6)
        return min(1.0, max(0.1, confidence))
    
    async def _validate_single_interaction(
        self, 
        interaction: PreviewInteractionEntity,
        all_interactions: List[PreviewInteractionEntity]
    ) -> Dict[str, Any]:
        """Validate a single interaction for quality and consistency."""
        # Calculate interaction impact
        impact_score = interaction.calculate_impact_score()
        
        # Check for conflicts with other interactions
        conflicts = []
        for other in all_interactions:
            if (other.interaction_id != interaction.interaction_id and 
                other.element_id == interaction.element_id and
                other.change_type != interaction.change_type):
                conflicts.append(str(other.interaction_id))
        
        # Calculate consistency score
        consistency_score = 0.8 if not conflicts else max(0.3, 0.8 - len(conflicts) * 0.1)
        
        return {
            "interaction_id": str(interaction.interaction_id),
            "impact_score": impact_score,
            "consistency_score": consistency_score,
            "has_conflicts": len(conflicts) > 0,
            "conflict_count": len(conflicts),
            "conflicting_interactions": conflicts
        }
    
    def _analyze_quality_trends(self, assessments: List[QualityAssessment]) -> Dict[str, Any]:
        """Analyze quality trends across multiple assessments."""
        if len(assessments) < 2:
            return {"trend": "insufficient_data", "message": "Need at least 2 assessments for trend analysis"}
        
        # Sort by assessment time
        sorted_assessments = sorted(assessments, key=lambda x: x.assessed_at)
        
        # Calculate trend direction
        first_score = sorted_assessments[0].overall_score
        last_score = sorted_assessments[-1].overall_score
        
        if last_score > first_score + 0.05:
            trend_direction = "improving"
        elif last_score < first_score - 0.05:
            trend_direction = "declining"
        else:
            trend_direction = "stable"
        
        # Calculate metric trends
        metric_trends = {}
        for metric in QualityMetric:
            if metric in sorted_assessments[0].metric_scores:
                first_metric_score = sorted_assessments[0].metric_scores[metric]
                last_metric_score = sorted_assessments[-1].metric_scores[metric]
                
                if last_metric_score > first_metric_score + 0.05:
                    metric_trends[metric.value] = "improving"
                elif last_metric_score < first_metric_score - 0.05:
                    metric_trends[metric.value] = "declining"
                else:
                    metric_trends[metric.value] = "stable"
        
        return {
            "overall_trend": trend_direction,
            "score_change": last_score - first_score,
            "first_score": first_score,
            "last_score": last_score,
            "assessment_count": len(assessments),
            "metric_trends": metric_trends,
            "time_span_hours": (sorted_assessments[-1].assessed_at - sorted_assessments[0].assessed_at).total_seconds() / 3600
        }
    
    def _estimate_improvement_effort(self, improvement_plan: List[Dict[str, Any]]) -> str:
        """Estimate effort required for improvements."""
        total_potential = sum(item["improvement_potential"] for item in improvement_plan)
        
        if total_potential < 0.1:
            return "low"
        elif total_potential < 0.3:
            return "medium" 
        else:
            return "high"
    
    def _estimate_improvement_timeline(self, improvement_plan: List[Dict[str, Any]]) -> str:
        """Estimate timeline for improvements."""
        high_priority_count = len([item for item in improvement_plan if item["priority"] == "high"])
        
        if high_priority_count == 0:
            return "1-2 hours"
        elif high_priority_count <= 2:
            return "2-4 hours"
        else:
            return "4-8 hours"
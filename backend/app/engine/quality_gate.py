"""QualityGateSystem - 品質ゲートシステム

設計書要件:
- 品質スコア管理（各フェーズ0.70以上の閾値）
- 自動リトライ（最大3回）
- 管理者オーバーライド機能
- フォールバック・プレースホルダー生成
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from uuid import UUID
from enum import Enum, IntEnum
from dataclasses import dataclass
import json
from statistics import mean, stdev

from app.core.logging import LoggerMixin
from app.core.redis_client import redis_manager
from app.domain.manga.value_objects import QualityMetrics, QualityCheck


class QualityLevel(IntEnum):
    """Quality assessment levels."""
    CRITICAL_FAILURE = 1  # 0.0 - 0.2
    POOR = 2             # 0.2 - 0.4
    BELOW_AVERAGE = 3    # 0.4 - 0.6
    ACCEPTABLE = 4       # 0.6 - 0.8
    GOOD = 5             # 0.8 - 1.0


class QualityDimension(Enum):
    """Quality assessment dimensions."""
    COMPLETENESS = "completeness"      # 完成度
    CONSISTENCY = "consistency"        # 一貫性
    CREATIVITY = "creativity"          # 創造性
    TECHNICAL = "technical"            # 技術品質
    NARRATIVE = "narrative"            # 物語性
    VISUAL = "visual"                  # 視覚品質


class GateAction(Enum):
    """Quality gate actions."""
    PASS = "pass"                      # 通過
    RETRY = "retry"                    # リトライ
    FALLBACK = "fallback"              # フォールバック
    MANUAL_REVIEW = "manual_review"    # 手動審査
    OVERRIDE = "override"              # オーバーライド


@dataclass
class QualityAssessment:
    """Quality assessment result."""
    phase_number: int
    overall_score: float
    dimension_scores: Dict[str, float]
    gate_action: GateAction
    issues: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]
    assessed_at: datetime


@dataclass
class QualityRule:
    """Quality evaluation rule."""
    name: str
    phase_numbers: List[int]
    dimension: QualityDimension
    evaluator_func: str  # Function name
    weight: float
    threshold: float
    critical: bool = False


class QualityGateSystem(LoggerMixin):
    """品質ゲートシステム
    
    各フェーズの品質評価・自動リトライ・フォールバック処理を管理。
    0.70以上の品質閾値・3回リトライ・管理者オーバーライド対応。
    """
    
    def __init__(self, redis_client=None):
        """Initialize QualityGateSystem.
        
        Args:
            redis_client: Redisクライアント
        """
        super().__init__()
        self.redis_client = redis_client or redis_manager
        
        # Quality thresholds by phase
        self.phase_thresholds = {
            1: 0.70,  # Concept analysis
            2: 0.75,  # Character design  
            3: 0.70,  # Plot structure
            4: 0.80,  # Name generation (critical)
            5: 0.85,  # Image generation (critical)
            6: 0.75,  # Dialogue placement
            7: 0.80   # Final integration
        }
        
        # Quality rules by phase
        self.quality_rules = self._initialize_quality_rules()
        
        # Assessment cache
        self.assessment_cache: Dict[str, QualityAssessment] = {}
        
        # Override permissions
        self.override_permissions: Dict[str, List[int]] = {}  # user_id -> allowed phases
        
        # Statistics
        self.stats = {
            "total_assessments": 0,
            "passed_assessments": 0,
            "failed_assessments": 0,
            "retry_attempts": 0,
            "fallback_activations": 0,
            "manual_reviews": 0,
            "overrides": 0,
            "phase_success_rates": {i: 0.0 for i in range(1, 8)},
            "average_scores_by_phase": {i: 0.0 for i in range(1, 8)}
        }
    
    def _initialize_quality_rules(self) -> List[QualityRule]:
        """Initialize quality evaluation rules."""
        rules = [
            # Phase 1: Concept Analysis
            QualityRule(
                name="concept_completeness",
                phase_numbers=[1],
                dimension=QualityDimension.COMPLETENESS,
                evaluator_func="_evaluate_concept_completeness",
                weight=0.4,
                threshold=0.7,
                critical=True
            ),
            QualityRule(
                name="concept_consistency",
                phase_numbers=[1],
                dimension=QualityDimension.CONSISTENCY,
                evaluator_func="_evaluate_concept_consistency",
                weight=0.3,
                threshold=0.6
            ),
            QualityRule(
                name="concept_creativity",
                phase_numbers=[1],
                dimension=QualityDimension.CREATIVITY,
                evaluator_func="_evaluate_concept_creativity",
                weight=0.3,
                threshold=0.5
            ),
            
            # Phase 2: Character Design
            QualityRule(
                name="character_completeness",
                phase_numbers=[2],
                dimension=QualityDimension.COMPLETENESS,
                evaluator_func="_evaluate_character_completeness",
                weight=0.3,
                threshold=0.7,
                critical=True
            ),
            QualityRule(
                name="character_consistency",
                phase_numbers=[2],
                dimension=QualityDimension.CONSISTENCY,
                evaluator_func="_evaluate_character_consistency",
                weight=0.3,
                threshold=0.7
            ),
            QualityRule(
                name="character_visual_quality",
                phase_numbers=[2],
                dimension=QualityDimension.VISUAL,
                evaluator_func="_evaluate_character_visual_quality",
                weight=0.4,
                threshold=0.6
            ),
            
            # Phase 3: Plot Structure
            QualityRule(
                name="plot_completeness",
                phase_numbers=[3],
                dimension=QualityDimension.COMPLETENESS,
                evaluator_func="_evaluate_plot_completeness",
                weight=0.3,
                threshold=0.7,
                critical=True
            ),
            QualityRule(
                name="plot_narrative_quality",
                phase_numbers=[3],
                dimension=QualityDimension.NARRATIVE,
                evaluator_func="_evaluate_plot_narrative_quality",
                weight=0.4,
                threshold=0.6
            ),
            QualityRule(
                name="plot_consistency",
                phase_numbers=[3],
                dimension=QualityDimension.CONSISTENCY,
                evaluator_func="_evaluate_plot_consistency",
                weight=0.3,
                threshold=0.6
            ),
            
            # Phase 4: Name Generation
            QualityRule(
                name="name_technical_quality",
                phase_numbers=[4],
                dimension=QualityDimension.TECHNICAL,
                evaluator_func="_evaluate_name_technical_quality",
                weight=0.5,
                threshold=0.8,
                critical=True
            ),
            QualityRule(
                name="name_completeness",
                phase_numbers=[4],
                dimension=QualityDimension.COMPLETENESS,
                evaluator_func="_evaluate_name_completeness",
                weight=0.3,
                threshold=0.8,
                critical=True
            ),
            QualityRule(
                name="name_consistency",
                phase_numbers=[4],
                dimension=QualityDimension.CONSISTENCY,
                evaluator_func="_evaluate_name_consistency",
                weight=0.2,
                threshold=0.7
            ),
            
            # Phase 5: Image Generation
            QualityRule(
                name="image_visual_quality",
                phase_numbers=[5],
                dimension=QualityDimension.VISUAL,
                evaluator_func="_evaluate_image_visual_quality",
                weight=0.6,
                threshold=0.8,
                critical=True
            ),
            QualityRule(
                name="image_technical_quality",
                phase_numbers=[5],
                dimension=QualityDimension.TECHNICAL,
                evaluator_func="_evaluate_image_technical_quality",
                weight=0.3,
                threshold=0.7,
                critical=True
            ),
            QualityRule(
                name="image_consistency",
                phase_numbers=[5],
                dimension=QualityDimension.CONSISTENCY,
                evaluator_func="_evaluate_image_consistency",
                weight=0.1,
                threshold=0.7
            ),
            
            # Phase 6: Dialogue Placement
            QualityRule(
                name="dialogue_technical_quality",
                phase_numbers=[6],
                dimension=QualityDimension.TECHNICAL,
                evaluator_func="_evaluate_dialogue_technical_quality",
                weight=0.4,
                threshold=0.7
            ),
            QualityRule(
                name="dialogue_completeness",
                phase_numbers=[6],
                dimension=QualityDimension.COMPLETENESS,
                evaluator_func="_evaluate_dialogue_completeness",
                weight=0.3,
                threshold=0.7
            ),
            QualityRule(
                name="dialogue_visual_quality",
                phase_numbers=[6],
                dimension=QualityDimension.VISUAL,
                evaluator_func="_evaluate_dialogue_visual_quality",
                weight=0.3,
                threshold=0.6
            ),
            
            # Phase 7: Final Integration
            QualityRule(
                name="integration_completeness",
                phase_numbers=[7],
                dimension=QualityDimension.COMPLETENESS,
                evaluator_func="_evaluate_integration_completeness",
                weight=0.3,
                threshold=0.8,
                critical=True
            ),
            QualityRule(
                name="integration_consistency",
                phase_numbers=[7],
                dimension=QualityDimension.CONSISTENCY,
                evaluator_func="_evaluate_integration_consistency",
                weight=0.3,
                threshold=0.8,
                critical=True
            ),
            QualityRule(
                name="integration_technical_quality",
                phase_numbers=[7],
                dimension=QualityDimension.TECHNICAL,
                evaluator_func="_evaluate_integration_technical_quality",
                weight=0.4,
                threshold=0.7
            )
        ]
        
        return rules
    
    async def evaluate_phase_result(
        self,
        phase_number: int,
        phase_result: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> QualityCheck:
        """Evaluate phase result quality.
        
        Args:
            phase_number: Phase number (1-7)
            phase_result: Phase result data
            context: Additional context for evaluation
            
        Returns:
            QualityCheck result
        """
        try:
            # Get applicable rules for this phase
            phase_rules = [
                rule for rule in self.quality_rules 
                if phase_number in rule.phase_numbers
            ]
            
            if not phase_rules:
                # No rules defined, return default pass
                return QualityCheck(
                    phase_number=phase_number,
                    score=0.8,  # Default pass score
                    passed=True,
                    issues=[],
                    recommendations=[],
                    metadata={"default_evaluation": True}
                )
            
            # Evaluate each rule
            dimension_scores = {}
            all_issues = []
            all_recommendations = []
            rule_results = []
            
            for rule in phase_rules:
                try:
                    evaluator = getattr(self, rule.evaluator_func)
                    score, issues, recommendations = await evaluator(
                        phase_result, context or {}
                    )
                    
                    rule_results.append({
                        "rule": rule.name,
                        "score": score,
                        "weight": rule.weight,
                        "threshold": rule.threshold,
                        "critical": rule.critical,
                        "passed": score >= rule.threshold
                    })
                    
                    # Accumulate dimension scores
                    dim_name = rule.dimension.value
                    if dim_name not in dimension_scores:
                        dimension_scores[dim_name] = []
                    dimension_scores[dim_name].append((score, rule.weight))
                    
                    # Collect issues and recommendations
                    all_issues.extend(issues)
                    all_recommendations.extend(recommendations)
                    
                except Exception as e:
                    self.logger.error(f"Rule evaluation failed: {rule.name} - {e}")
                    # Continue with other rules
            
            # Calculate weighted overall score
            total_weighted_score = 0.0
            total_weight = 0.0
            
            for result in rule_results:
                weight = result["weight"]
                score = result["score"]
                total_weighted_score += score * weight
                total_weight += weight
            
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
            
            # Calculate dimension averages
            averaged_dimensions = {}
            for dim_name, scores_weights in dimension_scores.items():
                weighted_sum = sum(score * weight for score, weight in scores_weights)
                total_weight = sum(weight for _, weight in scores_weights)
                averaged_dimensions[dim_name] = weighted_sum / total_weight if total_weight > 0 else 0.0
            
            # Check threshold
            threshold = self.phase_thresholds.get(phase_number, 0.70)
            passed = overall_score >= threshold
            
            # Check critical failures
            critical_failures = [
                result for result in rule_results 
                if result["critical"] and not result["passed"]
            ]
            
            if critical_failures:
                passed = False
                all_issues.append("Critical quality rules failed")
            
            # Create assessment
            assessment = QualityAssessment(
                phase_number=phase_number,
                overall_score=overall_score,
                dimension_scores=averaged_dimensions,
                gate_action=self._determine_gate_action(overall_score, threshold, critical_failures),
                issues=list(set(all_issues)),  # Remove duplicates
                recommendations=list(set(all_recommendations)),
                metadata={
                    "rule_results": rule_results,
                    "threshold": threshold,
                    "critical_failures": len(critical_failures),
                    "evaluation_time": datetime.utcnow().isoformat()
                },
                assessed_at=datetime.utcnow()
            )
            
            # Cache assessment
            cache_key = self._generate_assessment_cache_key(phase_number, phase_result)
            self.assessment_cache[cache_key] = assessment
            
            # Update statistics
            await self._update_statistics(assessment)
            
            # Create QualityCheck result
            quality_check = QualityCheck(
                phase_number=phase_number,
                score=overall_score,
                passed=passed,
                issues=all_issues,
                recommendations=all_recommendations,
                metadata={
                    "dimension_scores": averaged_dimensions,
                    "gate_action": assessment.gate_action.value,
                    "assessment_id": cache_key
                }
            )
            
            self.logger.info(
                f"Phase {phase_number} quality evaluation: "
                f"score={overall_score:.3f}, passed={passed}, action={assessment.gate_action.value}"
            )
            
            return quality_check
            
        except Exception as e:
            self.logger.error(f"Phase {phase_number} quality evaluation failed: {e}")
            
            # Return fallback evaluation
            return QualityCheck(
                phase_number=phase_number,
                score=0.5,  # Neutral score
                passed=False,
                issues=[f"Quality evaluation error: {str(e)}"],
                recommendations=["Manual review recommended"],
                metadata={"evaluation_error": True}
            )
    
    async def evaluate_overall_quality(
        self,
        all_phase_results: Dict[int, Dict[str, Any]]
    ) -> QualityCheck:
        """Evaluate overall manga generation quality.
        
        Args:
            all_phase_results: Results from all phases
            
        Returns:
            Overall quality assessment
        """
        phase_scores = []
        all_issues = []
        all_recommendations = []
        dimension_aggregates = {}
        
        # Evaluate each phase
        for phase_number, phase_result in all_phase_results.items():
            phase_check = await self.evaluate_phase_result(phase_number, phase_result)
            phase_scores.append(phase_check.score)
            all_issues.extend(phase_check.issues)
            all_recommendations.extend(phase_check.recommendations)
            
            # Aggregate dimensions
            if "dimension_scores" in phase_check.metadata:
                for dim, score in phase_check.metadata["dimension_scores"].items():
                    if dim not in dimension_aggregates:
                        dimension_aggregates[dim] = []
                    dimension_aggregates[dim].append(score)
        
        # Calculate overall metrics
        overall_score = mean(phase_scores) if phase_scores else 0.0
        consistency_score = 1.0 - (stdev(phase_scores) / 10.0) if len(phase_scores) > 1 else 1.0
        
        # Calculate dimension averages
        averaged_dimensions = {
            dim: mean(scores) for dim, scores in dimension_aggregates.items()
        }
        
        # Overall assessment
        passed = overall_score >= 0.75  # Higher threshold for overall quality
        
        return QualityCheck(
            phase_number=0,  # Overall evaluation
            score=overall_score,
            passed=passed,
            issues=list(set(all_issues)),
            recommendations=list(set(all_recommendations)),
            metadata={
                "phase_scores": {i: score for i, score in enumerate(phase_scores, 1)},
                "consistency_score": consistency_score,
                "dimension_scores": averaged_dimensions,
                "total_phases": len(phase_scores)
            }
        )
    
    def _determine_gate_action(
        self,
        score: float,
        threshold: float,
        critical_failures: List[Dict[str, Any]]
    ) -> GateAction:
        """Determine appropriate gate action based on score and failures.
        
        Args:
            score: Overall quality score
            threshold: Required threshold
            critical_failures: List of critical failures
            
        Returns:
            Recommended gate action
        """
        # Critical failures always trigger retry
        if critical_failures:
            return GateAction.RETRY
        
        # Score-based action determination
        if score >= threshold:
            return GateAction.PASS
        elif score >= threshold * 0.8:  # Close to threshold
            return GateAction.RETRY
        elif score >= threshold * 0.5:  # Moderate quality
            return GateAction.MANUAL_REVIEW
        else:  # Very low quality
            return GateAction.FALLBACK
    
    async def apply_override(
        self,
        user_id: str,
        phase_number: int,
        assessment_id: str,
        override_reason: str
    ) -> bool:
        """Apply quality override for assessment.
        
        Args:
            user_id: User requesting override
            phase_number: Phase number
            assessment_id: Assessment identifier
            override_reason: Reason for override
            
        Returns:
            Success flag
        """
        # Check override permissions
        user_permissions = self.override_permissions.get(user_id, [])
        if phase_number not in user_permissions and "all" not in user_permissions:
            self.logger.warning(f"User {user_id} lacks override permission for phase {phase_number}")
            return False
        
        # Find assessment
        if assessment_id not in self.assessment_cache:
            self.logger.warning(f"Assessment {assessment_id} not found for override")
            return False
        
        assessment = self.assessment_cache[assessment_id]
        
        # Apply override
        assessment.gate_action = GateAction.OVERRIDE
        assessment.metadata["override"] = {
            "user_id": user_id,
            "reason": override_reason,
            "timestamp": datetime.utcnow().isoformat(),
            "original_action": assessment.gate_action.value
        }
        
        # Log override
        self.logger.info(
            f"Quality override applied by {user_id} for phase {phase_number}: {override_reason}"
        )
        
        # Update statistics
        self.stats["overrides"] += 1
        
        return True
    
    async def generate_fallback_result(
        self,
        phase_number: int,
        phase_input: Dict[str, Any],
        failure_reason: str
    ) -> Dict[str, Any]:
        """Generate fallback result when quality gates fail.
        
        Args:
            phase_number: Phase number
            phase_input: Original phase input
            failure_reason: Reason for fallback
            
        Returns:
            Fallback result data
        """
        fallback_generators = {
            1: self._generate_concept_fallback,
            2: self._generate_character_fallback,
            3: self._generate_plot_fallback,
            4: self._generate_name_fallback,
            5: self._generate_image_fallback,
            6: self._generate_dialogue_fallback,
            7: self._generate_integration_fallback
        }
        
        generator = fallback_generators.get(phase_number)
        if not generator:
            # Generic fallback
            return {
                "status": "fallback",
                "phase_number": phase_number,
                "failure_reason": failure_reason,
                "fallback_data": {
                    "message": f"Phase {phase_number} fallback result",
                    "quality_level": "minimal",
                    "generated_at": datetime.utcnow().isoformat()
                },
                "metadata": {
                    "is_fallback": True,
                    "original_input": phase_input
                }
            }
        
        return await generator(phase_input, failure_reason)
    
    def _generate_assessment_cache_key(
        self,
        phase_number: int,
        phase_result: Dict[str, Any]
    ) -> str:
        """Generate cache key for assessment."""
        import hashlib
        result_str = json.dumps(phase_result, sort_keys=True)
        result_hash = hashlib.md5(result_str.encode()).hexdigest()[:8]
        timestamp = int(datetime.utcnow().timestamp())
        
        return f"assessment_{phase_number}_{result_hash}_{timestamp}"
    
    async def _update_statistics(self, assessment: QualityAssessment):
        """Update quality system statistics."""
        self.stats["total_assessments"] += 1
        
        if assessment.gate_action == GateAction.PASS:
            self.stats["passed_assessments"] += 1
        else:
            self.stats["failed_assessments"] += 1
        
        # Update phase-specific statistics
        phase_num = assessment.phase_number
        current_avg = self.stats["average_scores_by_phase"][phase_num]
        total_for_phase = sum(
            1 for a in self.assessment_cache.values() 
            if a.phase_number == phase_num
        )
        
        # Update running average
        self.stats["average_scores_by_phase"][phase_num] = (
            (current_avg * (total_for_phase - 1) + assessment.overall_score) / total_for_phase
        )
        
        # Update success rate
        phase_successes = sum(
            1 for a in self.assessment_cache.values()
            if a.phase_number == phase_num and a.gate_action == GateAction.PASS
        )
        self.stats["phase_success_rates"][phase_num] = (phase_successes / total_for_phase * 100)
    
    # Phase-specific quality evaluators
    
    async def _evaluate_concept_completeness(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate concept completeness."""
        issues = []
        recommendations = []
        score = 1.0
        
        required_fields = ["concept", "genre", "themes", "world_setting"]
        for field in required_fields:
            if field not in result or not result[field]:
                issues.append(f"Missing required field: {field}")
                score -= 0.2
        
        # Check concept depth
        concept = result.get("concept", {})
        if isinstance(concept, dict):
            if len(concept.keys()) < 3:
                issues.append("Concept lacks sufficient detail")
                score -= 0.1
                recommendations.append("Expand concept with more specific details")
        
        # Check theme relevance
        themes = result.get("themes", [])
        if len(themes) < 2:
            issues.append("Insufficient thematic elements")
            score -= 0.1
            recommendations.append("Add more thematic depth")
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_concept_consistency(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate concept consistency."""
        issues = []
        recommendations = []
        score = 1.0
        
        genre = result.get("genre", "")
        themes = result.get("themes", [])
        world_setting = result.get("world_setting", {})
        
        # Check genre-theme consistency
        if genre == "少年漫画" and "romance" in [t.lower() for t in themes]:
            issues.append("Genre-theme mismatch: Shounen with heavy romance focus")
            score -= 0.2
            recommendations.append("Align themes with genre expectations")
        
        # Check world-genre consistency
        if genre == "現代" and world_setting.get("time_period") == "medieval":
            issues.append("Genre-setting temporal inconsistency")
            score -= 0.3
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_concept_creativity(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate concept creativity."""
        issues = []
        recommendations = []
        score = 0.7  # Base creativity score
        
        concept = result.get("concept", {})
        themes = result.get("themes", [])
        
        # Check for unique elements
        unique_indicators = ["original", "unique", "innovative", "new"]
        concept_text = str(concept).lower()
        
        unique_count = sum(1 for indicator in unique_indicators if indicator in concept_text)
        score += unique_count * 0.1
        
        # Check theme diversity
        if len(set(themes)) == len(themes):  # No duplicate themes
            score += 0.1
        
        # Penalty for overly generic concepts
        generic_terms = ["adventure", "friendship", "love", "hero"]
        generic_count = sum(1 for term in generic_terms if term.lower() in concept_text)
        score -= generic_count * 0.05
        
        if score < 0.6:
            recommendations.append("Consider adding more unique or innovative elements")
        
        return max(0.0, min(1.0, score)), issues, recommendations
    
    async def _evaluate_character_completeness(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate character completeness."""
        issues = []
        recommendations = []
        score = 1.0
        
        characters = result.get("characters", [])
        
        if not characters:
            issues.append("No characters defined")
            return 0.0, issues, ["Create at least one main character"]
        
        # Check each character completeness
        for i, char in enumerate(characters):
            required_fields = ["name", "description", "personality", "role"]
            missing_fields = [field for field in required_fields if not char.get(field)]
            
            if missing_fields:
                issues.append(f"Character {i+1} missing fields: {missing_fields}")
                score -= 0.2 / len(characters)
        
        # Check character diversity
        roles = [char.get("role", "") for char in characters]
        unique_roles = set(roles)
        
        if len(unique_roles) < len(roles) * 0.8:  # Too many similar roles
            issues.append("Characters lack role diversity")
            score -= 0.1
            recommendations.append("Diversify character roles")
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_character_consistency(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate character consistency."""
        issues = []
        recommendations = []
        score = 1.0
        
        characters = result.get("characters", [])
        
        # Check personality-role consistency
        for char in characters:
            personality = char.get("personality", [])
            role = char.get("role", "").lower()
            
            # Check for contradictions
            if role == "hero" and "cowardly" in [p.lower() for p in personality]:
                issues.append(f"Character {char.get('name', 'Unknown')} has conflicting traits")
                score -= 0.15
                recommendations.append("Resolve character trait conflicts")
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_character_visual_quality(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate character visual quality."""
        issues = []
        recommendations = []
        score = 0.8  # Base visual score
        
        characters = result.get("characters", [])
        
        for char in characters:
            visual_desc = char.get("visual_description", "")
            
            if not visual_desc:
                issues.append(f"Character {char.get('name', 'Unknown')} lacks visual description")
                score -= 0.2
                recommendations.append("Add detailed visual descriptions")
            elif len(visual_desc.split()) < 10:
                issues.append(f"Character {char.get('name', 'Unknown')} has minimal visual detail")
                score -= 0.1
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_plot_completeness(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate plot completeness."""
        issues = []
        recommendations = []
        score = 1.0
        
        story_structure = result.get("story_structure", {})
        scenes = result.get("scenes", [])
        
        if not story_structure:
            issues.append("Missing story structure")
            score -= 0.4
        
        if not scenes:
            issues.append("No scenes defined")
            score -= 0.5
            return max(0.0, score), issues, ["Create story scenes"]
        
        # Check for story arc completeness
        required_elements = ["beginning", "middle", "end"]
        structure_keys = [k.lower() for k in story_structure.keys()]
        
        missing_elements = [elem for elem in required_elements if elem not in str(structure_keys).lower()]
        if missing_elements:
            issues.append(f"Missing story elements: {missing_elements}")
            score -= 0.2
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_plot_narrative_quality(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate plot narrative quality."""
        issues = []
        recommendations = []
        score = 0.8  # Base narrative score
        
        scenes = result.get("scenes", [])
        
        if len(scenes) < 3:
            issues.append("Insufficient scene count for narrative development")
            score -= 0.3
            recommendations.append("Expand story with more scenes")
        
        # Check scene progression
        if scenes:
            emotion_levels = [scene.get("emotion_level", 5) for scene in scenes]
            if len(set(emotion_levels)) == 1:  # Flat emotional progression
                issues.append("Lacks emotional variation")
                score -= 0.2
                recommendations.append("Add emotional peaks and valleys")
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_plot_consistency(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate plot consistency."""
        issues = []
        recommendations = []
        score = 1.0
        
        # Implementation would check for plot holes, character consistency, etc.
        # For now, basic validation
        
        scenes = result.get("scenes", [])
        if scenes:
            # Check for character continuity
            all_characters = set()
            for scene in scenes:
                scene_chars = scene.get("characters", [])
                all_characters.update(scene_chars)
            
            # Basic consistency check
            if len(all_characters) == 0:
                issues.append("No character continuity across scenes")
                score -= 0.2
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_name_technical_quality(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate name technical quality."""
        issues = []
        recommendations = []
        score = 1.0
        
        panels = result.get("panels", [])
        layout = result.get("layout", {})
        
        if not panels:
            issues.append("No panels generated")
            return 0.0, issues, ["Generate panel layout"]
        
        # Check panel structure
        for i, panel in enumerate(panels):
            if not panel.get("position"):
                issues.append(f"Panel {i+1} missing position data")
                score -= 0.1
            
            if not panel.get("size"):
                issues.append(f"Panel {i+1} missing size data")
                score -= 0.1
        
        # Check layout validity
        if not layout:
            issues.append("Missing layout configuration")
            score -= 0.2
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_name_completeness(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate name completeness."""
        issues = []
        recommendations = []
        score = 1.0
        
        panels = result.get("panels", [])
        
        # Check minimum panel count
        if len(panels) < 4:
            issues.append("Insufficient panel count for complete story")
            score -= 0.3
            recommendations.append("Add more panels for story development")
        
        # Check panel content completeness
        for panel in panels:
            if not panel.get("description"):
                score -= 0.1
                issues.append("Panel missing content description")
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_name_consistency(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate name consistency."""
        issues = []
        recommendations = []
        score = 1.0
        
        panels = result.get("panels", [])
        layout = result.get("layout", {})
        
        # Check layout consistency
        if layout.get("type") == "grid":
            expected_positions = []
            actual_positions = [panel.get("position", {}) for panel in panels]
            
            # Basic grid consistency check
            if len(set(str(pos) for pos in actual_positions)) != len(actual_positions):
                issues.append("Panel position conflicts in grid layout")
                score -= 0.2
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_image_visual_quality(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate image visual quality."""
        issues = []
        recommendations = []
        score = 0.8  # Base visual score
        
        images = result.get("images", [])
        
        if not images:
            return 0.0, ["No images generated"], ["Generate visual content"]
        
        # Check image quality scores
        quality_scores = [img.get("quality_score", 0.0) for img in images]
        avg_quality = mean(quality_scores) if quality_scores else 0.0
        
        score = avg_quality  # Use average image quality as score
        
        # Check for failed generations
        failed_count = sum(1 for img in images if img.get("status") != "success")
        if failed_count > 0:
            issues.append(f"{failed_count} image generation failures")
            score -= 0.1 * (failed_count / len(images))
        
        if avg_quality < 0.6:
            recommendations.append("Improve image generation parameters")
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_image_technical_quality(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate image technical quality."""
        issues = []
        recommendations = []
        score = 0.8  # Base technical score
        
        images = result.get("images", [])
        
        # Check technical specifications
        for img in images:
            if not img.get("resolution"):
                issues.append("Missing image resolution data")
                score -= 0.1
            
            if not img.get("format"):
                issues.append("Missing image format specification")
                score -= 0.05
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_image_consistency(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate image consistency."""
        issues = []
        recommendations = []
        score = 1.0
        
        images = result.get("images", [])
        style_params = result.get("style_parameters", {})
        
        # Check style consistency
        if images and style_params:
            styles = [img.get("style", "") for img in images]
            unique_styles = set(styles)
            
            if len(unique_styles) > 2:  # Too many different styles
                issues.append("Inconsistent visual styles across images")
                score -= 0.2
                recommendations.append("Maintain consistent visual style")
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_dialogue_technical_quality(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate dialogue technical quality."""
        issues = []
        recommendations = []
        score = 1.0
        
        speech_bubbles = result.get("speech_bubbles", [])
        dialogue_layout = result.get("dialogue_layout", {})
        
        # Check bubble positioning
        for bubble in speech_bubbles:
            if not bubble.get("position"):
                issues.append("Speech bubble missing position")
                score -= 0.1
            
            if not bubble.get("text"):
                issues.append("Empty speech bubble")
                score -= 0.15
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_dialogue_completeness(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate dialogue completeness."""
        issues = []
        recommendations = []
        score = 1.0
        
        speech_bubbles = result.get("speech_bubbles", [])
        
        if not speech_bubbles:
            return 0.0, ["No dialogue content"], ["Add dialogue to scenes"]
        
        # Check character attribution
        unattributed = sum(1 for bubble in speech_bubbles if not bubble.get("character"))
        if unattributed > 0:
            issues.append(f"{unattributed} unattributed dialogue bubbles")
            score -= 0.1 * (unattributed / len(speech_bubbles))
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_dialogue_visual_quality(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate dialogue visual quality."""
        issues = []
        recommendations = []
        score = 0.8  # Base visual score
        
        speech_bubbles = result.get("speech_bubbles", [])
        
        # Check bubble styling
        for bubble in speech_bubbles:
            if not bubble.get("style"):
                score -= 0.05
                issues.append("Speech bubble missing style information")
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_integration_completeness(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate integration completeness."""
        issues = []
        recommendations = []
        score = 1.0
        
        final_pages = result.get("final_pages", [])
        export_settings = result.get("export_settings", {})
        
        if not final_pages:
            return 0.0, ["No final pages generated"], ["Complete page assembly"]
        
        if not export_settings:
            issues.append("Missing export configuration")
            score -= 0.2
        
        # Check page completeness
        for i, page in enumerate(final_pages):
            if not page.get("content"):
                issues.append(f"Page {i+1} missing content")
                score -= 0.1
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_integration_consistency(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate integration consistency."""
        issues = []
        recommendations = []
        score = 1.0
        
        final_pages = result.get("final_pages", [])
        
        # Check page format consistency
        if final_pages:
            formats = [page.get("format", "") for page in final_pages]
            unique_formats = set(formats)
            
            if len(unique_formats) > 1:
                issues.append("Inconsistent page formats")
                score -= 0.2
                recommendations.append("Standardize page formats")
        
        return max(0.0, score), issues, recommendations
    
    async def _evaluate_integration_technical_quality(
        self,
        result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[float, List[str], List[str]]:
        """Evaluate integration technical quality."""
        issues = []
        recommendations = []
        score = 0.8  # Base technical score
        
        final_pages = result.get("final_pages", [])
        quality_metrics = result.get("quality_metrics", {})
        
        # Check technical specifications
        if quality_metrics:
            overall_score = quality_metrics.get("overall_score", 0.0)
            score = overall_score  # Use reported quality score
        
        # Check for technical issues
        for page in final_pages:
            if page.get("errors"):
                issues.append(f"Page {page.get('page_number', '?')} has technical errors")
                score -= 0.1
        
        return max(0.0, score), issues, recommendations
    
    # Fallback generators
    
    async def _generate_concept_fallback(
        self,
        input_data: Dict[str, Any],
        failure_reason: str
    ) -> Dict[str, Any]:
        """Generate concept fallback."""
        return {
            "status": "fallback",
            "concept": {
                "title": "Simple Story",
                "description": "A basic adventure story with standard elements"
            },
            "genre": "adventure",
            "themes": ["friendship", "growth"],
            "world_setting": {
                "time": "modern",
                "place": "everyday_world"
            },
            "metadata": {
                "is_fallback": True,
                "failure_reason": failure_reason
            }
        }
    
    async def _generate_character_fallback(
        self,
        input_data: Dict[str, Any],
        failure_reason: str
    ) -> Dict[str, Any]:
        """Generate character fallback."""
        return {
            "status": "fallback",
            "characters": [
                {
                    "name": "Main Character",
                    "description": "The protagonist of the story",
                    "personality": ["determined", "kind"],
                    "role": "hero",
                    "visual_description": "Standard manga protagonist appearance"
                }
            ],
            "metadata": {
                "is_fallback": True,
                "failure_reason": failure_reason
            }
        }
    
    async def _generate_plot_fallback(
        self,
        input_data: Dict[str, Any],
        failure_reason: str
    ) -> Dict[str, Any]:
        """Generate plot fallback."""
        return {
            "status": "fallback",
            "story_structure": {
                "beginning": "Introduction",
                "middle": "Development",
                "end": "Resolution"
            },
            "scenes": [
                {"title": "Opening", "description": "Story begins"},
                {"title": "Development", "description": "Plot unfolds"},
                {"title": "Conclusion", "description": "Story ends"}
            ],
            "metadata": {
                "is_fallback": True,
                "failure_reason": failure_reason
            }
        }
    
    async def _generate_name_fallback(
        self,
        input_data: Dict[str, Any],
        failure_reason: str
    ) -> Dict[str, Any]:
        """Generate name fallback."""
        return {
            "status": "fallback",
            "panels": [
                {
                    "position": {"x": 0, "y": 0},
                    "size": {"width": 400, "height": 300},
                    "description": "Basic panel layout"
                }
            ],
            "layout": {
                "type": "simple",
                "columns": 1,
                "rows": 1
            },
            "metadata": {
                "is_fallback": True,
                "failure_reason": failure_reason
            }
        }
    
    async def _generate_image_fallback(
        self,
        input_data: Dict[str, Any],
        failure_reason: str
    ) -> Dict[str, Any]:
        """Generate image fallback."""
        return {
            "status": "fallback",
            "images": [
                {
                    "placeholder": True,
                    "description": "Image placeholder",
                    "quality_score": 0.5,
                    "status": "fallback"
                }
            ],
            "metadata": {
                "is_fallback": True,
                "failure_reason": failure_reason
            }
        }
    
    async def _generate_dialogue_fallback(
        self,
        input_data: Dict[str, Any],
        failure_reason: str
    ) -> Dict[str, Any]:
        """Generate dialogue fallback."""
        return {
            "status": "fallback",
            "speech_bubbles": [
                {
                    "text": "...",
                    "character": "Unknown",
                    "position": {"x": 100, "y": 100},
                    "style": "normal"
                }
            ],
            "metadata": {
                "is_fallback": True,
                "failure_reason": failure_reason
            }
        }
    
    async def _generate_integration_fallback(
        self,
        input_data: Dict[str, Any],
        failure_reason: str
    ) -> Dict[str, Any]:
        """Generate integration fallback."""
        return {
            "status": "fallback",
            "final_pages": [
                {
                    "page_number": 1,
                    "content": "Basic page content",
                    "format": "standard"
                }
            ],
            "export_settings": {
                "format": "pdf",
                "quality": "standard"
            },
            "metadata": {
                "is_fallback": True,
                "failure_reason": failure_reason
            }
        }
    
    def get_quality_stats(self) -> Dict[str, Any]:
        """Get quality system statistics."""
        return {
            **self.stats,
            "current_assessments": len(self.assessment_cache),
            "quality_thresholds": self.phase_thresholds,
            "overall_success_rate": (
                self.stats["passed_assessments"] / 
                max(self.stats["total_assessments"], 1) * 100
            ),
            "critical_phase_performance": {
                phase: self.stats["phase_success_rates"][phase]
                for phase in [4, 5]  # Critical phases
            }
        }
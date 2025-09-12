"""Phase 7: Final Integration and Quality Adjustment Agent."""

from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
import asyncio
import json
import math
from dataclasses import dataclass

from app.agents.base_agent import BaseAgent
from app.core.config import settings
from app.services.vertex_ai_service import VertexAIService


@dataclass
class QualityMetric:
    """Individual quality metric result."""
    name: str
    score: float
    weight: float
    details: Dict[str, Any]
    recommendations: List[str]


class Phase7IntegrationAgent(BaseAgent):
    """Agent for final integration and quality adjustment of manga."""
    
    def __init__(self):
        super().__init__(
            phase_number=7,
            phase_name="最終統合・品質調整",
            timeout_seconds=settings.phase_timeouts[7]
        )
        
        # Initialize structured prompts
        from app.agents.phases.phase7_integration.prompts import FinalIntegrationPrompts
        self.prompts = FinalIntegrationPrompts()
        
        # Quality assessment categories and their weights
        self.quality_categories = {
            "visual_consistency": {
                "weight": 0.25,
                "description": "Visual style and character consistency across panels"
            },
            "narrative_coherence": {
                "weight": 0.20,
                "description": "Story flow and narrative structure quality"
            },
            "technical_quality": {
                "weight": 0.15,
                "description": "Image quality and technical execution"
            },
            "readability": {
                "weight": 0.15,
                "description": "Text placement and reading experience"
            },
            "pacing_flow": {
                "weight": 0.10,
                "description": "Panel pacing and visual rhythm"
            },
            "character_development": {
                "weight": 0.10,
                "description": "Character portrayal and development"
            },
            "artistic_appeal": {
                "weight": 0.05,
                "description": "Overall artistic and aesthetic quality"
            }
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            "excellent": 0.9,
            "good": 0.8,
            "acceptable": 0.7,
            "needs_improvement": 0.6,
            "poor": 0.0
        }
        
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
    
    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: UUID,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Perform final integration and quality assessment."""
        
        if not previous_results or not all(i in previous_results for i in [1, 2, 3, 4, 5, 6]):
            raise ValueError("All previous phases (1-6) results required for final integration")
        
        self.log_info(
            "Starting final integration and quality assessment",
            session_id=str(session_id)
        )
        
        # Extract all previous phase results
        phase_results = {i: previous_results[i] for i in range(1, 7)}
        
        # Call Gemini Pro for AI analysis
        try:
            # Generate prompt for Gemini Pro analysis
            prompt = await self.generate_prompt(input_data, previous_results)
            
            ai_response = await self.vertex_ai.generate_text(
                prompt=prompt,
                phase_number=self.phase_number
            )
            
            if ai_response.get("success", False):
                # Parse JSON response from Gemini Pro  
                ai_result = self._parse_ai_response(ai_response.get("content", ""))
                
                self.log_info(f"Gemini Pro analysis successful", 
                            tokens=ai_response.get("usage", {}).get("total_tokens", 0))
                
                # Use AI result or fallback
                quality_assessment = ai_result if ai_result else await self._perform_comprehensive_quality_assessment(phase_results, session_id)
                
            else:
                # Fallback to rule-based analysis
                self.log_warning(f"Gemini Pro failed, using fallback: {ai_response.get('error', 'Unknown error')}")
                quality_assessment = await self._perform_comprehensive_quality_assessment(phase_results, session_id)
                
        except Exception as e:
            # Fallback to rule-based analysis on error
            self.log_error(f"AI analysis failed, using fallback: {str(e)}")
            quality_assessment = await self._perform_comprehensive_quality_assessment(phase_results, session_id)
        
        # Compile final manga pages
        compiled_pages = await self._compile_manga_pages(phase_results)
        
        # Optimize layouts and consistency
        layout_optimization = await self._optimize_layouts(compiled_pages, quality_assessment)
        
        # Validate complete reading experience
        reading_experience = await self._validate_reading_experience(
            compiled_pages, phase_results
        )
        
        # Generate final metadata
        manga_metadata = await self._generate_manga_metadata(phase_results)
        
        # Create output formats
        output_formats = await self._prepare_output_formats(
            compiled_pages, manga_metadata, quality_assessment
        )
        
        # Generate improvement recommendations
        improvement_plan = await self._generate_improvement_plan(
            quality_assessment, phase_results
        )
        
        # Calculate final scores
        final_scores = await self._calculate_final_scores(quality_assessment)
        
        result = {
            "quality_assessment": quality_assessment,
            "compiled_pages": compiled_pages,
            "layout_optimization": layout_optimization,
            "reading_experience": reading_experience,
            "manga_metadata": manga_metadata,
            "output_formats": output_formats,
            "improvement_plan": improvement_plan,
            "final_scores": final_scores,
            "integration_status": "completed",
            "total_pages": len(compiled_pages),
            "overall_quality_score": final_scores.get("overall_score", 0.0),
            "quality_grade": self._determine_quality_grade(final_scores.get("overall_score", 0.0)),
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
        
        return self.prompts.get_main_prompt(
            input_data=input_data,
            previous_results=previous_results
        )
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate Phase 7 output."""
        
        required_keys = [
            "quality_assessment", "compiled_pages", "manga_metadata",
            "final_scores", "overall_quality_score", "production_ready"
        ]
        
        for key in required_keys:
            if key not in output_data:
                self.log_warning(f"Missing required key: {key}")
                return False
        
        # Validate quality assessment structure
        quality_assessment = output_data.get("quality_assessment", {})
        if not isinstance(quality_assessment, dict):
            self.log_warning("Invalid quality assessment structure")
            return False
        
        # Validate final scores
        final_scores = output_data.get("final_scores", {})
        if "overall_score" not in final_scores:
            self.log_warning("Missing overall score in final scores")
            return False
        
        overall_score = final_scores.get("overall_score", 0)
        if not isinstance(overall_score, (int, float)) or not (0 <= overall_score <= 1):
            self.log_warning("Invalid overall score value")
            return False
        
        return True
    
    async def _perform_comprehensive_quality_assessment(
        self,
        phase_results: Dict[int, Dict[str, Any]],
        session_id: UUID
    ) -> Dict[str, Any]:
        """Perform comprehensive quality assessment across all phases."""
        
        self.log_info("Performing comprehensive quality assessment", session_id=str(session_id))
        
        quality_metrics = []
        
        # Assess each quality category
        for category, config in self.quality_categories.items():
            self.log_info(f"Assessing {category}", session_id=str(session_id))
            
            metric = await self._assess_quality_category(
                category, config, phase_results
            )
            quality_metrics.append(metric)
        
        # Calculate weighted overall score
        total_weighted_score = sum(metric.score * metric.weight for metric in quality_metrics)
        overall_score = total_weighted_score / sum(metric.weight for metric in quality_metrics)
        
        # Aggregate recommendations
        all_recommendations = []
        for metric in quality_metrics:
            all_recommendations.extend(metric.recommendations)
        
        # Identify critical issues
        critical_issues = [
            metric for metric in quality_metrics 
            if metric.score < self.quality_thresholds["needs_improvement"]
        ]
        
        quality_assessment = {
            "overall_score": round(overall_score, 3),
            "quality_metrics": {
                metric.name: {
                    "score": metric.score,
                    "weight": metric.weight,
                    "weighted_score": metric.score * metric.weight,
                    "details": metric.details,
                    "recommendations": metric.recommendations
                } for metric in quality_metrics
            },
            "critical_issues": [
                {
                    "category": issue.name,
                    "score": issue.score,
                    "severity": "critical" if issue.score < 0.5 else "major",
                    "recommendations": issue.recommendations
                } for issue in critical_issues
            ],
            "improvement_priority": self._prioritize_improvements(quality_metrics),
            "quality_distribution": self._analyze_quality_distribution(quality_metrics),
            "assessment_summary": self._generate_assessment_summary(
                overall_score, quality_metrics, critical_issues
            )
        }
        
        return quality_assessment
    
    async def _assess_quality_category(
        self,
        category: str,
        config: Dict[str, Any],
        phase_results: Dict[int, Dict[str, Any]]
    ) -> QualityMetric:
        """Assess a specific quality category."""
        
        if category == "visual_consistency":
            return await self._assess_visual_consistency(phase_results, config["weight"])
        elif category == "narrative_coherence":
            return await self._assess_narrative_coherence(phase_results, config["weight"])
        elif category == "technical_quality":
            return await self._assess_technical_quality(phase_results, config["weight"])
        elif category == "readability":
            return await self._assess_readability(phase_results, config["weight"])
        elif category == "pacing_flow":
            return await self._assess_pacing_flow(phase_results, config["weight"])
        elif category == "character_development":
            return await self._assess_character_development(phase_results, config["weight"])
        elif category == "artistic_appeal":
            return await self._assess_artistic_appeal(phase_results, config["weight"])
        else:
            # Default assessment
            return QualityMetric(
                name=category,
                score=0.5,
                weight=config["weight"],
                details={"note": "Category not implemented"},
                recommendations=["実装待ちのカテゴリです"]
            )
    
    async def _assess_visual_consistency(
        self, phase_results: Dict[int, Dict[str, Any]], weight: float
    ) -> QualityMetric:
        """Assess visual consistency across the manga."""
        
        details = {}
        recommendations = []
        scores = []
        
        # Character visual consistency from Phase 2 and 5
        if 2 in phase_results and 5 in phase_results:
            phase2_result = phase_results[2]
            phase5_result = phase_results[5]
            
            # Character consistency from phase 5
            consistency_report = phase5_result.get("consistency_report", {})
            character_consistency = consistency_report.get("character_consistency", {})
            char_score = character_consistency.get("overall_character_consistency", 0.5)
            
            scores.append(char_score)
            details["character_consistency_score"] = char_score
            
            if char_score < 0.7:
                recommendations.append("キャラクターの視覚的一貫性を改善")
            
            # Style consistency
            style_consistency = consistency_report.get("style_consistency", {})
            style_score = style_consistency.get("style_consistency_score", 0.5)
            
            scores.append(style_score)
            details["style_consistency_score"] = style_score
            
            if style_score < 0.7:
                recommendations.append("アートスタイルの統一性を向上")
        
        # Color and tone consistency from Phase 4
        if 4 in phase_results:
            phase4_result = phase_results[4]
            composition_guidelines = phase4_result.get("composition_guidelines", {})
            
            # Assume composition guidelines indicate visual consistency
            if composition_guidelines:
                scores.append(0.8)  # Good score for having guidelines
                details["composition_consistency"] = "guidelines_present"
            else:
                scores.append(0.5)
                recommendations.append("構図ガイドラインの統一が必要")
        
        # Calculate overall visual consistency score
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return QualityMetric(
            name="visual_consistency",
            score=round(overall_score, 3),
            weight=weight,
            details=details,
            recommendations=recommendations
        )
    
    async def _assess_narrative_coherence(
        self, phase_results: Dict[int, Dict[str, Any]], weight: float
    ) -> QualityMetric:
        """Assess narrative coherence and story flow."""
        
        details = {}
        recommendations = []
        scores = []
        
        # Story structure quality from Phase 3
        if 3 in phase_results:
            phase3_result = phase_results[3]
            
            # Story complexity score
            complexity_score = phase3_result.get("story_complexity_score", 0.5)
            scores.append(complexity_score)
            details["story_complexity"] = complexity_score
            
            if complexity_score < 0.6:
                recommendations.append("ストーリー構造の複雑さと深みを改善")
            
            # Theme integration
            theme_integration = phase3_result.get("theme_integration", {})
            if theme_integration.get("theme_balance") == "balanced":
                scores.append(0.8)
                details["theme_integration"] = "balanced"
            else:
                scores.append(0.6)
                recommendations.append("テーマの統合とバランスを調整")
            
            # Conflict structure
            conflict_structure = phase3_result.get("conflict_structure", {})
            if conflict_structure.get("primary_conflict_type"):
                scores.append(0.7)
                details["conflict_structure"] = "well_defined"
            else:
                scores.append(0.5)
                recommendations.append("対立構造の明確化が必要")
        
        # Dialogue flow from Phase 6
        if 6 in phase_results:
            phase6_result = phase_results[6]
            
            dialogue_flow = phase6_result.get("dialogue_flow", {})
            progression_score = dialogue_flow.get("narrative_progression_score", 0.5)
            
            scores.append(progression_score)
            details["dialogue_narrative_progression"] = progression_score
            
            if progression_score < 0.7:
                recommendations.append("セリフによる物語進行を改善")
        
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return QualityMetric(
            name="narrative_coherence",
            score=round(overall_score, 3),
            weight=weight,
            details=details,
            recommendations=recommendations
        )
    
    async def _assess_technical_quality(
        self, phase_results: Dict[int, Dict[str, Any]], weight: float
    ) -> QualityMetric:
        """Assess technical quality of generated content."""
        
        details = {}
        recommendations = []
        scores = []
        
        # Image generation quality from Phase 5
        if 5 in phase_results:
            phase5_result = phase_results[5]
            
            quality_analysis = phase5_result.get("quality_analysis", {})
            
            # Success rate
            success_rate = quality_analysis.get("success_rate", 0.0)
            scores.append(success_rate)
            details["image_generation_success_rate"] = success_rate
            
            if success_rate < 0.8:
                recommendations.append("画像生成成功率の改善")
            
            # Average quality score
            avg_quality = quality_analysis.get("average_quality_score", 0.0)
            scores.append(avg_quality)
            details["average_image_quality"] = avg_quality
            
            if avg_quality < 0.7:
                recommendations.append("画像品質の向上")
            
            # Generation efficiency
            parallel_efficiency = phase5_result.get("parallel_efficiency_score", 0.0)
            scores.append(parallel_efficiency)
            details["generation_efficiency"] = parallel_efficiency
        
        # Panel layout quality from Phase 4
        if 4 in phase_results:
            phase4_result = phase_results[4]
            
            layout_complexity = phase4_result.get("layout_complexity_score", 0.5)
            visual_storytelling = phase4_result.get("visual_storytelling_score", 0.5)
            
            scores.extend([layout_complexity, visual_storytelling])
            details["layout_quality"] = {
                "complexity": layout_complexity,
                "visual_storytelling": visual_storytelling
            }
            
            if layout_complexity < 0.6:
                recommendations.append("パネルレイアウトの複雑さを調整")
            
            if visual_storytelling < 0.7:
                recommendations.append("視覚的ストーリーテリングを強化")
        
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return QualityMetric(
            name="technical_quality",
            score=round(overall_score, 3),
            weight=weight,
            details=details,
            recommendations=recommendations
        )
    
    async def _assess_readability(
        self, phase_results: Dict[int, Dict[str, Any]], weight: float
    ) -> QualityMetric:
        """Assess readability and text integration."""
        
        details = {}
        recommendations = []
        scores = []
        
        # Text placement quality from Phase 6
        if 6 in phase_results:
            phase6_result = phase_results[6]
            
            # Readability score
            readability_score = phase6_result.get("readability_score", 0.5)
            scores.append(readability_score)
            details["text_readability"] = readability_score
            
            if readability_score < 0.7:
                recommendations.append("テキストの読みやすさを改善")
            
            # Text-image integration
            integration_score = phase6_result.get("text_image_integration_score", 0.5)
            scores.append(integration_score)
            details["text_image_integration"] = integration_score
            
            if integration_score < 0.7:
                recommendations.append("テキストと画像の統合を最適化")
            
            # Dialogue density
            dialogue_density = phase6_result.get("dialogue_density_score", 0.5)
            scores.append(dialogue_density)
            details["dialogue_density"] = dialogue_density
            
            if dialogue_density > 0.8:
                recommendations.append("セリフ密度を適切に調整")
            elif dialogue_density < 0.3:
                recommendations.append("セリフを追加して読み応えを向上")
        
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return QualityMetric(
            name="readability",
            score=round(overall_score, 3),
            weight=weight,
            details=details,
            recommendations=recommendations
        )
    
    async def _assess_pacing_flow(
        self, phase_results: Dict[int, Dict[str, Any]], weight: float
    ) -> QualityMetric:
        """Assess pacing and visual flow."""
        
        details = {}
        recommendations = []
        scores = []
        
        # Story pacing from Phase 3
        if 3 in phase_results:
            phase3_result = phase_results[3]
            
            pacing_analysis = phase3_result.get("pacing_analysis", {})
            pacing_match_score = pacing_analysis.get("pacing_match_score", 0.5)
            
            scores.append(pacing_match_score)
            details["story_pacing_match"] = pacing_match_score
            
            if pacing_match_score < 0.7:
                recommendations.append("ストーリーペーシングの調整")
        
        # Visual flow from Phase 4
        if 4 in phase_results:
            phase4_result = phase_results[4]
            
            visual_flow = phase4_result.get("visual_flow", {})
            reading_flow_score = visual_flow.get("reading_flow_score", 0.5)
            
            scores.append(reading_flow_score)
            details["visual_reading_flow"] = reading_flow_score
            
            if reading_flow_score < 0.7:
                recommendations.append("視覚的読み流れを改善")
            
            # Pacing visual alignment
            pacing_alignment = phase4_result.get("pacing_visual_alignment", {})
            alignment_score = pacing_alignment.get("alignment_score", 0.5)
            
            scores.append(alignment_score)
            details["pacing_visual_alignment"] = alignment_score
            
            if alignment_score < 0.7:
                recommendations.append("ペーシングと視覚的表現の整合性を向上")
        
        # Dialogue pacing from Phase 6
        if 6 in phase_results:
            phase6_result = phase_results[6]
            
            dialogue_flow = phase6_result.get("dialogue_flow", {})
            pacing_analysis = dialogue_flow.get("dialogue_pacing_analysis", {})
            dialogue_pacing_score = pacing_analysis.get("pacing_alignment_score", 0.5)
            
            scores.append(dialogue_pacing_score)
            details["dialogue_pacing"] = dialogue_pacing_score
            
            if dialogue_pacing_score < 0.7:
                recommendations.append("セリフペーシングの最適化")
        
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return QualityMetric(
            name="pacing_flow",
            score=round(overall_score, 3),
            weight=weight,
            details=details,
            recommendations=recommendations
        )
    
    async def _assess_character_development(
        self, phase_results: Dict[int, Dict[str, Any]], weight: float
    ) -> QualityMetric:
        """Assess character development and portrayal."""
        
        details = {}
        recommendations = []
        scores = []
        
        # Character design quality from Phase 2
        if 2 in phase_results:
            phase2_result = phase_results[2]
            
            # Character diversity
            diversity_score = phase2_result.get("character_diversity_score", 0.5)
            scores.append(diversity_score)
            details["character_diversity"] = diversity_score
            
            if diversity_score < 0.6:
                recommendations.append("キャラクターの多様性を向上")
            
            # Character count and importance distribution
            characters = phase2_result.get("characters", [])
            main_character_count = phase2_result.get("main_character_count", 0)
            
            if characters:
                # Check character development potential
                chars_with_development = sum(
                    1 for char in characters 
                    if char.get("arc_potential") and len(char.get("arc_potential", "")) > 10
                )
                development_ratio = chars_with_development / len(characters)
                scores.append(development_ratio)
                details["character_development_potential"] = development_ratio
                
                if development_ratio < 0.5:
                    recommendations.append("キャラクター成長要素を強化")
        
        # Character voice consistency from Phase 6
        if 6 in phase_results:
            phase6_result = phase_results[6]
            
            dialogue_flow = phase6_result.get("dialogue_flow", {})
            voice_consistency = dialogue_flow.get("character_voice_consistency", {})
            overall_consistency = voice_consistency.get("overall_voice_consistency", 0.5)
            
            scores.append(overall_consistency)
            details["character_voice_consistency"] = overall_consistency
            
            if overall_consistency < 0.8:
                recommendations.append("キャラクターの声の一貫性を改善")
        
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return QualityMetric(
            name="character_development",
            score=round(overall_score, 3),
            weight=weight,
            details=details,
            recommendations=recommendations
        )
    
    async def _assess_artistic_appeal(
        self, phase_results: Dict[int, Dict[str, Any]], weight: float
    ) -> QualityMetric:
        """Assess artistic appeal and aesthetic quality."""
        
        details = {}
        recommendations = []
        scores = []
        
        # Genre appropriateness from Phase 1
        if 1 in phase_results:
            phase1_result = phase_results[1]
            
            genre = phase1_result.get("genre", "general")
            themes = phase1_result.get("themes", [])
            
            # Genre-theme alignment
            if genre != "general" and themes:
                scores.append(0.8)  # Good alignment
                details["genre_theme_alignment"] = "appropriate"
            else:
                scores.append(0.6)  # Moderate alignment
                recommendations.append("ジャンルとテーマの整合性を向上")
        
        # Visual appeal from image quality
        if 5 in phase_results:
            phase5_result = phase_results[5]
            
            quality_analysis = phase5_result.get("quality_analysis", {})
            avg_quality = quality_analysis.get("average_quality_score", 0.5)
            
            # Convert technical quality to artistic appeal
            artistic_score = min(1.0, avg_quality * 1.1)  # Boost slightly for artistic appeal
            scores.append(artistic_score)
            details["visual_artistic_quality"] = artistic_score
            
            if artistic_score < 0.7:
                recommendations.append("視覚的魅力を向上")
        
        # Composition and design from Phase 4
        if 4 in phase_results:
            phase4_result = phase_results[4]
            
            # Use visual storytelling score as artistic indicator
            visual_storytelling = phase4_result.get("visual_storytelling_score", 0.5)
            scores.append(visual_storytelling)
            details["visual_storytelling_appeal"] = visual_storytelling
            
            if visual_storytelling < 0.7:
                recommendations.append("視覚的ストーリーテリングの魅力を強化")
        
        overall_score = sum(scores) / len(scores) if scores else 0.5
        
        return QualityMetric(
            name="artistic_appeal",
            score=round(overall_score, 3),
            weight=weight,
            details=details,
            recommendations=recommendations
        )
    
    def _prioritize_improvements(self, quality_metrics: List[QualityMetric]) -> List[Dict[str, Any]]:
        """Prioritize improvement areas based on impact and feasibility."""
        
        improvement_priorities = []
        
        for metric in quality_metrics:
            # Calculate improvement impact
            max_possible_improvement = (1.0 - metric.score) * metric.weight
            
            # Determine feasibility based on category
            feasibility_map = {
                "visual_consistency": 0.7,  # Moderate - requires regeneration
                "narrative_coherence": 0.9,  # High - mostly text changes
                "technical_quality": 0.5,   # Low - requires system improvements
                "readability": 0.8,         # High - mostly positioning
                "pacing_flow": 0.8,         # High - mostly adjustments
                "character_development": 0.6, # Moderate - design changes
                "artistic_appeal": 0.4      # Low - subjective and complex
            }
            
            feasibility = feasibility_map.get(metric.name, 0.5)
            priority_score = max_possible_improvement * feasibility
            
            if metric.score < self.quality_thresholds["good"] and metric.recommendations:
                improvement_priorities.append({
                    "category": metric.name,
                    "current_score": metric.score,
                    "weight": metric.weight,
                    "max_improvement": max_possible_improvement,
                    "feasibility": feasibility,
                    "priority_score": priority_score,
                    "recommendations": metric.recommendations
                })
        
        # Sort by priority score (highest first)
        improvement_priorities.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return improvement_priorities
    
    def _analyze_quality_distribution(self, quality_metrics: List[QualityMetric]) -> Dict[str, Any]:
        """Analyze the distribution of quality scores."""
        
        scores = [metric.score for metric in quality_metrics]
        
        distribution = {
            "mean": sum(scores) / len(scores) if scores else 0,
            "min": min(scores) if scores else 0,
            "max": max(scores) if scores else 0,
            "range": max(scores) - min(scores) if scores else 0,
            "categories_by_threshold": {}
        }
        
        # Categorize by quality thresholds
        for threshold_name, threshold_value in self.quality_thresholds.items():
            if threshold_name == "poor":  # Skip the "poor" threshold
                continue
            
            count = sum(1 for score in scores if score >= threshold_value)
            distribution["categories_by_threshold"][threshold_name] = {
                "count": count,
                "percentage": count / len(scores) if scores else 0
            }
        
        return distribution
    
    def _generate_assessment_summary(
        self,
        overall_score: float,
        quality_metrics: List[QualityMetric],
        critical_issues: List[QualityMetric]
    ) -> str:
        """Generate a human-readable assessment summary."""
        
        quality_grade = self._determine_quality_grade(overall_score)
        
        summary_parts = [
            f"総合品質スコア: {overall_score:.2f} ({quality_grade})"
        ]
        
        if critical_issues:
            summary_parts.append(f"重大な問題: {len(critical_issues)}項目")
            
        # Identify strongest areas
        strong_areas = [m.name for m in quality_metrics if m.score >= 0.8]
        if strong_areas:
            summary_parts.append(f"優秀な分野: {', '.join(strong_areas)}")
        
        # Identify areas needing improvement
        weak_areas = [m.name for m in quality_metrics if m.score < 0.7]
        if weak_areas:
            summary_parts.append(f"改善必要分野: {', '.join(weak_areas)}")
        
        return " / ".join(summary_parts)
    
    async def _compile_manga_pages(self, phase_results: Dict[int, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Compile final manga pages with all elements integrated."""
        
        compiled_pages = []
        
        # Get page layouts from Phase 4
        if 4 not in phase_results:
            return compiled_pages
        
        phase4_result = phase_results[4]
        page_layouts = phase4_result.get("page_layouts", [])
        panel_specifications = phase4_result.get("panel_specifications", [])
        
        # Get images from Phase 5
        phase5_images = {}
        if 5 in phase_results:
            phase5_result = phase_results[5]
            generated_images = phase5_result.get("generated_images", [])
            for img in generated_images:
                if img.success:
                    phase5_images[img.panel_id] = img
        
        # Get text from Phase 6
        phase6_texts = {}
        if 6 in phase_results:
            phase6_result = phase_results[6]
            text_placements = phase6_result.get("text_placements", [])
            for text in text_placements:
                panel_id = text.get("panel_id", "")
                if panel_id not in phase6_texts:
                    phase6_texts[panel_id] = []
                phase6_texts[panel_id].append(text)
        
        # Compile each page
        for page_layout in page_layouts:
            page_number = page_layout.get("page_number", 0)
            
            page_panels = []
            for panel in page_layout.get("panels", []):
                panel_id = panel.get("panel_id", "")
                
                # Find panel specification
                panel_spec = next(
                    (spec for spec in panel_specifications if spec.get("panel_id") == panel_id),
                    {}
                )
                
                # Get image for this panel
                panel_image = phase5_images.get(panel_id)
                
                # Get text for this panel
                panel_texts = phase6_texts.get(panel_id, [])
                
                compiled_panel = {
                    "panel_id": panel_id,
                    "panel_number": panel.get("panel_number", 0),
                    "layout": {
                        "size": panel.get("size", "medium"),
                        "aspect_ratio": panel.get("aspect_ratio", "4:3"),
                        "position": panel.get("position", {"x": 0, "y": 0}),
                    },
                    "image": {
                        "url": panel_image.image_url if panel_image else None,
                        "thumbnail_url": panel_image.thumbnail_url if panel_image else None,
                        "quality_score": panel_image.quality_score if panel_image else 0
                    },
                    "camera_work": {
                        "angle": panel_spec.get("camera_angle", "medium_shot"),
                        "position": panel_spec.get("camera_position", "eye_level"),
                        "composition": panel_spec.get("composition", "rule_of_thirds")
                    },
                    "text_elements": panel_texts,
                    "visual_effects": panel_spec.get("special_effects", []),
                    "mood": panel_spec.get("emotional_tone", "neutral")
                }
                
                page_panels.append(compiled_panel)
            
            compiled_page = {
                "page_number": page_number,
                "panels": page_panels,
                "layout_type": page_layout.get("layout_type", "standard"),
                "reading_time_seconds": page_layout.get("reading_time_seconds", 15),
                "scene_numbers": page_layout.get("scene_numbers", []),
                "visual_weight_distribution": page_layout.get("visual_weight_distribution", "balanced"),
                "page_completion_status": self._assess_page_completion(compiled_page)
            }
            
            compiled_pages.append(compiled_page)
        
        return compiled_pages
    
    def _assess_page_completion(self, compiled_page: Dict[str, Any]) -> Dict[str, Any]:
        """Assess completion status of a compiled page."""
        
        panels = compiled_page.get("panels", [])
        
        completion_status = {
            "total_panels": len(panels),
            "panels_with_images": 0,
            "panels_with_text": 0,
            "complete_panels": 0,
            "completion_percentage": 0.0
        }
        
        for panel in panels:
            has_image = panel.get("image", {}).get("url") is not None
            has_text = len(panel.get("text_elements", [])) > 0
            
            if has_image:
                completion_status["panels_with_images"] += 1
            
            if has_text:
                completion_status["panels_with_text"] += 1
            
            if has_image:  # Consider panel complete if it has an image
                completion_status["complete_panels"] += 1
        
        if panels:
            completion_status["completion_percentage"] = (
                completion_status["complete_panels"] / len(panels)
            )
        
        return completion_status
    
    async def _optimize_layouts(
        self,
        compiled_pages: List[Dict[str, Any]],
        quality_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize layouts based on quality assessment."""
        
        optimization_results = {
            "optimizations_applied": [],
            "layout_adjustments": [],
            "consistency_fixes": [],
            "readability_improvements": []
        }
        
        # Check for layout optimization opportunities
        critical_issues = quality_assessment.get("critical_issues", [])
        
        for issue in critical_issues:
            category = issue.get("category", "")
            recommendations = issue.get("recommendations", [])
            
            if category == "readability":
                # Apply readability optimizations
                for page in compiled_pages:
                    page_optimizations = await self._optimize_page_readability(page)
                    if page_optimizations:
                        optimization_results["readability_improvements"].extend(page_optimizations)
                        
            elif category == "visual_consistency":
                # Apply consistency fixes
                consistency_fixes = await self._optimize_visual_consistency(compiled_pages)
                optimization_results["consistency_fixes"] = consistency_fixes
                
            elif category == "pacing_flow":
                # Apply pacing optimizations
                pacing_adjustments = await self._optimize_pacing_flow(compiled_pages)
                optimization_results["layout_adjustments"].extend(pacing_adjustments)
        
        # Calculate optimization impact
        total_optimizations = sum(len(opt_list) for opt_list in optimization_results.values())
        optimization_results["total_optimizations"] = total_optimizations
        optimization_results["optimization_impact_estimate"] = min(0.1, total_optimizations * 0.02)
        
        return optimization_results
    
    async def _optimize_page_readability(self, page: Dict[str, Any]) -> List[str]:
        """Optimize readability for a single page."""
        
        optimizations = []
        panels = page.get("panels", [])
        
        for panel in panels:
            text_elements = panel.get("text_elements", [])
            
            # Check for text overlap
            if len(text_elements) > 2:
                optimizations.append(f"Page {page.get('page_number')}: テキスト要素の配置を調整")
            
            # Check for text density
            total_text_length = sum(len(elem.get("text_content", "")) for elem in text_elements)
            if total_text_length > 100:
                optimizations.append(f"Page {page.get('page_number')}: テキスト密度を軽減")
        
        return optimizations
    
    async def _optimize_visual_consistency(self, compiled_pages: List[Dict[str, Any]]) -> List[str]:
        """Optimize visual consistency across pages."""
        
        consistency_fixes = []
        
        # Analyze character consistency across pages
        all_characters = set()
        for page in compiled_pages:
            for panel in page.get("panels", []):
                for text_elem in panel.get("text_elements", []):
                    speaker = text_elem.get("speaker")
                    if speaker:
                        all_characters.add(speaker)
        
        if len(all_characters) > 3:
            consistency_fixes.append("多キャラクターシーンでの視覚的一貫性を強化")
        
        # Check for style consistency
        image_quality_scores = []
        for page in compiled_pages:
            for panel in page.get("panels", []):
                quality_score = panel.get("image", {}).get("quality_score", 0)
                if quality_score > 0:
                    image_quality_scores.append(quality_score)
        
        if image_quality_scores:
            quality_variance = self._calculate_variance(image_quality_scores)
            if quality_variance > 0.05:
                consistency_fixes.append("画像品質の一貫性を向上")
        
        return consistency_fixes
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of values."""
        if not values:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return round(variance, 4)
    
    async def _optimize_pacing_flow(self, compiled_pages: List[Dict[str, Any]]) -> List[str]:
        """Optimize pacing and flow between pages."""
        
        pacing_adjustments = []
        
        # Analyze reading time distribution
        reading_times = [page.get("reading_time_seconds", 15) for page in compiled_pages]
        
        if reading_times:
            avg_time = sum(reading_times) / len(reading_times)
            
            for i, page in enumerate(compiled_pages):
                reading_time = reading_times[i]
                page_num = page.get("page_number", i + 1)
                
                if reading_time > avg_time * 1.5:
                    pacing_adjustments.append(f"Page {page_num}: 読み時間が長すぎます（調整推奨）")
                elif reading_time < avg_time * 0.5:
                    pacing_adjustments.append(f"Page {page_num}: 読み時間が短すぎます（内容追加推奨）")
        
        return pacing_adjustments
    
    async def _validate_reading_experience(
        self,
        compiled_pages: List[Dict[str, Any]],
        phase_results: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Validate the complete reading experience."""
        
        # Calculate total reading time
        total_reading_time = sum(page.get("reading_time_seconds", 15) for page in compiled_pages)
        
        # Analyze page flow
        page_flow_analysis = await self._analyze_page_flow(compiled_pages)
        
        # Check story completeness
        story_completeness = await self._check_story_completeness(compiled_pages, phase_results)
        
        # Assess reader engagement
        engagement_score = await self._assess_reader_engagement(compiled_pages, phase_results)
        
        reading_experience = {
            "total_pages": len(compiled_pages),
            "total_reading_time_seconds": total_reading_time,
            "average_reading_time_per_page": total_reading_time / len(compiled_pages) if compiled_pages else 0,
            "page_flow_analysis": page_flow_analysis,
            "story_completeness": story_completeness,
            "reader_engagement_score": engagement_score,
            "reading_experience_quality": self._rate_reading_experience(
                total_reading_time, page_flow_analysis, story_completeness, engagement_score
            ),
            "accessibility_score": await self._assess_accessibility(compiled_pages),
            "mobile_readability": await self._assess_mobile_readability(compiled_pages)
        }
        
        return reading_experience
    
    async def _analyze_page_flow(self, compiled_pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze flow between pages."""
        
        flow_analysis = {
            "smooth_transitions": 0,
            "jarring_transitions": 0,
            "scene_continuity_breaks": 0,
            "pacing_inconsistencies": []
        }
        
        for i in range(len(compiled_pages) - 1):
            current_page = compiled_pages[i]
            next_page = compiled_pages[i + 1]
            
            # Check scene continuity
            current_scenes = set(current_page.get("scene_numbers", []))
            next_scenes = set(next_page.get("scene_numbers", []))
            
            if current_scenes & next_scenes:  # Overlapping scenes
                flow_analysis["smooth_transitions"] += 1
            elif not current_scenes or not next_scenes:  # Missing scene info
                flow_analysis["scene_continuity_breaks"] += 1
            else:
                flow_analysis["jarring_transitions"] += 1
            
            # Check pacing consistency
            current_reading_time = current_page.get("reading_time_seconds", 15)
            next_reading_time = next_page.get("reading_time_seconds", 15)
            
            time_ratio = max(current_reading_time, next_reading_time) / min(current_reading_time, next_reading_time)
            if time_ratio > 2.0:  # Significant pacing change
                flow_analysis["pacing_inconsistencies"].append({
                    "from_page": current_page.get("page_number"),
                    "to_page": next_page.get("page_number"),
                    "time_ratio": round(time_ratio, 1)
                })
        
        return flow_analysis
    
    async def _check_story_completeness(
        self,
        compiled_pages: List[Dict[str, Any]],
        phase_results: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check if the story is complete and coherent."""
        
        completeness = {
            "has_beginning": False,
            "has_middle": False,
            "has_ending": False,
            "character_arcs_present": False,
            "themes_addressed": False,
            "plot_resolution": False
        }
        
        if not compiled_pages:
            return completeness
        
        total_pages = len(compiled_pages)
        
        # Check story structure based on page distribution
        if total_pages >= 3:
            completeness["has_beginning"] = True  # First third
            completeness["has_middle"] = True    # Middle third
            completeness["has_ending"] = True    # Last third
        
        # Check character presence
        all_characters = set()
        for page in compiled_pages:
            for panel in page.get("panels", []):
                for text_elem in panel.get("text_elements", []):
                    speaker = text_elem.get("speaker")
                    if speaker:
                        all_characters.add(speaker)
        
        if len(all_characters) >= 1:
            completeness["character_arcs_present"] = True
        
        # Check theme presence from Phase 1
        if 1 in phase_results:
            themes = phase_results[1].get("themes", [])
            if themes:
                completeness["themes_addressed"] = True
        
        # Assume plot resolution if story has ending
        completeness["plot_resolution"] = completeness["has_ending"]
        
        # Calculate overall completeness score
        completed_elements = sum(1 for value in completeness.values() if value)
        completeness["overall_completeness_score"] = completed_elements / len(completeness)
        
        return completeness
    
    async def _assess_reader_engagement(
        self,
        compiled_pages: List[Dict[str, Any]],
        phase_results: Dict[int, Dict[str, Any]]
    ) -> float:
        """Assess potential reader engagement."""
        
        engagement_factors = []
        
        # Visual variety (different panel types and compositions)
        panel_types = set()
        for page in compiled_pages:
            for panel in page.get("panels", []):
                camera_angle = panel.get("camera_work", {}).get("angle", "medium_shot")
                panel_types.add(camera_angle)
        
        visual_variety = min(1.0, len(panel_types) / 5)  # Normalize by 5 different angles
        engagement_factors.append(visual_variety)
        
        # Dialogue engagement (character interactions)
        dialogue_interactions = 0
        total_dialogue_elements = 0
        
        for page in compiled_pages:
            for panel in page.get("panels", []):
                text_elements = panel.get("text_elements", [])
                panel_speakers = set(elem.get("speaker") for elem in text_elements if elem.get("speaker"))
                
                total_dialogue_elements += len(text_elements)
                
                if len(panel_speakers) > 1:
                    dialogue_interactions += 1
        
        interaction_rate = dialogue_interactions / len(compiled_pages) if compiled_pages else 0
        engagement_factors.append(min(1.0, interaction_rate))
        
        # Pacing variety
        reading_times = [page.get("reading_time_seconds", 15) for page in compiled_pages]
        if reading_times:
            time_variance = self._calculate_variance(reading_times)
            pacing_variety = min(1.0, time_variance * 10)  # Normalize variance
            engagement_factors.append(pacing_variety)
        
        # Genre engagement from Phase 1
        if 1 in phase_results:
            genre = phase_results[1].get("genre", "general")
            genre_engagement = 0.8 if genre != "general" else 0.5
            engagement_factors.append(genre_engagement)
        
        # Calculate overall engagement score
        engagement_score = sum(engagement_factors) / len(engagement_factors) if engagement_factors else 0.5
        
        return round(engagement_score, 3)
    
    def _rate_reading_experience(
        self,
        total_reading_time: int,
        page_flow_analysis: Dict[str, Any],
        story_completeness: Dict[str, Any],
        engagement_score: float
    ) -> str:
        """Rate the overall reading experience quality."""
        
        # Calculate reading experience score
        factors = []
        
        # Appropriate reading time (not too short or too long)
        optimal_time_range = (120, 600)  # 2-10 minutes
        if optimal_time_range[0] <= total_reading_time <= optimal_time_range[1]:
            factors.append(1.0)
        elif total_reading_time < optimal_time_range[0]:
            factors.append(0.6)  # Too short
        else:
            factors.append(0.7)  # Too long but acceptable
        
        # Page flow quality
        total_transitions = (
            page_flow_analysis.get("smooth_transitions", 0) +
            page_flow_analysis.get("jarring_transitions", 0)
        )
        
        if total_transitions > 0:
            smooth_ratio = page_flow_analysis.get("smooth_transitions", 0) / total_transitions
            factors.append(smooth_ratio)
        else:
            factors.append(0.5)
        
        # Story completeness
        factors.append(story_completeness.get("overall_completeness_score", 0.5))
        
        # Engagement score
        factors.append(engagement_score)
        
        overall_score = sum(factors) / len(factors)
        
        if overall_score >= 0.9:
            return "excellent"
        elif overall_score >= 0.8:
            return "good"
        elif overall_score >= 0.7:
            return "acceptable"
        elif overall_score >= 0.6:
            return "needs_improvement"
        else:
            return "poor"
    
    async def _assess_accessibility(self, compiled_pages: List[Dict[str, Any]]) -> float:
        """Assess accessibility of the manga."""
        
        accessibility_factors = []
        
        # Text readability
        total_text_elements = 0
        readable_text_elements = 0
        
        for page in compiled_pages:
            for panel in page.get("panels", []):
                text_elements = panel.get("text_elements", [])
                total_text_elements += len(text_elements)
                
                for text_elem in text_elements:
                    text_content = text_elem.get("text_content", "")
                    # Simple readability check based on length
                    if 1 <= len(text_content) <= 50:  # Reasonable length
                        readable_text_elements += 1
        
        if total_text_elements > 0:
            text_readability = readable_text_elements / total_text_elements
            accessibility_factors.append(text_readability)
        
        # Visual clarity (assume good if images are present)
        pages_with_images = sum(
            1 for page in compiled_pages
            if any(panel.get("image", {}).get("url") for panel in page.get("panels", []))
        )
        
        visual_clarity = pages_with_images / len(compiled_pages) if compiled_pages else 0
        accessibility_factors.append(visual_clarity)
        
        # Layout consistency
        layout_types = set(page.get("layout_type", "standard") for page in compiled_pages)
        layout_consistency = 1.0 if len(layout_types) <= 3 else 0.7  # Not too many different layouts
        accessibility_factors.append(layout_consistency)
        
        return round(sum(accessibility_factors) / len(accessibility_factors), 3) if accessibility_factors else 0.5
    
    async def _assess_mobile_readability(self, compiled_pages: List[Dict[str, Any]]) -> float:
        """Assess readability on mobile devices."""
        
        mobile_factors = []
        
        # Panel size distribution
        small_panels = 0
        total_panels = 0
        
        for page in compiled_pages:
            for panel in page.get("panels", []):
                total_panels += 1
                panel_size = panel.get("layout", {}).get("size", "medium")
                if panel_size in ["small"]:
                    small_panels += 1
        
        if total_panels > 0:
            # Fewer small panels is better for mobile
            mobile_panel_ratio = 1.0 - (small_panels / total_panels)
            mobile_factors.append(mobile_panel_ratio)
        
        # Text size consideration (assume larger text elements are better)
        large_text_elements = 0
        total_text_elements = 0
        
        for page in compiled_pages:
            for panel in page.get("panels", []):
                text_elements = panel.get("text_elements", [])
                total_text_elements += len(text_elements)
                
                for text_elem in text_elements:
                    importance = text_elem.get("importance", "medium")
                    if importance in ["high", "medium"]:
                        large_text_elements += 1
        
        if total_text_elements > 0:
            mobile_text_ratio = large_text_elements / total_text_elements
            mobile_factors.append(mobile_text_ratio)
        
        return round(sum(mobile_factors) / len(mobile_factors), 3) if mobile_factors else 0.7
    
    async def _generate_manga_metadata(self, phase_results: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive metadata for the manga."""
        
        metadata = {
            "title": "AI生成漫画",
            "creation_date": "2024-01-01",  # Would use actual date
            "format_version": "1.0",
            "total_pages": 0,
            "estimated_reading_time_minutes": 0,
            "content_rating": "general"
        }
        
        # Extract information from each phase
        if 1 in phase_results:
            phase1_result = phase_results[1]
            metadata.update({
                "genre": phase1_result.get("genre", "general"),
                "themes": phase1_result.get("themes", []),
                "world_setting": phase1_result.get("world_setting", {}),
                "target_audience": phase1_result.get("target_audience", "general"),
                "estimated_pages": phase1_result.get("estimated_pages", 0)
            })
        
        if 2 in phase_results:
            phase2_result = phase_results[2]
            metadata.update({
                "characters": [
                    {
                        "name": char.get("name", ""),
                        "role": char.get("role", ""),
                        "importance": char.get("importance", 0)
                    } for char in phase2_result.get("characters", [])
                ],
                "character_count": phase2_result.get("total_character_count", 0)
            })
        
        if 3 in phase_results:
            phase3_result = phase_results[3]
            metadata.update({
                "story_structure": phase3_result.get("story_structure", {}),
                "total_scenes": phase3_result.get("total_scenes", 0),
                "story_complexity_score": phase3_result.get("story_complexity_score", 0.5)
            })
        
        if 4 in phase_results:
            phase4_result = phase_results[4]
            metadata.update({
                "total_panels": phase4_result.get("total_panels", 0),
                "layout_complexity_score": phase4_result.get("layout_complexity_score", 0.5)
            })
        
        if 5 in phase_results:
            phase5_result = phase_results[5]
            metadata.update({
                "total_images": phase5_result.get("total_images_generated", 0),
                "successful_images": phase5_result.get("successful_generations", 0),
                "average_image_quality": phase5_result.get("quality_analysis", {}).get("average_quality_score", 0)
            })
        
        if 6 in phase_results:
            phase6_result = phase_results[6]
            metadata.update({
                "total_dialogue_elements": phase6_result.get("total_dialogue_elements", 0),
                "characters_speaking": phase6_result.get("characters_speaking", 0)
            })
        
        # Calculate total reading time
        if "estimated_pages" in metadata:
            # Rough estimate: 30-60 seconds per page
            metadata["estimated_reading_time_minutes"] = round(
                (metadata["estimated_pages"] * 45) / 60, 1
            )
        
        # Add technical metadata
        metadata.update({
            "creation_method": "ai_generated",
            "ai_models_used": ["gemini-pro", "imagen-4"],
            "processing_phases": list(phase_results.keys()),
            "language": "japanese",
            "text_direction": "right_to_left"
        })
        
        return metadata
    
    async def _prepare_output_formats(
        self,
        compiled_pages: List[Dict[str, Any]],
        manga_metadata: Dict[str, Any],
        quality_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare different output formats for the manga."""
        
        output_formats = {
            "web_format": {
                "format": "web_optimized",
                "pages": await self._prepare_web_format(compiled_pages),
                "viewer_compatible": True,
                "mobile_optimized": True
            },
            "print_format": {
                "format": "print_ready", 
                "pages": await self._prepare_print_format(compiled_pages),
                "resolution": "300dpi",
                "color_space": "CMYK"
            },
            "digital_format": {
                "format": "digital_distribution",
                "pages": await self._prepare_digital_format(compiled_pages),
                "drm_ready": False,
                "platform_compatible": ["web", "mobile", "tablet"]
            },
            "preview_format": {
                "format": "preview",
                "pages": await self._prepare_preview_format(compiled_pages[:3]),  # First 3 pages
                "watermarked": True,
                "resolution": "low"
            }
        }
        
        # Add format-specific metadata
        for format_name, format_data in output_formats.items():
            format_data["metadata"] = manga_metadata.copy()
            format_data["quality_info"] = {
                "overall_score": quality_assessment.get("overall_score", 0),
                "production_ready": quality_assessment.get("overall_score", 0) >= 0.7
            }
        
        return output_formats
    
    async def _prepare_web_format(self, compiled_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare web-optimized format."""
        
        web_pages = []
        
        for page in compiled_pages:
            web_page = {
                "page_number": page.get("page_number", 0),
                "layout": "responsive",
                "panels": [],
                "loading_priority": "high" if page.get("page_number", 0) <= 3 else "normal"
            }
            
            for panel in page.get("panels", []):
                web_panel = {
                    "panel_id": panel.get("panel_id", ""),
                    "image_url": panel.get("image", {}).get("url", ""),
                    "thumbnail_url": panel.get("image", {}).get("thumbnail_url", ""),
                    "alt_text": self._generate_alt_text(panel),
                    "text_overlay": panel.get("text_elements", []),
                    "responsive_sizing": True
                }
                web_page["panels"].append(web_panel)
            
            web_pages.append(web_page)
        
        return web_pages
    
    async def _prepare_print_format(self, compiled_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare print-ready format."""
        
        print_pages = []
        
        for page in compiled_pages:
            print_page = {
                "page_number": page.get("page_number", 0),
                "dimensions": {"width": "210mm", "height": "297mm"},  # A4
                "margins": {"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"},
                "bleed": "3mm",
                "color_profile": "Japan Color 2001 Coated",
                "panels": []
            }
            
            for panel in page.get("panels", []):
                print_panel = {
                    "panel_id": panel.get("panel_id", ""),
                    "high_res_image_url": panel.get("image", {}).get("url", ""),  # Would be high-res version
                    "vector_text": panel.get("text_elements", []),
                    "print_quality": "300dpi"
                }
                print_page["panels"].append(print_panel)
            
            print_pages.append(print_page)
        
        return print_pages
    
    async def _prepare_digital_format(self, compiled_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare digital distribution format."""
        
        digital_pages = []
        
        for page in compiled_pages:
            digital_page = {
                "page_number": page.get("page_number", 0),
                "format": "digital_comic",
                "guided_view_compatible": True,
                "zoom_regions": await self._define_zoom_regions(page),
                "panels": []
            }
            
            for panel in page.get("panels", []):
                digital_panel = {
                    "panel_id": panel.get("panel_id", ""),
                    "image_url": panel.get("image", {}).get("url", ""),
                    "interactive_elements": panel.get("text_elements", []),
                    "reading_order": panel.get("panel_number", 0)
                }
                digital_page["panels"].append(digital_panel)
            
            digital_pages.append(digital_page)
        
        return digital_pages
    
    async def _prepare_preview_format(self, compiled_pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare preview format."""
        
        preview_pages = []
        
        for page in compiled_pages:
            preview_page = {
                "page_number": page.get("page_number", 0),
                "watermark": "PREVIEW",
                "quality": "reduced",
                "panels": []
            }
            
            for panel in page.get("panels", []):
                preview_panel = {
                    "panel_id": panel.get("panel_id", ""),
                    "thumbnail_url": panel.get("image", {}).get("thumbnail_url", ""),
                    "preview_quality": True
                }
                preview_page["panels"].append(preview_panel)
            
            preview_pages.append(preview_page)
        
        return preview_pages
    
    def _generate_alt_text(self, panel: Dict[str, Any]) -> str:
        """Generate alt text for accessibility."""
        
        camera_work = panel.get("camera_work", {})
        camera_angle = camera_work.get("angle", "medium_shot")
        mood = panel.get("mood", "neutral")
        
        # Generate basic alt text
        alt_text = f"{camera_angle}の構図"
        
        if mood != "neutral":
            alt_text += f"、{mood}な雰囲気"
        
        # Add character information if available
        text_elements = panel.get("text_elements", [])
        speakers = set(elem.get("speaker") for elem in text_elements if elem.get("speaker"))
        
        if speakers:
            alt_text += f"、{', '.join(speakers)}が登場"
        
        return alt_text
    
    async def _define_zoom_regions(self, page: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Define zoom regions for guided view."""
        
        zoom_regions = []
        
        for i, panel in enumerate(page.get("panels", [])):
            zoom_region = {
                "region_id": f"panel_{i}",
                "panel_id": panel.get("panel_id", ""),
                "zoom_level": self._determine_zoom_level(panel),
                "focus_point": self._determine_focus_point(panel),
                "reading_order": panel.get("panel_number", 0)
            }
            zoom_regions.append(zoom_region)
        
        return zoom_regions
    
    def _determine_zoom_level(self, panel: Dict[str, Any]) -> str:
        """Determine appropriate zoom level for panel."""
        
        camera_angle = panel.get("camera_work", {}).get("angle", "medium_shot")
        
        zoom_mapping = {
            "extreme_close_up": "high",
            "close_up": "medium",
            "medium_shot": "medium",
            "full_shot": "low",
            "wide_shot": "low"
        }
        
        return zoom_mapping.get(camera_angle, "medium")
    
    def _determine_focus_point(self, panel: Dict[str, Any]) -> Dict[str, float]:
        """Determine focus point for guided view."""
        
        # Default to center
        focus_point = {"x": 0.5, "y": 0.5}
        
        camera_angle = panel.get("camera_work", {}).get("angle", "medium_shot")
        
        # Adjust focus based on camera angle
        if camera_angle in ["extreme_close_up", "close_up"]:
            # Focus slightly higher for face/character focus
            focus_point["y"] = 0.4
        elif camera_angle == "wide_shot":
            # Center focus for establishing shots
            focus_point = {"x": 0.5, "y": 0.5}
        
        return focus_point
    
    async def _generate_improvement_plan(
        self,
        quality_assessment: Dict[str, Any],
        phase_results: Dict[int, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate comprehensive improvement plan."""
        
        improvement_plan = {
            "priority_improvements": [],
            "phase_specific_recommendations": {},
            "estimated_impact": {},
            "implementation_difficulty": {},
            "quick_wins": [],
            "long_term_improvements": []
        }
        
        # Get prioritized improvements from quality assessment
        improvement_priorities = quality_assessment.get("improvement_priority", [])
        
        for improvement in improvement_priorities[:5]:  # Top 5 priorities
            category = improvement.get("category", "")
            recommendations = improvement.get("recommendations", [])
            priority_score = improvement.get("priority_score", 0)
            
            improvement_item = {
                "category": category,
                "current_score": improvement.get("current_score", 0),
                "recommendations": recommendations,
                "estimated_improvement": improvement.get("max_improvement", 0),
                "implementation_time": self._estimate_implementation_time(category),
                "resource_requirements": self._estimate_resource_requirements(category)
            }
            
            improvement_plan["priority_improvements"].append(improvement_item)
            
            # Categorize as quick wins or long-term
            if improvement.get("feasibility", 0) > 0.7 and priority_score > 0.05:
                improvement_plan["quick_wins"].append({
                    "category": category,
                    "action": recommendations[0] if recommendations else "改善が必要",
                    "estimated_days": self._estimate_implementation_time(category)
                })
            elif priority_score > 0.03:
                improvement_plan["long_term_improvements"].append({
                    "category": category,
                    "action": recommendations[0] if recommendations else "改善が必要",
                    "estimated_weeks": self._estimate_implementation_time(category) / 7
                })
        
        # Generate phase-specific recommendations
        for phase_num, phase_result in phase_results.items():
            phase_recommendations = await self._generate_phase_recommendations(
                phase_num, phase_result, quality_assessment
            )
            if phase_recommendations:
                improvement_plan["phase_specific_recommendations"][f"phase_{phase_num}"] = phase_recommendations
        
        return improvement_plan
    
    def _estimate_implementation_time(self, category: str) -> int:
        """Estimate implementation time in days."""
        
        time_estimates = {
            "visual_consistency": 3,      # Moderate - requires some regeneration
            "narrative_coherence": 1,     # Quick - mostly text adjustments
            "technical_quality": 7,       # Long - system improvements
            "readability": 1,             # Quick - positioning adjustments
            "pacing_flow": 2,             # Short - flow adjustments
            "character_development": 5,   # Moderate - design changes
            "artistic_appeal": 10         # Long - subjective improvements
        }
        
        return time_estimates.get(category, 3)
    
    def _estimate_resource_requirements(self, category: str) -> str:
        """Estimate resource requirements."""
        
        resource_map = {
            "visual_consistency": "medium",
            "narrative_coherence": "low", 
            "technical_quality": "high",
            "readability": "low",
            "pacing_flow": "low",
            "character_development": "medium",
            "artistic_appeal": "high"
        }
        
        return resource_map.get(category, "medium")
    
    async def _generate_phase_recommendations(
        self,
        phase_num: int,
        phase_result: Dict[str, Any],
        quality_assessment: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for specific phase."""
        
        recommendations = []
        
        if phase_num == 1:  # Concept analysis
            if not phase_result.get("themes") or len(phase_result.get("themes", [])) < 2:
                recommendations.append("テーマの深化と多様性の向上")
        
        elif phase_num == 2:  # Character design
            diversity_score = phase_result.get("character_diversity_score", 0.5)
            if diversity_score < 0.7:
                recommendations.append("キャラクターの多様性と個性の強化")
        
        elif phase_num == 3:  # Story structure
            complexity_score = phase_result.get("story_complexity_score", 0.5)
            if complexity_score < 0.6:
                recommendations.append("ストーリー構造の複雑性と深みの向上")
        
        elif phase_num == 4:  # Panel layout
            visual_storytelling = phase_result.get("visual_storytelling_score", 0.5)
            if visual_storytelling < 0.7:
                recommendations.append("視覚的ストーリーテリングの強化")
        
        elif phase_num == 5:  # Image generation
            success_rate = phase_result.get("quality_analysis", {}).get("success_rate", 0)
            if success_rate < 0.8:
                recommendations.append("画像生成成功率の改善")
        
        elif phase_num == 6:  # Dialogue
            readability_score = phase_result.get("readability_score", 0.5)
            if readability_score < 0.7:
                recommendations.append("テキスト配置と読みやすさの改善")
        
        return recommendations
    
    async def _calculate_final_scores(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final scores for the manga."""
        
        overall_score = quality_assessment.get("overall_score", 0.5)
        quality_metrics = quality_assessment.get("quality_metrics", {})
        
        final_scores = {
            "overall_score": overall_score,
            "category_scores": {},
            "weighted_scores": {},
            "grade": self._determine_quality_grade(overall_score),
            "percentile": self._calculate_percentile(overall_score),
            "strengths": [],
            "weaknesses": [],
            "benchmark_comparison": self._compare_to_benchmark(overall_score)
        }
        
        # Extract category scores
        for category, metric_data in quality_metrics.items():
            score = metric_data.get("score", 0)
            weight = metric_data.get("weight", 0)
            
            final_scores["category_scores"][category] = score
            final_scores["weighted_scores"][category] = score * weight
            
            # Identify strengths and weaknesses
            if score >= 0.8:
                final_scores["strengths"].append(category)
            elif score < 0.6:
                final_scores["weaknesses"].append(category)
        
        return final_scores
    
    def _determine_quality_grade(self, overall_score: float) -> str:
        """Determine quality grade based on overall score."""
        
        if overall_score >= 0.9:
            return "A+"
        elif overall_score >= 0.85:
            return "A"
        elif overall_score >= 0.8:
            return "B+"
        elif overall_score >= 0.75:
            return "B"
        elif overall_score >= 0.7:
            return "C+"
        elif overall_score >= 0.65:
            return "C"
        elif overall_score >= 0.6:
            return "D+"
        else:
            return "D"
    
    def _calculate_percentile(self, overall_score: float) -> int:
        """Calculate percentile ranking (simulated)."""
        
        # Simulate percentile based on score distribution
        # In real implementation, this would be based on actual data
        if overall_score >= 0.9:
            return 95
        elif overall_score >= 0.8:
            return 80
        elif overall_score >= 0.7:
            return 60
        elif overall_score >= 0.6:
            return 40
        else:
            return 20
    
    def _compare_to_benchmark(self, overall_score: float) -> Dict[str, Any]:
        """Compare to benchmark standards."""
        
        benchmarks = {
            "professional_manga": 0.85,
            "amateur_high_quality": 0.75,
            "acceptable_quality": 0.65,
            "minimum_readable": 0.5
        }
        
        comparison = {}
        
        for benchmark_name, benchmark_score in benchmarks.items():
            if overall_score >= benchmark_score:
                comparison[benchmark_name] = "達成"
            else:
                gap = benchmark_score - overall_score
                comparison[benchmark_name] = f"未達成 (差分: {gap:.2f})"
        
        return comparison
    
    def _generate_processing_summary(
        self,
        phase_results: Dict[int, Dict[str, Any]],
        final_scores: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary of processing results."""
        
        summary = {
            "phases_completed": len(phase_results),
            "total_elements_generated": 0,
            "processing_highlights": [],
            "technical_stats": {},
            "quality_achievements": []
        }
        
        # Count elements generated
        if 2 in phase_results:
            char_count = len(phase_results[2].get("characters", []))
            summary["total_elements_generated"] += char_count
            summary["processing_highlights"].append(f"{char_count}体のキャラクター生成")
        
        if 4 in phase_results:
            panel_count = phase_results[4].get("total_panels", 0)
            summary["total_elements_generated"] += panel_count
            summary["processing_highlights"].append(f"{panel_count}個のパネル設計")
        
        if 5 in phase_results:
            image_count = phase_results[5].get("successful_generations", 0)
            summary["total_elements_generated"] += image_count
            summary["processing_highlights"].append(f"{image_count}枚の画像生成成功")
        
        if 6 in phase_results:
            text_count = phase_results[6].get("total_dialogue_elements", 0)
            summary["total_elements_generated"] += text_count
            summary["processing_highlights"].append(f"{text_count}個のテキスト要素配置")
        
        # Technical stats
        if 5 in phase_results:
            quality_analysis = phase_results[5].get("quality_analysis", {})
            summary["technical_stats"]["image_success_rate"] = quality_analysis.get("success_rate", 0)
            summary["technical_stats"]["average_image_quality"] = quality_analysis.get("average_quality_score", 0)
        
        # Quality achievements
        overall_score = final_scores.get("overall_score", 0)
        grade = final_scores.get("grade", "D")
        
        summary["quality_achievements"].append(f"総合品質スコア: {overall_score:.2f} ({grade})")
        
        strengths = final_scores.get("strengths", [])
        if strengths:
            summary["quality_achievements"].append(f"優秀分野: {', '.join(strengths)}")
        
        return summary

    def _parse_ai_response(self, ai_content: str) -> Dict[str, Any]:
        """Parse Gemini Pro JSON response into structured data."""
        try:
            # Find JSON in response (handle cases where AI adds explanation text)
            json_start = ai_content.find('{')
            json_end = ai_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_content[json_start:json_end]
                parsed_data = json.loads(json_str)
                return parsed_data
            else:
                raise ValueError("No JSON found in AI response")
                
        except (json.JSONDecodeError, ValueError) as e:
            self.log_warning(f"Failed to parse AI response as JSON: {str(e)}")
            return {}
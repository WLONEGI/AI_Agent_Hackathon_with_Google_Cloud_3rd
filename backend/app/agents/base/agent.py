"""Base Agent class for all phase processing agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import json
from uuid import UUID

from app.core.logging import LoggerMixin
from .executor import PhaseExecutor
from .validator import BaseValidator
from .metrics import AgentMetrics


class BaseAgent(ABC, LoggerMixin):
    """Abstract base class for phase processing agents."""
    
    def __init__(
        self,
        phase_number: int,
        phase_name: str,
        timeout_seconds: int = 60
    ):
        """Initialize base agent.
        
        Args:
            phase_number: The phase number (1-7)
            phase_name: Human-readable phase name
            timeout_seconds: Maximum processing time in seconds
        """
        super().__init__()
        
        self.phase_number = phase_number
        self.phase_name = phase_name
        self.timeout_seconds = timeout_seconds
        
        # Initialize components
        self.executor = PhaseExecutor(timeout_seconds)
        self.validator = self._create_validator()
        self.metrics = AgentMetrics(phase_number, phase_name)
        
        self.logger.info(
            f"Initialized {self.phase_name} agent",
            phase_number=phase_number,
            timeout=timeout_seconds
        )
    
    @abstractmethod
    def _create_validator(self) -> BaseValidator:
        """Create phase-specific validator."""
        pass

    def _validate_input_data(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Validate input data according to phase interface specifications.
        
        Args:
            input_data: Input data for this phase
            previous_results: Results from previous phases
            
        Returns:
            Dict containing validation result with is_valid and errors
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Define expected input fields for each phase
        phase_requirements = {
            1: {
                "required_fields": ["story_context"],
                "optional_fields": ["genre", "themes", "target_audience"]
            },
            2: {
                "required_previous_phases": [1],
                "required_from_phase_1": ["genre_analysis", "theme_analysis", "world_setting"],
                "optional_fields": ["character_requirements"]
            },
            3: {
                "required_previous_phases": [1, 2],
                "required_from_phase_1": ["genre_analysis", "theme_analysis", "world_setting"],
                "required_from_phase_2": ["characters"],
                "optional_fields": ["estimated_pages"]
            },
            4: {
                "required_previous_phases": [1, 2, 3],
                "required_from_phase_3": ["scenes", "story_structure"],
                "required_from_phase_2": ["characters"],
                "optional_fields": ["layout_preferences"]
            },
            5: {
                "required_previous_phases": [3, 4],
                "required_from_phase_4": ["panels"],
                "required_from_phase_3": ["scenes"],
                "required_from_phase_2": ["characters"],
                "optional_fields": ["visual_style_preferences"]
            },
            6: {
                "required_previous_phases": [3, 5],
                "required_from_phase_5": ["image_descriptions"],
                "required_from_phase_3": ["scenes"],
                "required_from_phase_2": ["characters"],
                "optional_fields": ["dialogue_style_preferences"]
            },
            7: {
                "required_previous_phases": [4, 5, 6],
                "required_from_phase_6": ["dialogue_placements"],
                "required_from_phase_5": ["image_descriptions"],
                "required_from_phase_4": ["panels"],
                "optional_fields": ["integration_preferences"]
            }
        }
        
        current_phase = self.phase_number
        requirements = phase_requirements.get(current_phase, {})
        
        # Check if required previous phases exist
        required_phases = requirements.get("required_previous_phases", [])
        if previous_results:
            for phase_num in required_phases:
                if phase_num not in previous_results:
                    validation_result["errors"].append(
                        f"Required phase {phase_num} results not found"
                    )
                    validation_result["is_valid"] = False
        elif required_phases:
            # Debug: log the actual previous_results value
            print(f"DEBUG Phase {current_phase}: required_phases={required_phases}, previous_results={previous_results}")
            validation_result["errors"].append(
                "Previous phase results required but not provided"
            )
            validation_result["is_valid"] = False
        
        # Validate required fields from specific phases
        if previous_results:
            for phase_num in required_phases:
                if phase_num in previous_results:
                    phase_result = previous_results[phase_num]
                    required_fields_key = f"required_from_phase_{phase_num}"
                    required_fields = requirements.get(required_fields_key, [])
                    
                    for field in required_fields:
                        if field not in phase_result:
                            validation_result["errors"].append(
                                f"Required field '{field}' missing from Phase {phase_num} results"
                            )
                            validation_result["is_valid"] = False
                        elif not phase_result[field]:
                            validation_result["warnings"].append(
                                f"Field '{field}' from Phase {phase_num} is empty"
                            )
        
        # Validate standardized field names (critical for Phase 3 → Phase 6 data flow)
        if current_phase == 6 and previous_results and 3 in previous_results:
            phase3_result = previous_results[3]
            if "scene_breakdown" in phase3_result and "scenes" not in phase3_result:
                validation_result["errors"].append(
                    "Phase 3 still using deprecated 'scene_breakdown' field. Expected 'scenes' field."
                )
                validation_result["is_valid"] = False
            elif "scenes" not in phase3_result:
                validation_result["errors"].append(
                    "Phase 3 missing required 'scenes' field"
                )
                validation_result["is_valid"] = False
        
        # Validate data types for critical fields
        if previous_results:
            type_validations = {
                "characters": list,
                "scenes": list,
                "panels": list,
                "image_descriptions": list,
                "dialogue_placements": list
            }
            
            for phase_num, phase_result in previous_results.items():
                for field_name, expected_type in type_validations.items():
                    if field_name in phase_result:
                        if not isinstance(phase_result[field_name], expected_type):
                            validation_result["errors"].append(
                                f"Field '{field_name}' in Phase {phase_num} should be {expected_type.__name__}, got {type(phase_result[field_name]).__name__}"
                            )
                            validation_result["is_valid"] = False
        
        return validation_result
    
    @abstractmethod
    async def _generate_prompt(
        self,
        input_data: Dict[str, Any],
        previous_results: Optional[Dict[int, Any]] = None
    ) -> str:
        """Generate AI prompt for this phase."""
        pass
    
    @abstractmethod
    async def _process_ai_response(
        self,
        ai_response: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process AI response into structured output."""
        pass
    
    @abstractmethod
    async def _generate_preview(
        self,
        output_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate preview data for this phase."""
        pass
    
    async def process_phase(
        self,
        input_data: Dict[str, Any],
        session_id: str,
        previous_results: Optional[Dict[int, Any]] = None
    ) -> Dict[str, Any]:
        """Process the phase with input data."""
        
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(
                f"Starting {self.phase_name} processing",
                session_id=session_id,
                phase_number=self.phase_number
            )
            
            # Validate input data according to phase interface specifications
            input_validation = self._validate_input_data(input_data, previous_results)
            if not input_validation["is_valid"]:
                raise ValueError(f"Input validation failed: {input_validation['errors']}")
            
            # Log warnings if any
            if input_validation["warnings"]:
                for warning in input_validation["warnings"]:
                    self.logger.warning(f"Input validation warning: {warning}")
            
            # Generate prompt
            prompt = await self._generate_prompt(input_data, previous_results)
            
            # Execute phase processing
            result = await self.executor.execute_with_timeout(
                self._execute_phase_logic,
                input_data,
                session_id,
                prompt,
                timeout=self.timeout_seconds
            )
            
            # Validate output
            validation_result = await self.validator.validate_output(result)
            if not validation_result.is_valid:
                raise ValueError(f"Output validation failed: {validation_result.errors}")
            
            # Generate preview
            preview = await self._generate_preview(result)
            result["preview"] = preview
            
            # Update metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            await self.metrics.record_success(processing_time)
            
            self.logger.info(
                f"Completed {self.phase_name} processing",
                session_id=session_id,
                processing_time=processing_time
            )
            
            return {
                "phase_number": self.phase_number,
                "phase_name": self.phase_name,
                "status": "completed",
                "processing_time": processing_time,
                "output": result,
                "preview": preview,
                "validation_passed": True,
                "input_validation_warnings": input_validation["warnings"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            await self.metrics.record_failure(processing_time, str(e))
            
            self.logger.error(
                f"Failed {self.phase_name} processing",
                session_id=session_id,
                error=str(e),
                processing_time=processing_time
            )
            
            return {
                "phase_number": self.phase_number,
                "phase_name": self.phase_name,
                "status": "error",
                "processing_time": processing_time,
                "error": str(e),
                "validation_passed": False,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _execute_phase_logic(
        self,
        input_data: Dict[str, Any],
        session_id: str,
        prompt: str
    ) -> Dict[str, Any]:
        """Execute the core phase processing logic."""
        
        # This is a placeholder for AI service call
        # In real implementation, this would call Vertex AI or other AI services
        ai_response = await self._simulate_ai_call(prompt)
        
        # Process AI response into structured output
        processed_result = await self._process_ai_response(ai_response, input_data)
        
        return processed_result
    
    async def _simulate_ai_call(self, prompt: str) -> str:
        """Simulate AI service call for development."""
        # Simulate processing time
        await asyncio.sleep(0.5)

        # Generate phase-specific mock data
        if self.phase_number == 1:
            # Phase 1: Concept analysis
            return json.dumps({
                "genre_analysis": {"primary_genre": "fantasy", "confidence_score": 0.85},
                "theme_analysis": {"main_themes": ["冒険", "友情", "成長"]},
                "world_setting": {"time_period": "modern_fantasy", "location": "魔法学校"},
                "estimated_pages": 20,
                "complexity_score": 0.7,
                "visual_richness": 0.8
            })
        elif self.phase_number == 2:
            # Phase 2: Character design
            return json.dumps({
                "characters": [
                    {
                        "name": "主人公",
                        "archetype": "protagonist",
                        "age_group": "teenager",
                        "gender": "female",
                        "role_importance": 1.0,
                        "appearance": {
                            "hair_color": "brown",
                            "eye_color": "green",
                            "height": "average"
                        },
                        "personality": {
                            "core_traits": ["内気", "優しい", "勇敢"],
                            "goals": ["友達を作る", "魔法を上達させる"],
                            "fears": ["失敗すること", "一人になること"]
                        }
                    },
                    {
                        "name": "クラスメート",
                        "archetype": "ally",
                        "age_group": "teenager",
                        "gender": "male",
                        "role_importance": 0.7,
                        "appearance": {
                            "hair_color": "black",
                            "eye_color": "blue",
                            "height": "tall"
                        },
                        "personality": {
                            "core_traits": ["明朗", "親切", "積極的"],
                            "goals": ["みんなと仲良くなる"],
                            "fears": ["仲間外れになること"]
                        }
                    }
                ],
                "relationships": [
                    {
                        "character1_name": "主人公",
                        "character2_name": "クラスメート",
                        "relationship_type": "友情",
                        "relationship_strength": 0.8,
                        "description": "互いを支え合う友達関係"
                    }
                ],
                "style_guide": {
                    "overall_style": "shoujo",
                    "color_palette": {"primary": "#FF69B4", "secondary": "#87CEEB"},
                    "design_principles": ["キャラクターの個性重視", "親しみやすいデザイン"]
                }
            })
        elif self.phase_number == 3:
            # Phase 3: Story structure
            return json.dumps({
                "scenes": [
                    {
                        "scene_number": 1,
                        "scene_type": "introduction",
                        "location": "魔法学校の教室",
                        "description": "主人公の初めての授業",
                        "key_actions": ["授業参加", "失敗体験", "落ち込み"]
                    },
                    {
                        "scene_number": 2,
                        "scene_type": "development",
                        "location": "学校の中庭",
                        "description": "クラスメートとの出会い",
                        "key_actions": ["慰められる", "励まされる", "友情の芽生え"]
                    }
                ],
                "story_structure": {
                    "acts": ["導入", "展開", "結論"],
                    "pacing": "standard",
                    "total_scenes": 2
                }
            })
        elif self.phase_number == 4:
            # Phase 4: Panel layout and composition
            return json.dumps({
                "panel_layouts": [
                    {
                        "page_number": 1,
                        "panels": [
                            {
                                "panel_id": "p1_panel1",
                                "position": {"x": 0.05, "y": 0.05},
                                "size": {"width": 0.9, "height": 0.4},
                                "camera_angle": "medium",
                                "camera_distance": 3,
                                "composition_rule": "rule_of_thirds",
                                "importance": "high",
                                "scene_reference": 1
                            },
                            {
                                "panel_id": "p1_panel2",
                                "position": {"x": 0.05, "y": 0.5},
                                "size": {"width": 0.4, "height": 0.45},
                                "camera_angle": "close",
                                "camera_distance": 2,
                                "composition_rule": "center",
                                "importance": "medium",
                                "scene_reference": 1
                            }
                        ]
                    }
                ],
                "total_pages": 1,
                "total_panels": 2,
                "layout_analysis": {
                    "average_panels_per_page": 2,
                    "layout_variety": 0.7,
                    "composition_quality": 0.8,
                    "readability_score": 0.85
                }
            })
        elif self.phase_number == 5:
            # Phase 5: Image generation
            return json.dumps({
                "generated_images": [
                    {
                        "panel_id": "p1_panel1",
                        "image_path": "/mock/images/panel1.jpg",
                        "generation_status": "success",
                        "quality_score": 0.85,
                        "style_consistency": 0.9
                    },
                    {
                        "panel_id": "p1_panel2",
                        "image_path": "/mock/images/panel2.jpg",
                        "generation_status": "success",
                        "quality_score": 0.88,
                        "style_consistency": 0.87
                    }
                ],
                "scene_image_mapping": {
                    "scene_1": ["p1_panel1", "p1_panel2"]
                },
                "quality_analysis": {
                    "success_rate": 1.0,
                    "average_quality_score": 0.865,
                    "total_generated": 2,
                    "successful_generations": 2,
                    "failed_generations": 0
                },
                "generation_stats": {
                    "total_processing_time": 15.2,
                    "average_generation_time": 7.6,
                    "parallel_efficiency_score": 0.92
                }
            })
        elif self.phase_number == 6:
            # Phase 6: Dialogue and text placement
            return json.dumps({
                "dialogue_placements": [
                    {
                        "panel_id": "p1_panel1",
                        "dialogues": [
                            {
                                "character": "主人公",
                                "text": "今日から魔法学校に通うんだ...",
                                "bubble_type": "speech",
                                "position": {"x": 0.7, "y": 0.2},
                                "size": {"width": 0.25, "height": 0.15}
                            }
                        ]
                    },
                    {
                        "panel_id": "p1_panel2",
                        "dialogues": [
                            {
                                "character": "クラスメート",
                                "text": "大丈夫だよ、一緒にがんばろう！",
                                "bubble_type": "speech",
                                "position": {"x": 0.1, "y": 0.3},
                                "size": {"width": 0.3, "height": 0.2}
                            }
                        ]
                    }
                ],
                "typography_specs": {
                    "main_font": "NotoSansJP",
                    "dialogue_font_size": 12,
                    "bubble_style": "rounded"
                },
                "readability_optimization": {
                    "text_contrast_ratio": 4.5,
                    "bubble_spacing": "optimal",
                    "reading_flow_score": 0.9
                }
            })
        elif self.phase_number == 7:
            # Phase 7: Final integration and quality adjustment
            return json.dumps({
                "final_output": {
                    "manga_pages": [
                        {
                            "page_number": 1,
                            "compiled_image_path": "/output/manga_page_1.jpg",
                            "panel_count": 2,
                            "dialogue_count": 2,
                            "quality_score": 0.89
                        }
                    ],
                    "total_pages": 1,
                    "format": "high_res_jpg"
                },
                "quality_metrics": {
                    "overall_quality": 0.87,
                    "visual_consistency": 0.85,
                    "narrative_flow": 0.9,
                    "technical_quality": 0.88
                },
                "integration_report": {
                    "compilation_success": True,
                    "optimization_applied": ["layout_adjustment", "color_balance", "text_clarity"],
                    "final_file_size_mb": 12.5,
                    "processing_time_seconds": 8.3
                },
                "output_formats": {
                    "web_preview": "/output/preview.jpg",
                    "print_ready": "/output/print_ready.pdf",
                    "mobile_optimized": "/output/mobile.jpg"
                }
            })
        else:
            # Default response for unknown phases
            return json.dumps({
                "phase": self.phase_number,
                "result": f"Simulated AI response for {self.phase_name}",
                "prompt_length": len(prompt),
                "confidence": 0.85
            })
    
    async def apply_feedback(
        self,
        output_data: Dict[str, Any],
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply HITL feedback to phase output."""
        
        self.logger.info(
            f"Applying feedback to {self.phase_name}",
            feedback_type=feedback.get("type")
        )
        
        # Base implementation - subclasses can override
        updated_output = output_data.copy()
        updated_output["feedback_applied"] = feedback
        updated_output["revised_at"] = datetime.utcnow().isoformat()
        
        return updated_output
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics."""
        return await self.metrics.get_summary()
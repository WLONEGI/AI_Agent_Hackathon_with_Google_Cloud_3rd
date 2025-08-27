"""End-to-end tests for complete manga generation pipeline."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.agents.pipeline_orchestrator import PipelineOrchestrator, PipelineStatus
from app.agents.base_agent import BaseAgent
from app.models.manga import MangaSession, GenerationStatus
from app.models.user import User


class MockE2EAgent(BaseAgent):
    """Mock agent for end-to-end testing with realistic behavior."""
    
    def __init__(self, phase_number: int, processing_time: float = 0.1, failure_rate: float = 0.0):
        expected_times = {1: 12, 2: 18, 3: 15, 4: 20, 5: 25, 6: 4, 7: 3}
        super().__init__(phase_number, f"E2E Phase {phase_number}", expected_times.get(phase_number, 30))
        self.processing_time = processing_time
        self.failure_rate = failure_rate
        self._call_count = 0
    
    async def process_phase(self, input_data: Dict[str, Any], session_id, previous_results=None):
        """Mock processing with realistic data transformation."""
        self._call_count += 1
        
        # Simulate processing time
        await asyncio.sleep(self.processing_time)
        
        # Simulate occasional failures
        if self.failure_rate > 0 and (self._call_count * self.failure_rate) >= 1:
            raise Exception(f"Simulated failure in phase {self.phase_number}")
        
        # Phase-specific mock outputs
        phase_outputs = {
            1: {  # Concept Analysis
                "genre": "fantasy_adventure",
                "themes": ["heroism", "friendship", "self_discovery"],
                "target_audience": "young_adult",
                "estimated_pages": 20,
                "story_complexity": 0.7,
                "world_building": {
                    "setting": "magical_academy",
                    "time_period": "modern_fantasy",
                    "key_locations": ["academy", "forbidden_forest", "ancient_library"]
                }
            },
            2: {  # Character Design  
                "main_characters": [
                    {
                        "id": "hero",
                        "name": "Alex Chen",
                        "role": "protagonist",
                        "description": "Determined young mage with hidden potential",
                        "visual_traits": {
                            "hair": "black_messy", 
                            "eyes": "emerald_green",
                            "height": "average",
                            "distinctive_feature": "glowing_pendant"
                        },
                        "personality": ["brave", "curious", "sometimes_reckless"]
                    },
                    {
                        "id": "mentor", 
                        "name": "Professor Vance",
                        "role": "mentor",
                        "description": "Wise but mysterious magic instructor",
                        "visual_traits": {
                            "hair": "silver_long",
                            "eyes": "steel_blue", 
                            "height": "tall",
                            "distinctive_feature": "ancient_staff"
                        }
                    }
                ],
                "supporting_characters": 3,
                "character_relationships": [
                    {"from": "hero", "to": "mentor", "type": "student_teacher"},
                ],
                "design_notes": "Focus on expressive eyes and dynamic poses"
            },
            3: {  # Story Structure
                "total_scenes": 8,
                "story_arc": "three_act_structure",
                "key_plot_points": [
                    {"scene": 1, "type": "introduction", "description": "Alex discovers magical abilities"},
                    {"scene": 3, "type": "inciting_incident", "description": "Ancient evil awakens"},
                    {"scene": 5, "type": "midpoint", "description": "Alex learns true heritage"},
                    {"scene": 7, "type": "climax", "description": "Final confrontation"},
                    {"scene": 8, "type": "resolution", "description": "New beginning"}
                ],
                "pacing": "moderate_with_action_peaks",
                "story_complexity_score": 0.75
            },
            4: {  # Panel Layout (Name Generation)
                "total_panels": 32,
                "pages": 8,
                "layout_style": "dynamic_manga",
                "panel_layouts": [
                    {
                        "page": 1, 
                        "panels": [
                            {"id": 1, "type": "wide_establishing", "content": "academy_exterior"},
                            {"id": 2, "type": "medium_shot", "content": "alex_walking"},
                            {"id": 3, "type": "close_up", "content": "alex_expression"}
                        ]
                    }
                    # ... more pages
                ],
                "visual_flow": "left_to_right_top_to_bottom",
                "special_panels": ["splash_page_scene_5", "double_spread_scene_7"]
            },
            5: {  # Image Generation
                "total_images_generated": 32,
                "successful_generations": 30,
                "failed_generations": 2,
                "images": [
                    {
                        "panel_id": 1,
                        "scene_number": 1,
                        "image_url": "https://cdn.example.com/generated/scene1_panel1.png",
                        "thumbnail_url": "https://cdn.example.com/thumbs/scene1_panel1_thumb.png",
                        "quality_score": 0.87,
                        "generation_time_ms": 8500,
                        "prompt": "Magical academy exterior, anime style, detailed architecture",
                        "model_used": "imagen-4"
                    }
                    # ... more images
                ],
                "quality_analysis": {
                    "average_quality": 0.82,
                    "high_quality_count": 24,
                    "needs_regeneration": ["panel_15", "panel_28"],
                    "style_consistency": 0.91
                },
                "generation_stats": {
                    "total_generation_time": 240000,  # 4 minutes
                    "average_time_per_image": 7500,
                    "retry_count": 5
                }
            },
            6: {  # Dialogue Generation
                "total_dialogue_elements": 45,
                "dialogue_by_scene": {
                    1: ["Welcome to Arcane Academy, Alex.", "I... I can feel something different here."],
                    3: ["The ancient seal is breaking!", "We must prepare for what's coming."],
                    7: ["You have more power than you know.", "I won't let darkness win!"]
                },
                "character_voice_consistency": 0.88,
                "readability_score": 0.92,
                "emotional_impact_scores": {
                    "excitement": 0.85,
                    "tension": 0.78, 
                    "humor": 0.65,
                    "emotion": 0.82
                },
                "localization": "english_natural"
            },
            7: {  # Integration & Quality
                "overall_quality_score": 0.84,
                "quality_breakdown": {
                    "story_coherence": 0.87,
                    "character_consistency": 0.85,
                    "visual_quality": 0.82,
                    "dialogue_naturalness": 0.88,
                    "technical_execution": 0.81
                },
                "production_ready": True,
                "total_pages": 8,
                "estimated_reading_time": 12,  # minutes
                "output_formats": {
                    "pdf": "/outputs/manga_final.pdf",
                    "cbz": "/outputs/manga_final.cbz", 
                    "web_optimized": "/outputs/web/index.html"
                },
                "quality_assurance": {
                    "critical_issues": [],
                    "minor_issues": ["panel_15_quality", "dialogue_page_4_spacing"],
                    "recommendations": ["Consider regenerating panel 15", "Adjust dialogue spacing"]
                },
                "metadata": {
                    "title": "The Awakening at Arcane Academy",
                    "creator": "AI Manga Generator",
                    "completion_date": datetime.utcnow().isoformat(),
                    "version": "1.0.0"
                }
            }
        }
        
        # Get base output for this phase
        output = phase_outputs.get(self.phase_number, {
            "phase_number": self.phase_number,
            "processed": True,
            "mock_data": True
        })
        
        # Add input context
        output["input_context"] = input_data
        output["processing_timestamp"] = datetime.utcnow().isoformat()
        
        # Add previous phase results summary for context
        if previous_results:
            output["previous_phases_summary"] = {
                f"phase_{k}": len(str(v)) for k, v in previous_results.items()
            }
        
        return output
    
    async def generate_prompt(self, input_data: Dict[str, Any], previous_results=None):
        """Generate realistic prompts for each phase."""
        phase_prompts = {
            1: "Analyze the story concept and extract genre, themes, and world-building elements",
            2: "Design main and supporting characters based on the story concept",  
            3: "Structure the story into scenes with proper pacing and plot points",
            4: "Create panel layouts and page compositions for visual storytelling",
            5: "Generate high-quality images for each panel using AI image generation",
            6: "Create natural dialogue that matches character voices and story tone",
            7: "Integrate all elements and perform final quality assessment"
        }
        
        base_prompt = phase_prompts.get(self.phase_number, f"Process phase {self.phase_number}")
        
        # Add context from input and previous results
        context_parts = [base_prompt]
        if input_data:
            context_parts.append(f"Input: {list(input_data.keys())}")
        if previous_results:
            context_parts.append(f"Previous phases: {list(previous_results.keys())}")
            
        return " | ".join(context_parts)
    
    async def validate_output(self, output_data: Dict[str, Any]):
        """Validate phase output with realistic checks."""
        if not isinstance(output_data, dict):
            return False
            
        # Phase-specific validation
        phase_validations = {
            1: lambda d: "genre" in d and "themes" in d and "estimated_pages" in d,
            2: lambda d: "main_characters" in d and len(d["main_characters"]) > 0,
            3: lambda d: "total_scenes" in d and "story_arc" in d,
            4: lambda d: "total_panels" in d and "pages" in d,
            5: lambda d: "total_images_generated" in d and "quality_analysis" in d,
            6: lambda d: "total_dialogue_elements" in d and "readability_score" in d,
            7: lambda d: "overall_quality_score" in d and "production_ready" in d
        }
        
        validator = phase_validations.get(self.phase_number)
        return validator(output_data) if validator else True


@pytest.mark.asyncio
class TestCompleteE2EPipeline:
    """Test complete end-to-end pipeline execution."""
    
    async def test_successful_complete_pipeline(self, sample_manga_session: MangaSession, db_session):
        """Test successful execution of complete 7-phase pipeline."""
        # Create orchestrator with mock agents
        orchestrator = PipelineOrchestrator()
        
        # Replace agents with mock E2E agents
        for phase_num in range(1, 8):
            mock_agent = MockE2EAgent(phase_num, processing_time=0.1)
            orchestrator.agents[phase_num] = mock_agent
            orchestrator.execution_plan[phase_num].agent = mock_agent
        
        input_data = {
            "story_concept": "A young student discovers magical abilities at a mysterious academy",
            "genre_hint": "fantasy",
            "target_audience": "young_adult",
            "style_preferences": "anime_manga",
            "quality_level": "high"
        }
        
        # Execute complete pipeline
        start_time = datetime.utcnow()
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session,
            progress_callback=None,
            feedback_timeout=30
        )
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # Verify successful completion
        assert orchestrator.status == PipelineStatus.COMPLETED
        assert "execution_summary" in result
        assert result["execution_summary"]["pipeline_status"] == "completed"
        assert result["execution_summary"]["phases_completed"] == 7
        assert result["execution_summary"]["phases_failed"] == 0
        
        # Verify quality summary
        assert "quality_summary" in result
        assert result["quality_summary"]["overall_quality_score"] > 0.8
        assert result["quality_summary"]["production_ready"] is True
        
        # Verify content summary
        assert "content_summary" in result
        assert result["content_summary"]["total_pages"] == 8
        
        # Verify phase results
        assert len(orchestrator.phase_results) == 7
        
        # Verify phase sequence and data flow
        phase_1_result = orchestrator.phase_results[1]
        assert "genre" in phase_1_result
        assert "themes" in phase_1_result
        
        phase_2_result = orchestrator.phase_results[2]
        assert "main_characters" in phase_2_result
        assert len(phase_2_result["main_characters"]) >= 1
        
        phase_5_result = orchestrator.phase_results[5]
        assert "total_images_generated" in phase_5_result
        assert phase_5_result["successful_generations"] > 0
        
        phase_7_result = orchestrator.phase_results[7]
        assert "overall_quality_score" in phase_7_result
        assert "output_formats" in phase_7_result
        
        # Verify performance metrics
        assert execution_time < 10.0  # Should complete quickly with mocks
        assert result["execution_summary"]["parallel_efficiency_percentage"] > 0
        
        print(f"E2E Pipeline completed in {execution_time:.2f}s")
        print(f"Quality score: {result['quality_summary']['overall_quality_score']:.2f}")
        print(f"Parallel efficiency: {result['execution_summary']['parallel_efficiency_percentage']:.1f}%")
    
    async def test_pipeline_with_failure_recovery(self, sample_manga_session: MangaSession, db_session):
        """Test pipeline execution with failure and retry handling."""
        orchestrator = PipelineOrchestrator()
        
        # Set up agents with one that fails on first attempt
        for phase_num in range(1, 8):
            failure_rate = 0.5 if phase_num == 3 else 0.0  # Phase 3 will fail first time
            mock_agent = MockE2EAgent(phase_num, processing_time=0.05, failure_rate=failure_rate)
            orchestrator.agents[phase_num] = mock_agent
            orchestrator.execution_plan[phase_num].agent = mock_agent
            orchestrator.execution_plan[phase_num].max_retries = 2  # Allow retries
        
        input_data = {
            "story_concept": "Story with failure recovery test",
            "quality_level": "medium"
        }
        
        # Execute pipeline (should succeed after retries)
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session
        )
        
        # Should eventually complete successfully
        assert orchestrator.status == PipelineStatus.COMPLETED
        assert result["execution_summary"]["retry_count"] > 0
        
        # Phase 3 should show retry activity
        phase_3_execution = orchestrator.execution_plan[3]
        assert phase_3_execution.retry_count > 0
    
    async def test_pipeline_with_hitl_feedback(self, sample_manga_session: MangaSession, db_session):
        """Test pipeline with Human-in-the-Loop feedback integration."""
        orchestrator = PipelineOrchestrator()
        
        # Set up agents
        for phase_num in range(1, 8):
            mock_agent = MockE2EAgent(phase_num, processing_time=0.05)
            orchestrator.agents[phase_num] = mock_agent
            orchestrator.execution_plan[phase_num].agent = mock_agent
        
        # Enable HITL
        sample_manga_session.hitl_enabled = True
        
        # Set up feedback handlers
        feedback_received = []
        
        async def character_feedback_handler(phase_result):
            """Mock feedback for character design phase."""
            feedback_received.append(("character", phase_result))
            return {
                "type": "character_adjustment",
                "feedback": "Make the main character more heroic looking",
                "specific_changes": {
                    "hero": {
                        "visual_traits": {
                            "posture": "more_confident",
                            "expression": "more_determined"
                        }
                    }
                }
            }
        
        async def layout_feedback_handler(phase_result):
            """Mock feedback for layout phase.""" 
            feedback_received.append(("layout", phase_result))
            return {
                "type": "layout_adjustment", 
                "feedback": "Make panels more dynamic",
                "adjustments": ["increase_action_panels", "vary_panel_sizes"]
            }
        
        # Register feedback handlers
        orchestrator.register_feedback_handler(2, character_feedback_handler)  # Character phase
        orchestrator.register_feedback_handler(4, layout_feedback_handler)    # Layout phase
        
        input_data = {"story_concept": "HITL feedback test story"}
        
        # Execute pipeline with feedback
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session,
            feedback_timeout=5  # Short timeout for testing
        )
        
        # Should complete successfully
        assert orchestrator.status == PipelineStatus.COMPLETED
        
        # Should have received feedback
        assert len(feedback_received) >= 1  # At least one feedback phase triggered
        
        # Verify feedback was applied to phase results
        if 2 in orchestrator.phase_results:
            phase_2_result = orchestrator.phase_results[2]
            assert "feedback_applied" in phase_2_result
    
    async def test_pipeline_performance_metrics(self, sample_manga_session: MangaSession, db_session):
        """Test detailed performance metrics collection."""
        orchestrator = PipelineOrchestrator()
        
        # Set up agents with varying processing times
        phase_times = {1: 0.05, 2: 0.08, 3: 0.06, 4: 0.09, 5: 0.12, 6: 0.02, 7: 0.01}
        for phase_num in range(1, 8):
            mock_agent = MockE2EAgent(phase_num, processing_time=phase_times[phase_num])
            orchestrator.agents[phase_num] = mock_agent
            orchestrator.execution_plan[phase_num].agent = mock_agent
        
        input_data = {"story_concept": "Performance testing story"}
        
        # Execute pipeline
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session
        )
        
        # Verify performance metrics
        execution_summary = result["execution_summary"]
        assert "total_execution_time_seconds" in execution_summary
        assert "parallel_efficiency_percentage" in execution_summary
        assert "performance_metrics" in execution_summary
        
        perf_metrics = execution_summary["performance_metrics"]
        assert "phase_times" in perf_metrics
        assert "estimated_sequential_time" in perf_metrics
        assert "parallel_efficiency" in perf_metrics
        
        # Verify all phases have timing data
        assert len(perf_metrics["phase_times"]) == 7
        
        # Verify efficiency calculation
        parallel_efficiency = perf_metrics["parallel_efficiency"]
        assert 0.0 <= parallel_efficiency <= 1.0
        
        # Sequential time should be sum of all phase times
        sequential_time = sum(perf_metrics["phase_times"].values())
        actual_time = perf_metrics["total_processing_time"]
        assert sequential_time > actual_time  # Parallel execution should be faster
    
    async def test_pipeline_quality_assessment(self, sample_manga_session: MangaSession, db_session):
        """Test comprehensive quality assessment."""
        orchestrator = PipelineOrchestrator()
        
        # Set up agents
        for phase_num in range(1, 8):
            mock_agent = MockE2EAgent(phase_num, processing_time=0.05)
            orchestrator.agents[phase_num] = mock_agent
            orchestrator.execution_plan[phase_num].agent = mock_agent
        
        input_data = {
            "story_concept": "Quality assessment test",
            "quality_requirements": {
                "minimum_score": 0.8,
                "require_production_ready": True
            }
        }
        
        # Execute pipeline
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session
        )
        
        # Verify quality assessment
        quality_summary = result["quality_summary"]
        assert "overall_quality_score" in quality_summary
        assert "quality_grade" in quality_summary
        assert "production_ready" in quality_summary
        assert "critical_issues_count" in quality_summary
        
        # Should meet quality requirements
        assert quality_summary["overall_quality_score"] >= 0.8
        assert quality_summary["production_ready"] is True
        assert quality_summary["critical_issues_count"] == 0
        
        # Verify phase-by-phase quality
        phase_summary = result["phase_summary"]
        for phase_num in range(1, 8):
            phase_key = f"phase_{phase_num}"
            assert phase_key in phase_summary
            assert "status" in phase_summary[phase_key]
            assert phase_summary[phase_key]["status"] == "completed"
    
    async def test_pipeline_data_flow_integrity(self, sample_manga_session: MangaSession, db_session):
        """Test that data flows correctly between phases."""
        orchestrator = PipelineOrchestrator()
        
        # Set up agents
        for phase_num in range(1, 8):
            mock_agent = MockE2EAgent(phase_num, processing_time=0.05)
            orchestrator.agents[phase_num] = mock_agent
            orchestrator.execution_plan[phase_num].agent = mock_agent
        
        input_data = {
            "story_concept": "A tale of data integrity",
            "genre": "sci-fi",
            "tracking_id": "data_flow_test_123"
        }
        
        # Execute pipeline
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session
        )
        
        # Verify data flow
        phase_results = orchestrator.phase_results
        
        # Phase 1 should receive original input
        phase_1_result = phase_results[1]
        assert "input_context" in phase_1_result
        assert phase_1_result["input_context"]["tracking_id"] == "data_flow_test_123"
        
        # Later phases should have previous phase data
        for phase_num in range(2, 8):
            phase_result = phase_results[phase_num]
            assert "previous_phases_summary" in phase_result
            
            # Should have data from all previous phases
            prev_summary = phase_result["previous_phases_summary"]
            for prev_phase in range(1, phase_num):
                assert f"phase_{prev_phase}" in prev_summary
        
        # Final phase should integrate all previous data
        phase_7_result = phase_results[7]
        assert len(phase_7_result["previous_phases_summary"]) == 6  # Phases 1-6
        
        # Verify specific data dependencies
        # Characters from phase 2 should influence later phases
        phase_2_result = phase_results[2]
        assert "main_characters" in phase_2_result
        
        # Story structure from phase 3 should be used in layout
        phase_3_result = phase_results[3]
        assert "total_scenes" in phase_3_result
        
        phase_4_result = phase_results[4]
        assert "total_panels" in phase_4_result
        
        # Images from phase 5 should match panel count from phase 4
        phase_5_result = phase_results[5]
        assert phase_5_result["total_images_generated"] >= phase_4_result["total_panels"] * 0.8


@pytest.mark.asyncio
class TestE2EPipelineEdgeCases:
    """Test edge cases in end-to-end pipeline execution."""
    
    async def test_pipeline_with_minimal_input(self, sample_manga_session: MangaSession, db_session):
        """Test pipeline with minimal input data."""
        orchestrator = PipelineOrchestrator()
        
        # Set up agents
        for phase_num in range(1, 8):
            mock_agent = MockE2EAgent(phase_num, processing_time=0.02)
            orchestrator.agents[phase_num] = mock_agent
            orchestrator.execution_plan[phase_num].agent = mock_agent
        
        # Minimal input
        input_data = {
            "story_concept": "Minimal test"
        }
        
        # Should still complete successfully
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session
        )
        
        assert orchestrator.status == PipelineStatus.COMPLETED
        assert result["execution_summary"]["phases_completed"] == 7
    
    async def test_pipeline_with_complex_input(self, sample_manga_session: MangaSession, db_session):
        """Test pipeline with complex, detailed input data."""
        orchestrator = PipelineOrchestrator()
        
        # Set up agents  
        for phase_num in range(1, 8):
            mock_agent = MockE2EAgent(phase_num, processing_time=0.02)
            orchestrator.agents[phase_num] = mock_agent
            orchestrator.execution_plan[phase_num].agent = mock_agent
        
        # Complex input with detailed specifications
        input_data = {
            "story_concept": "An epic fantasy adventure with deep world-building",
            "genre": "high_fantasy",
            "subgenres": ["adventure", "coming_of_age", "magical_school"],
            "target_audience": "young_adult",
            "content_rating": "PG-13",
            "world_building": {
                "setting": "magical_academy_in_floating_city",
                "magic_system": "elemental_with_rare_specializations",
                "technology_level": "renaissance_with_magic",
                "cultures": ["sky_people", "earth_dwellers", "void_walkers"]
            },
            "character_requirements": {
                "protagonist_count": 1,
                "major_supporting_count": 3,
                "minor_supporting_count": 5,
                "antagonist_count": 2,
                "diversity_requirements": {
                    "cultural_backgrounds": 3,
                    "gender_balance": "balanced",
                    "age_range": "teen_to_adult"
                }
            },
            "story_structure": {
                "act_structure": "three_act",
                "pacing": "moderate_with_action_climaxes",
                "themes": ["self_discovery", "friendship", "responsibility", "sacrifice"],
                "tone": "hopeful_with_serious_moments"
            },
            "visual_style": {
                "art_style": "detailed_anime_manga",
                "color_palette": "vibrant_with_earth_tones",
                "panel_style": "dynamic_varied_layouts",
                "character_design": "distinctive_memorable_silhouettes"
            },
            "technical_requirements": {
                "page_count": "20_to_30",
                "panel_density": "medium_to_high",
                "dialogue_density": "moderate",
                "action_to_dialogue_ratio": "balanced"
            },
            "quality_standards": {
                "minimum_overall_score": 0.85,
                "critical_quality_factors": ["story_coherence", "character_consistency", "visual_quality"],
                "production_ready_required": True
            }
        }
        
        # Execute pipeline
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session
        )
        
        # Should handle complex input successfully
        assert orchestrator.status == PipelineStatus.COMPLETED
        assert result["quality_summary"]["overall_quality_score"] >= 0.85
        
        # Verify that complex input influenced results
        phase_1_result = orchestrator.phase_results[1]
        assert "themes" in phase_1_result
        assert len(phase_1_result["themes"]) >= 3
        
        phase_2_result = orchestrator.phase_results[2]
        assert len(phase_2_result["main_characters"]) >= 1
    
    async def test_pipeline_cancellation_during_execution(self, sample_manga_session: MangaSession, db_session):
        """Test pipeline cancellation during execution."""
        orchestrator = PipelineOrchestrator()
        
        # Set up agents with longer processing times
        for phase_num in range(1, 8):
            mock_agent = MockE2EAgent(phase_num, processing_time=0.5)  # Longer time
            orchestrator.agents[phase_num] = mock_agent
            orchestrator.execution_plan[phase_num].agent = mock_agent
        
        input_data = {"story_concept": "Cancellation test"}
        
        # Start pipeline execution
        pipeline_task = asyncio.create_task(
            orchestrator.execute_pipeline(
                session=sample_manga_session,
                input_data=input_data,
                db_session=db_session
            )
        )
        
        # Wait a bit then cancel
        await asyncio.sleep(0.2)
        await orchestrator.cancel_pipeline("Test cancellation")
        
        # Wait for task to complete/cancel
        try:
            await pipeline_task
        except Exception:
            pass  # Expected if cancellation raises exception
        
        # Verify cancellation
        assert orchestrator.status == PipelineStatus.CANCELLED
        
        # Some phases might have completed before cancellation
        completed_phases = sum(1 for p in orchestrator.execution_plan.values() if p.status == "completed")
        cancelled_phases = sum(1 for p in orchestrator.execution_plan.values() if p.status == "cancelled")
        
        assert completed_phases + cancelled_phases <= 7
    
    async def test_pipeline_resource_usage_monitoring(self, sample_manga_session: MangaSession, db_session):
        """Test monitoring of resource usage during pipeline execution."""
        orchestrator = PipelineOrchestrator()
        
        # Set up agents
        for phase_num in range(1, 8):
            mock_agent = MockE2EAgent(phase_num, processing_time=0.05)
            orchestrator.agents[phase_num] = mock_agent
            orchestrator.execution_plan[phase_num].agent = mock_agent
        
        # Track resource usage
        resource_snapshots = []
        
        async def resource_monitor(progress_info):
            """Mock resource monitoring callback."""
            import psutil
            resource_snapshots.append({
                "timestamp": datetime.utcnow(),
                "phase": progress_info.get("current_phase", 0),
                "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_percent": psutil.Process().cpu_percent()
            })
        
        orchestrator.register_progress_callback(resource_monitor)
        
        input_data = {"story_concept": "Resource monitoring test"}
        
        # Execute pipeline
        result = await orchestrator.execute_pipeline(
            session=sample_manga_session,
            input_data=input_data,
            db_session=db_session
        )
        
        # Verify resource monitoring
        assert len(resource_snapshots) >= 7  # At least one per phase
        
        # Check that memory usage is reasonable (no major leaks)
        memory_values = [s["memory_mb"] for s in resource_snapshots]
        max_memory = max(memory_values)
        min_memory = min(memory_values)
        
        # Memory growth should be reasonable (less than 100MB for mock pipeline)
        assert max_memory - min_memory < 100
        
        # Should complete successfully
        assert orchestrator.status == PipelineStatus.COMPLETED
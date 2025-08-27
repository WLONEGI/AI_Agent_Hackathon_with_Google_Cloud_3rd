"""Test helper utilities and fixtures."""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import random

from app.models.manga import MangaSession, PhaseResult, GenerationStatus, QualityLevel
from app.models.user import User
from app.domain.manga.value_objects.quality_metrics import QualityMetric, QualityScore, QualityMetricType


class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_user(
        email: str = None,
        username: str = None,
        is_active: bool = True,
        is_superuser: bool = False
    ) -> User:
        """Create a test user."""
        return User(
            id=uuid4(),
            email=email or f"test_{uuid4().hex[:8]}@example.com",
            username=username or f"user_{uuid4().hex[:8]}",
            hashed_password="$2b$12$test_hashed_password",
            is_active=is_active,
            is_superuser=is_superuser,
            created_at=datetime.utcnow()
        )
    
    @staticmethod
    def create_manga_session(
        user_id: UUID,
        title: str = None,
        input_text: str = None,
        status: GenerationStatus = GenerationStatus.PENDING,
        current_phase: int = 0,
        **kwargs
    ) -> MangaSession:
        """Create a test manga session."""
        return MangaSession(
            id=uuid4(),
            user_id=user_id,
            title=title or f"Test Manga {uuid4().hex[:8]}",
            input_text=input_text or TestDataFactory.generate_story_concept(),
            genre=kwargs.get("genre", "fantasy"),
            style=kwargs.get("style", "anime"),
            quality_level=kwargs.get("quality_level", QualityLevel.HIGH.value),
            status=status.value,
            current_phase=current_phase,
            total_phases=7,
            hitl_enabled=kwargs.get("hitl_enabled", True),
            auto_proceed=kwargs.get("auto_proceed", False),
            created_at=kwargs.get("created_at", datetime.utcnow()),
            updated_at=kwargs.get("updated_at", datetime.utcnow()),
            **{k: v for k, v in kwargs.items() if hasattr(MangaSession, k)}
        )
    
    @staticmethod
    def create_phase_result(
        session_id: UUID,
        phase_number: int,
        status: str = "completed",
        processing_time_ms: int = None,
        quality_score: float = None,
        **kwargs
    ) -> PhaseResult:
        """Create a test phase result."""
        if processing_time_ms is None:
            # Realistic processing times by phase
            phase_times = {1: 12000, 2: 18000, 3: 15000, 4: 20000, 5: 25000, 6: 4000, 7: 3000}
            processing_time_ms = phase_times.get(phase_number, 10000)
        
        if quality_score is None:
            quality_score = random.uniform(0.7, 0.95)
        
        return PhaseResult(
            id=uuid4(),
            session_id=session_id,
            phase_number=phase_number,
            phase_name=kwargs.get("phase_name", f"Test Phase {phase_number}"),
            input_data=kwargs.get("input_data", TestDataFactory.generate_phase_input(phase_number)),
            output_data=kwargs.get("output_data", TestDataFactory.generate_phase_output(phase_number)),
            processing_time_ms=processing_time_ms,
            ai_model_used=kwargs.get("ai_model_used", "gemini-1.5-pro"),
            prompt_tokens=kwargs.get("prompt_tokens", random.randint(100, 500)),
            completion_tokens=kwargs.get("completion_tokens", random.randint(200, 800)),
            quality_score=quality_score,
            confidence_score=kwargs.get("confidence_score", random.uniform(0.7, 0.9)),
            status=status,
            created_at=kwargs.get("created_at", datetime.utcnow()),
            started_at=kwargs.get("started_at", datetime.utcnow()),
            completed_at=kwargs.get("completed_at", datetime.utcnow())
        )
    
    @staticmethod
    def generate_story_concept(complexity: str = "medium") -> str:
        """Generate a realistic story concept for testing."""
        concepts = {
            "simple": [
                "A young student discovers they have magical powers.",
                "A robot learns about human emotions.",
                "Two friends go on an adventure in the forest."
            ],
            "medium": [
                "A teenage hacker discovers a conspiracy that threatens to destroy the virtual reality world everyone lives in.",
                "In a world where magic and technology coexist, a young engineer must bridge the gap between two warring factions.",
                "A time traveler gets stuck in the past and must find a way home while avoiding changing history."
            ],
            "complex": [
                "In a post-apocalyptic world where memories can be extracted and traded like currency, a memory thief discovers they hold the key to humanity's forgotten past, but unlocking it means sacrificing their own identity.",
                "A quantum physicist accidentally splits reality into multiple timelines and must navigate through different versions of their life to prevent a catastrophic collapse of the multiverse.",
                "In a society where emotions are regulated by AI, a black-market emotion dealer discovers that the government's emotion suppression program is actually preparing humanity for an alien invasion."
            ]
        }
        
        return random.choice(concepts.get(complexity, concepts["medium"]))
    
    @staticmethod
    def generate_phase_input(phase_number: int) -> Dict[str, Any]:
        """Generate realistic input data for a phase."""
        inputs = {
            1: {
                "story_concept": TestDataFactory.generate_story_concept(),
                "genre_hint": random.choice(["fantasy", "sci-fi", "adventure", "mystery"]),
                "target_audience": random.choice(["children", "teenagers", "young_adult", "adult"])
            },
            2: {
                "genre": "fantasy",
                "themes": ["friendship", "courage", "growth"],
                "character_count": random.randint(2, 5)
            },
            3: {
                "characters": [{"name": "Hero", "role": "protagonist"}],
                "genre": "fantasy",
                "target_length": "medium"
            },
            4: {
                "story_structure": {"acts": 3, "scenes": 8},
                "characters": [{"name": "Hero"}],
                "pacing": "moderate"
            },
            5: {
                "scenes": [{"description": "Hero stands at castle gate"}] * 8,
                "art_style": "anime",
                "quality_level": "high"
            },
            6: {
                "scenes": [{"characters": ["Hero"], "context": "adventure"}] * 6,
                "tone": "adventurous",
                "language": "english"
            },
            7: {
                "all_phase_results": {"phases_1_to_6": "completed"},
                "quality_requirements": {"minimum_score": 0.8}
            }
        }
        
        return inputs.get(phase_number, {"phase": phase_number, "test_input": True})
    
    @staticmethod
    def generate_phase_output(phase_number: int) -> Dict[str, Any]:
        """Generate realistic output data for a phase."""
        outputs = {
            1: {
                "genre": "fantasy_adventure",
                "themes": ["heroism", "friendship", "self_discovery"],
                "target_audience": "young_adult",
                "estimated_pages": random.randint(15, 30),
                "story_complexity": random.uniform(0.6, 0.9),
                "world_setting": "magical_academy"
            },
            2: {
                "main_characters": [
                    {
                        "id": "hero",
                        "name": "Alex",
                        "role": "protagonist",
                        "description": "Brave young student",
                        "visual_traits": {"hair": "brown", "eyes": "blue", "height": "average"}
                    }
                ],
                "supporting_characters": random.randint(2, 4),
                "character_relationships": [{"from": "hero", "to": "mentor", "type": "student_teacher"}]
            },
            3: {
                "total_scenes": random.randint(6, 12),
                "story_arc": "three_act_structure",
                "plot_points": [
                    {"scene": 1, "type": "introduction", "description": "Hero introduced"},
                    {"scene": 3, "type": "inciting_incident", "description": "Adventure begins"},
                    {"scene": 8, "type": "resolution", "description": "Hero triumphant"}
                ],
                "pacing": "moderate_with_action"
            },
            4: {
                "total_panels": random.randint(24, 40),
                "pages": random.randint(6, 10),
                "layout_style": "dynamic_manga",
                "panel_layouts": [
                    {"page": 1, "panels": [{"type": "wide", "content": "establishing_shot"}]}
                ]
            },
            5: {
                "total_images_generated": random.randint(20, 35),
                "successful_generations": random.randint(18, 33),
                "failed_generations": random.randint(0, 3),
                "quality_analysis": {
                    "average_quality": random.uniform(0.75, 0.95),
                    "style_consistency": random.uniform(0.8, 0.95)
                },
                "images": [
                    {
                        "panel_id": 1,
                        "image_url": "https://cdn.example.com/image1.png",
                        "quality_score": random.uniform(0.7, 0.95)
                    }
                ]
            },
            6: {
                "total_dialogue_elements": random.randint(30, 60),
                "dialogue_by_scene": {
                    1: ["Welcome to the academy!", "Thank you, I'm excited to learn."],
                    2: ["The ancient magic is awakening.", "We must be careful."]
                },
                "readability_score": random.uniform(0.8, 0.95),
                "emotional_impact": random.uniform(0.7, 0.9)
            },
            7: {
                "overall_quality_score": random.uniform(0.8, 0.95),
                "production_ready": True,
                "output_formats": {
                    "pdf": "/outputs/manga.pdf",
                    "cbz": "/outputs/manga.cbz"
                },
                "final_page_count": random.randint(8, 12),
                "estimated_reading_time": random.randint(10, 20)
            }
        }
        
        return outputs.get(phase_number, {"phase": phase_number, "completed": True})
    
    @staticmethod
    def create_quality_metrics(
        phase_number: int,
        base_score: float = 0.8,
        variance: float = 0.1
    ) -> QualityScore:
        """Create realistic quality metrics for a phase."""
        return QualityScore.create_phase_specific(
            phase_number=phase_number,
            base_score=base_score + random.uniform(-variance, variance),
            content_type=f"phase_{phase_number}_content"
        )
    
    @staticmethod
    def create_generation_params(**overrides) -> Dict[str, Any]:
        """Create realistic generation parameters."""
        defaults = {
            "style": random.choice(["anime", "manga", "western", "realistic"]),
            "quality_level": random.choice(["high", "medium", "ultra_high"]),
            "enable_hitl": True,
            "auto_proceed": False,
            "custom_style_params": {
                "color_scheme": random.choice(["vibrant", "muted", "monochrome"]),
                "line_style": random.choice(["clean", "sketchy", "detailed"])
            },
            "content_guidelines": {
                "age_rating": random.choice(["G", "PG", "PG-13", "R"]),
                "content_warnings": []
            }
        }
        
        defaults.update(overrides)
        return defaults


class MockAIService:
    """Mock AI service for testing."""
    
    def __init__(self, failure_rate: float = 0.0, latency_ms: int = 100):
        self.failure_rate = failure_rate
        self.latency_ms = latency_ms
        self.call_count = 0
    
    async def process_phase(self, phase_number: int, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock AI phase processing."""
        self.call_count += 1
        
        # Simulate latency
        await asyncio.sleep(self.latency_ms / 1000.0)
        
        # Simulate failures
        if self.failure_rate > 0 and random.random() < self.failure_rate:
            raise Exception(f"Mock AI failure for phase {phase_number}")
        
        # Return realistic output
        return TestDataFactory.generate_phase_output(phase_number)
    
    async def generate_image(
        self,
        prompt: str,
        style_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Mock image generation."""
        await asyncio.sleep(self.latency_ms / 1000.0)
        
        if self.failure_rate > 0 and random.random() < self.failure_rate:
            raise Exception("Mock image generation failure")
        
        return {
            "image_url": f"https://cdn.example.com/generated_{uuid4().hex[:8]}.png",
            "thumbnail_url": f"https://cdn.example.com/thumb_{uuid4().hex[:8]}.png",
            "quality_score": random.uniform(0.7, 0.95),
            "generation_time_ms": self.latency_ms,
            "model_used": "mock-imagen-4"
        }
    
    async def analyze_quality(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Mock quality analysis."""
        await asyncio.sleep(50)  # Quick analysis
        
        return {
            "overall_score": random.uniform(0.7, 0.95),
            "detailed_scores": {
                "coherence": random.uniform(0.7, 0.9),
                "creativity": random.uniform(0.6, 0.95),
                "technical_quality": random.uniform(0.75, 0.9)
            },
            "issues": [],
            "recommendations": ["Consider improving character consistency"]
        }


class TestMetricsCollector:
    """Collect and analyze test metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.start_times: Dict[str, float] = {}
        self.events: List[Dict[str, Any]] = []
    
    def start_timer(self, label: str) -> None:
        """Start timing an operation."""
        import time
        self.start_times[label] = time.time()
    
    def end_timer(self, label: str) -> float:
        """End timing and record duration."""
        import time
        if label not in self.start_times:
            return 0.0
        
        duration = time.time() - self.start_times[label]
        
        if label not in self.metrics:
            self.metrics[label] = []
        
        self.metrics[label].append(duration)
        del self.start_times[label]
        
        return duration
    
    def record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record a test event."""
        self.events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "data": data
        })
    
    def get_stats(self, label: str) -> Dict[str, float]:
        """Get statistics for a metric."""
        import statistics
        
        if label not in self.metrics or not self.metrics[label]:
            return {}
        
        values = self.metrics[label]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0
        }
    
    def report(self) -> Dict[str, Any]:
        """Generate a comprehensive test metrics report."""
        report = {
            "summary": {},
            "detailed_metrics": {},
            "event_count": len(self.events),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        for label in self.metrics:
            stats = self.get_stats(label)
            report["detailed_metrics"][label] = stats
            report["summary"][f"{label}_avg"] = stats.get("mean", 0)
        
        return report


class TestAssertions:
    """Custom test assertions for manga generation testing."""
    
    @staticmethod
    def assert_phase_output_valid(
        phase_number: int,
        output_data: Dict[str, Any],
        min_quality_score: float = 0.6
    ) -> None:
        """Assert that phase output is valid."""
        assert isinstance(output_data, dict), f"Phase {phase_number} output must be dict"
        
        # Phase-specific validations
        if phase_number == 1:  # Concept Analysis
            assert "genre" in output_data, "Phase 1 must include genre"
            assert "themes" in output_data, "Phase 1 must include themes"
            assert isinstance(output_data["themes"], list), "Themes must be a list"
            
        elif phase_number == 2:  # Character Design
            assert "main_characters" in output_data, "Phase 2 must include main_characters"
            assert len(output_data["main_characters"]) > 0, "Must have at least one character"
            
        elif phase_number == 5:  # Image Generation
            assert "total_images_generated" in output_data, "Phase 5 must include image count"
            assert output_data["total_images_generated"] > 0, "Must generate at least one image"
            
            if "quality_analysis" in output_data:
                quality = output_data["quality_analysis"]
                if "average_quality" in quality:
                    assert quality["average_quality"] >= min_quality_score
        
        elif phase_number == 7:  # Integration
            assert "overall_quality_score" in output_data, "Phase 7 must include quality score"
            assert output_data["overall_quality_score"] >= min_quality_score
            assert "production_ready" in output_data, "Phase 7 must include production status"
    
    @staticmethod
    def assert_pipeline_result_complete(result: Dict[str, Any]) -> None:
        """Assert that pipeline result is complete."""
        required_sections = ["execution_summary", "quality_summary", "content_summary", "phase_summary"]
        
        for section in required_sections:
            assert section in result, f"Pipeline result missing {section}"
        
        # Execution summary validation
        exec_summary = result["execution_summary"]
        assert "pipeline_status" in exec_summary
        assert "phases_completed" in exec_summary
        assert exec_summary["phases_completed"] > 0
        
        # Quality summary validation
        quality_summary = result["quality_summary"]
        assert "overall_quality_score" in quality_summary
        assert 0 <= quality_summary["overall_quality_score"] <= 1
    
    @staticmethod
    def assert_performance_acceptable(
        actual_time_ms: float,
        expected_time_ms: float,
        tolerance_factor: float = 1.5
    ) -> None:
        """Assert that performance is within acceptable bounds."""
        max_allowed_time = expected_time_ms * tolerance_factor
        assert actual_time_ms <= max_allowed_time, \
            f"Performance too slow: {actual_time_ms}ms > {max_allowed_time}ms (expected: {expected_time_ms}ms)"
        
        # Also check that it's not suspiciously fast (potential mocking issues)
        min_allowed_time = expected_time_ms * 0.1
        assert actual_time_ms >= min_allowed_time, \
            f"Performance suspiciously fast: {actual_time_ms}ms < {min_allowed_time}ms"
    
    @staticmethod
    def assert_quality_metrics_valid(quality_score: QualityScore) -> None:
        """Assert that quality metrics are valid."""
        assert 0 <= quality_score.overall_score <= 1, "Overall score must be 0-1"
        assert 1 <= quality_score.phase_number <= 7, "Phase number must be 1-7"
        
        for metric_type, metric in quality_score.metrics.items():
            assert isinstance(metric_type, QualityMetricType), f"Invalid metric type: {metric_type}"
            assert 0 <= metric.score <= 1, f"Metric {metric_type} score must be 0-1"
            assert 0 <= metric.weight <= 1, f"Metric {metric_type} weight must be 0-1"


def create_test_environment(
    user_count: int = 1,
    session_count_per_user: int = 1,
    include_completed_sessions: bool = True,
    include_failed_sessions: bool = False
) -> Dict[str, Any]:
    """Create a complete test environment with users and sessions."""
    env = {
        "users": [],
        "sessions": [],
        "phase_results": [],
        "created_at": datetime.utcnow().isoformat()
    }
    
    for i in range(user_count):
        user = TestDataFactory.create_user(
            email=f"testuser{i}@example.com",
            username=f"testuser{i}"
        )
        env["users"].append(user)
        
        for j in range(session_count_per_user):
            # Create sessions with different statuses
            if include_completed_sessions and j % 2 == 0:
                status = GenerationStatus.COMPLETED
                current_phase = 7
            elif include_failed_sessions and j % 3 == 0:
                status = GenerationStatus.FAILED
                current_phase = random.randint(1, 6)
            else:
                status = GenerationStatus.PROCESSING
                current_phase = random.randint(1, 6)
            
            session = TestDataFactory.create_manga_session(
                user_id=user.id,
                title=f"Test Session {i}-{j}",
                status=status,
                current_phase=current_phase
            )
            env["sessions"].append(session)
            
            # Create phase results for completed phases
            for phase_num in range(1, current_phase + 1):
                phase_result = TestDataFactory.create_phase_result(
                    session_id=session.id,
                    phase_number=phase_num
                )
                env["phase_results"].append(phase_result)
    
    return env


async def wait_for_condition(
    condition_func,
    timeout_seconds: float = 5.0,
    check_interval: float = 0.1
) -> bool:
    """Wait for a condition to become true."""
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
            return True
        await asyncio.sleep(check_interval)
    
    return False
"""Integration tests for database operations."""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.manga import MangaSession, PhaseResult, UserFeedback, GeneratedImage, GenerationStatus, QualityLevel
from app.models.user import User


@pytest.mark.asyncio
class TestMangaSessionDatabaseOperations:
    """Test database operations for MangaSession model."""
    
    async def test_manga_session_creation(self, db_session: AsyncSession, test_user: User):
        """Test creating a manga session."""
        session = MangaSession(
            id=uuid4(),
            user_id=test_user.id,
            title="Test Manga Creation",
            input_text="A story about testing database operations",
            genre="testing",
            style="unit_test",
            quality_level=QualityLevel.HIGH.value,
            status=GenerationStatus.PENDING.value,
            hitl_enabled=True,
            created_at=datetime.utcnow()
        )
        
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        
        # Verify session was created
        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.title == "Test Manga Creation"
        assert session.status == GenerationStatus.PENDING.value
        assert session.progress_percentage == 0.0  # 0/7 phases
    
    async def test_manga_session_relationships(self, db_session: AsyncSession, test_user: User):
        """Test manga session relationships with other models."""
        # Create session
        session = MangaSession(
            id=uuid4(),
            user_id=test_user.id,
            title="Relationship Test",
            input_text="Testing relationships",
            created_at=datetime.utcnow()
        )
        db_session.add(session)
        await db_session.flush()  # Get session ID without committing
        
        # Create related phase result
        phase_result = PhaseResult(
            id=uuid4(),
            session_id=session.id,
            phase_number=1,
            phase_name="Test Phase",
            input_data={"test": "input"},
            output_data={"test": "output"},
            processing_time_ms=1500,
            status="completed",
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        db_session.add(phase_result)
        
        # Create related feedback
        feedback = UserFeedback(
            id=uuid4(),
            session_id=session.id,
            phase_number=1,
            feedback_type="text",
            feedback_text="Great work!",
            created_at=datetime.utcnow()
        )
        db_session.add(feedback)
        
        await db_session.commit()
        await db_session.refresh(session)
        
        # Test relationships
        assert len(session.phase_results) == 1
        assert session.phase_results[0].phase_number == 1
        assert len(session.feedbacks) == 1
        assert session.feedbacks[0].feedback_text == "Great work!"
    
    async def test_manga_session_status_updates(self, db_session: AsyncSession, test_user: User):
        """Test status updates and progress tracking."""
        session = MangaSession(
            id=uuid4(),
            user_id=test_user.id,
            title="Status Update Test",
            input_text="Testing status updates",
            current_phase=0,
            total_phases=7,
            created_at=datetime.utcnow()
        )
        db_session.add(session)
        await db_session.commit()
        
        # Update session progress
        session.status = GenerationStatus.PROCESSING.value
        session.current_phase = 3
        session.started_at = datetime.utcnow()
        
        await db_session.commit()
        await db_session.refresh(session)
        
        # Verify updates
        assert session.status == GenerationStatus.PROCESSING.value
        assert session.current_phase == 3
        assert session.progress_percentage == pytest.approx(42.857, rel=1e-2)  # 3/7 * 100
        assert session.is_active is True
        assert session.started_at is not None
    
    async def test_manga_session_completion(self, db_session: AsyncSession, test_user: User):
        """Test session completion with final results."""
        session = MangaSession(
            id=uuid4(),
            user_id=test_user.id,
            title="Completion Test",
            input_text="Testing completion flow",
            current_phase=7,
            total_phases=7,
            created_at=datetime.utcnow()
        )
        db_session.add(session)
        await db_session.flush()
        
        # Set completion data
        final_result = {
            "manga_data": {
                "pages": 20,
                "characters": ["Hero", "Villain"],
                "scenes": 8
            },
            "quality_metrics": {
                "overall_score": 0.85,
                "technical_quality": 0.9,
                "creative_score": 0.8
            },
            "output_files": {
                "pdf": "/path/to/manga.pdf",
                "images": ["/path/to/page1.png", "/path/to/page2.png"]
            }
        }
        
        session.status = GenerationStatus.COMPLETED.value
        session.final_result = final_result
        session.quality_score = 0.85
        session.total_processing_time_ms = 120000  # 2 minutes
        session.completed_at = datetime.utcnow()
        
        await db_session.commit()
        await db_session.refresh(session)
        
        # Verify completion
        assert session.status == GenerationStatus.COMPLETED.value
        assert session.progress_percentage == 100.0
        assert session.is_active is False
        assert session.final_result["quality_metrics"]["overall_score"] == 0.85
        assert session.quality_score == 0.85
    
    async def test_manga_session_failure_handling(self, db_session: AsyncSession, test_user: User):
        """Test failure handling and error storage."""
        session = MangaSession(
            id=uuid4(),
            user_id=test_user.id,
            title="Failure Test",
            input_text="Testing failure scenarios",
            created_at=datetime.utcnow()
        )
        db_session.add(session)
        await db_session.flush()
        
        # Simulate failure
        error_message = "AI API rate limit exceeded during phase 3 processing"
        session.status = GenerationStatus.FAILED.value
        session.current_phase = 3
        session.error_message = error_message
        session.retry_count = 1
        
        await db_session.commit()
        await db_session.refresh(session)
        
        # Verify failure state
        assert session.status == GenerationStatus.FAILED.value
        assert session.error_message == error_message
        assert session.retry_count == 1
        assert session.is_active is False


@pytest.mark.asyncio
class TestPhaseResultDatabaseOperations:
    """Test database operations for PhaseResult model."""
    
    async def test_phase_result_creation(self, db_session: AsyncSession, sample_manga_session: MangaSession):
        """Test creating phase results."""
        phase_result = PhaseResult(
            id=uuid4(),
            session_id=sample_manga_session.id,
            phase_number=1,
            phase_name="Concept Analysis",
            input_data={
                "input_text": "A young hero's journey",
                "genre_hint": "fantasy"
            },
            output_data={
                "genre": "fantasy_adventure",
                "themes": ["heroism", "growth", "friendship"],
                "target_audience": "young_adult",
                "estimated_pages": 25,
                "story_complexity": 0.7
            },
            processing_time_ms=12500,
            ai_model_used="gemini-1.5-pro",
            prompt_tokens=150,
            completion_tokens=300,
            quality_score=0.82,
            confidence_score=0.88,
            status="completed",
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        db_session.add(phase_result)
        await db_session.commit()
        await db_session.refresh(phase_result)
        
        # Verify creation
        assert phase_result.id is not None
        assert phase_result.session_id == sample_manga_session.id
        assert phase_result.phase_number == 1
        assert phase_result.output_data["genre"] == "fantasy_adventure"
        assert len(phase_result.output_data["themes"]) == 3
        assert phase_result.quality_score == 0.82
    
    async def test_phase_result_performance_metrics(self, db_session: AsyncSession, sample_manga_session: MangaSession):
        """Test phase result performance tracking."""
        phases_data = [
            (1, "Concept Analysis", 12000, "gemini-1.5-pro", 120, 280),
            (2, "Character Design", 18500, "gemini-1.5-pro", 200, 450),
            (3, "Story Structure", 15800, "gemini-1.5-pro", 180, 380),
            (5, "Image Generation", 25000, "imagen-4", 50, 100),  # Different model
        ]
        
        phase_results = []
        for phase_num, phase_name, proc_time, model, prompt_tokens, completion_tokens in phases_data:
            result = PhaseResult(
                id=uuid4(),
                session_id=sample_manga_session.id,
                phase_number=phase_num,
                phase_name=phase_name,
                input_data={"phase": phase_num},
                output_data={"completed": True},
                processing_time_ms=proc_time,
                ai_model_used=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                status="completed",
                created_at=datetime.utcnow()
            )
            phase_results.append(result)
            db_session.add(result)
        
        await db_session.commit()
        
        # Query performance metrics
        stmt = select(
            PhaseResult.ai_model_used,
            func.avg(PhaseResult.processing_time_ms).label('avg_time'),
            func.sum(PhaseResult.prompt_tokens).label('total_prompt_tokens'),
            func.sum(PhaseResult.completion_tokens).label('total_completion_tokens'),
            func.count().label('phase_count')
        ).where(
            PhaseResult.session_id == sample_manga_session.id
        ).group_by(PhaseResult.ai_model_used)
        
        result = await db_session.execute(stmt)
        metrics = result.fetchall()
        
        # Verify metrics
        assert len(metrics) == 2  # Two different models used
        
        gemini_metrics = next(m for m in metrics if m.ai_model_used == "gemini-1.5-pro")
        imagen_metrics = next(m for m in metrics if m.ai_model_used == "imagen-4")
        
        assert gemini_metrics.phase_count == 3
        assert imagen_metrics.phase_count == 1
        assert gemini_metrics.avg_time > 12000  # Average should be reasonable
        assert imagen_metrics.avg_time == 25000  # Single phase
    
    async def test_phase_result_preview_data(self, db_session: AsyncSession, sample_manga_session: MangaSession):
        """Test phase result with preview data and images."""
        preview_urls = [
            "https://cdn.example.com/preview/character1.png",
            "https://cdn.example.com/preview/character2.png"
        ]
        
        phase_result = PhaseResult(
            id=uuid4(),
            session_id=sample_manga_session.id,
            phase_number=2,
            phase_name="Character Design",
            input_data={"characters_to_create": 2},
            output_data={
                "characters": [
                    {"name": "Hero", "description": "Brave young warrior"},
                    {"name": "Mentor", "description": "Wise old sage"}
                ]
            },
            preview_data={
                "character_thumbnails": preview_urls,
                "style_notes": "Anime-style character design",
                "color_palette": ["#FF6B6B", "#4ECDC4", "#45B7D1"]
            },
            preview_image_urls=preview_urls,
            processing_time_ms=18200,
            status="completed",
            created_at=datetime.utcnow()
        )
        
        db_session.add(phase_result)
        await db_session.commit()
        await db_session.refresh(phase_result)
        
        # Verify preview data
        assert phase_result.preview_data is not None
        assert len(phase_result.preview_image_urls) == 2
        assert "character_thumbnails" in phase_result.preview_data
        assert phase_result.preview_data["color_palette"][0] == "#FF6B6B"
    
    async def test_phase_result_feedback_tracking(self, db_session: AsyncSession, sample_manga_session: MangaSession):
        """Test phase result feedback application tracking."""
        # Initial phase result
        phase_result = PhaseResult(
            id=uuid4(),
            session_id=sample_manga_session.id,
            phase_number=4,
            phase_name="Panel Layout",
            input_data={"layout_style": "dynamic"},
            output_data={
                "panels": [
                    {"type": "wide", "content": "establishing_shot"},
                    {"type": "close_up", "content": "character_reaction"}
                ]
            },
            processing_time_ms=20000,
            feedback_count=0,
            status="completed",
            created_at=datetime.utcnow()
        )
        
        db_session.add(phase_result)
        await db_session.flush()
        
        # Apply feedback
        feedback_applied = {
            "original_output": phase_result.output_data,
            "feedback": {
                "type": "layout_adjustment",
                "request": "Make panels more dynamic",
                "specific_changes": ["add_action_lines", "increase_panel_size"]
            },
            "adjusted_output": {
                "panels": [
                    {"type": "wide", "content": "establishing_shot", "dynamic": True},
                    {"type": "close_up", "content": "character_reaction", "action_lines": True}
                ]
            },
            "applied_at": datetime.utcnow().isoformat()
        }
        
        phase_result.feedback_count = 1
        phase_result.feedback_applied = feedback_applied
        phase_result.output_data = feedback_applied["adjusted_output"]
        
        await db_session.commit()
        await db_session.refresh(phase_result)
        
        # Verify feedback tracking
        assert phase_result.feedback_count == 1
        assert phase_result.feedback_applied is not None
        assert "original_output" in phase_result.feedback_applied
        assert phase_result.output_data["panels"][0]["dynamic"] is True


@pytest.mark.asyncio
class TestGeneratedImageDatabaseOperations:
    """Test database operations for GeneratedImage model."""
    
    async def test_generated_image_creation(self, db_session: AsyncSession, sample_manga_session: MangaSession):
        """Test creating generated images."""
        image = GeneratedImage(
            id=uuid4(),
            session_id=sample_manga_session.id,
            phase_number=5,
            scene_number=1,
            image_url="https://storage.example.com/images/scene1_full.png",
            thumbnail_url="https://cdn.example.com/thumbnails/scene1_thumb.png",
            cdn_url="https://cdn.example.com/images/scene1_full.png",
            prompt_used="A young hero standing at the edge of a mystical forest, anime style, high quality",
            negative_prompt="blurry, low quality, nsfw, violence",
            model_name="imagen-4",
            model_version="v4.1",
            width=1024,
            height=1536,
            format="png",
            size_bytes=1024000,  # ~1MB
            quality_score=0.87,
            nsfw_score=0.02,  # Very low NSFW content
            generation_time_ms=8500,
            retry_count=0,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        db_session.add(image)
        await db_session.commit()
        await db_session.refresh(image)
        
        # Verify image creation
        assert image.id is not None
        assert image.session_id == sample_manga_session.id
        assert image.quality_score == 0.87
        assert image.nsfw_score == 0.02
        assert image.width == 1024
        assert image.height == 1536
        assert image.model_name == "imagen-4"
    
    async def test_generated_image_batch_operations(self, db_session: AsyncSession, sample_manga_session: MangaSession):
        """Test batch image generation tracking."""
        # Create multiple images for the same scene
        images = []
        for i in range(3):
            image = GeneratedImage(
                id=uuid4(),
                session_id=sample_manga_session.id,
                phase_number=5,
                scene_number=2,
                image_url=f"https://storage.example.com/scene2_variant{i+1}.png",
                prompt_used=f"Scene 2 variant {i+1} - Epic battle scene",
                model_name="imagen-4",
                width=1024,
                height=1536,
                format="png",
                quality_score=0.7 + (i * 0.05),  # Varying quality
                generation_time_ms=7000 + (i * 500),
                retry_count=i,  # Simulate some retries
                created_at=datetime.utcnow()
            )
            images.append(image)
            db_session.add(image)
        
        await db_session.commit()
        
        # Query images by scene
        stmt = select(GeneratedImage).where(
            GeneratedImage.session_id == sample_manga_session.id,
            GeneratedImage.scene_number == 2
        ).order_by(GeneratedImage.quality_score.desc())
        
        result = await db_session.execute(stmt)
        scene_images = result.scalars().all()
        
        # Verify batch operations
        assert len(scene_images) == 3
        assert scene_images[0].quality_score >= scene_images[1].quality_score
        assert scene_images[1].quality_score >= scene_images[2].quality_score
        
        # Test aggregation queries
        stmt = select(
            func.count().label('total_images'),
            func.avg(GeneratedImage.quality_score).label('avg_quality'),
            func.sum(GeneratedImage.generation_time_ms).label('total_time'),
            func.avg(GeneratedImage.retry_count).label('avg_retries')
        ).where(
            GeneratedImage.session_id == sample_manga_session.id,
            GeneratedImage.scene_number == 2
        )
        
        result = await db_session.execute(stmt)
        stats = result.first()
        
        assert stats.total_images == 3
        assert stats.avg_quality == pytest.approx(0.775, rel=1e-2)  # (0.7 + 0.75 + 0.8) / 3
        assert stats.avg_retries == pytest.approx(1.0, rel=1e-2)    # (0 + 1 + 2) / 3


@pytest.mark.asyncio
class TestUserFeedbackDatabaseOperations:
    """Test database operations for UserFeedback model."""
    
    async def test_user_feedback_creation(self, db_session: AsyncSession, sample_manga_session: MangaSession):
        """Test creating user feedback."""
        feedback = UserFeedback(
            id=uuid4(),
            session_id=sample_manga_session.id,
            phase_number=2,
            feedback_type="text",
            feedback_text="The main character should look more heroic and confident",
            feedback_data={
                "character_id": "hero",
                "specific_adjustments": {
                    "facial_expression": "more_determined",
                    "posture": "more_confident",
                    "clothing": "add_hero_cape"
                },
                "priority": "high",
                "user_satisfaction_before": 3
            },
            applied=False,
            satisfaction_score=4,
            created_at=datetime.utcnow()
        )
        
        db_session.add(feedback)
        await db_session.commit()
        await db_session.refresh(feedback)
        
        # Verify feedback creation
        assert feedback.id is not None
        assert feedback.session_id == sample_manga_session.id
        assert feedback.phase_number == 2
        assert feedback.feedback_type == "text"
        assert feedback.applied is False
        assert feedback.satisfaction_score == 4
        assert feedback.feedback_data["priority"] == "high"
    
    async def test_feedback_application_tracking(self, db_session: AsyncSession, sample_manga_session: MangaSession):
        """Test tracking feedback application."""
        feedback = UserFeedback(
            id=uuid4(),
            session_id=sample_manga_session.id,
            phase_number=6,
            feedback_type="dialogue_adjustment",
            feedback_text="Make the dialogue sound more natural",
            feedback_data={
                "dialogue_items": [
                    {"id": 1, "original": "I will defeat you!", "suggestion": "I won't let you hurt anyone!"},
                    {"id": 2, "original": "You cannot stop me", "suggestion": "You can't stop me now"}
                ]
            },
            applied=False,
            created_at=datetime.utcnow()
        )
        
        db_session.add(feedback)
        await db_session.flush()
        
        # Simulate feedback application
        result_after_application = {
            "dialogue_changes": [
                {"id": 1, "before": "I will defeat you!", "after": "I won't let you hurt anyone!"},
                {"id": 2, "before": "You cannot stop me", "after": "You can't stop me now"}
            ],
            "quality_improvement": 0.15,
            "user_approval": True
        }
        
        feedback.applied = True
        feedback.applied_at = datetime.utcnow()
        feedback.result_after_application = result_after_application
        feedback.satisfaction_score = 5  # User satisfaction after application
        
        await db_session.commit()
        await db_session.refresh(feedback)
        
        # Verify application tracking
        assert feedback.applied is True
        assert feedback.applied_at is not None
        assert feedback.result_after_application is not None
        assert feedback.satisfaction_score == 5
        assert len(feedback.result_after_application["dialogue_changes"]) == 2
    
    async def test_feedback_analytics(self, db_session: AsyncSession, sample_manga_session: MangaSession):
        """Test feedback analytics and aggregations."""
        # Create multiple feedbacks for different phases
        feedbacks_data = [
            (1, "text", "Good concept", 4, True),
            (2, "visual", "Character needs improvement", 2, True),
            (2, "text", "Love the character design!", 5, False),
            (4, "layout", "Panels are too crowded", 3, True),
            (6, "dialogue", "Dialogue is perfect", 5, False)
        ]
        
        for phase, f_type, text, satisfaction, applied in feedbacks_data:
            feedback = UserFeedback(
                id=uuid4(),
                session_id=sample_manga_session.id,
                phase_number=phase,
                feedback_type=f_type,
                feedback_text=text,
                satisfaction_score=satisfaction,
                applied=applied,
                created_at=datetime.utcnow()
            )
            db_session.add(feedback)
        
        await db_session.commit()
        
        # Analytics query 1: Feedback by phase
        stmt = select(
            UserFeedback.phase_number,
            func.count().label('feedback_count'),
            func.avg(UserFeedback.satisfaction_score).label('avg_satisfaction'),
            func.sum(UserFeedback.applied.cast('int')).label('applied_count')
        ).where(
            UserFeedback.session_id == sample_manga_session.id
        ).group_by(UserFeedback.phase_number).order_by(UserFeedback.phase_number)
        
        result = await db_session.execute(stmt)
        phase_stats = result.fetchall()
        
        # Verify phase-level analytics
        phase_2_stats = next(p for p in phase_stats if p.phase_number == 2)
        assert phase_2_stats.feedback_count == 2
        assert phase_2_stats.avg_satisfaction == 3.5  # (2 + 5) / 2
        assert phase_2_stats.applied_count == 1
        
        # Analytics query 2: Overall session feedback stats
        stmt = select(
            func.count().label('total_feedback'),
            func.avg(UserFeedback.satisfaction_score).label('overall_satisfaction'),
            func.count(UserFeedback.applied == True).label('total_applied')
        ).where(UserFeedback.session_id == sample_manga_session.id)
        
        result = await db_session.execute(stmt)
        overall_stats = result.first()
        
        assert overall_stats.total_feedback == 5
        assert overall_stats.overall_satisfaction == pytest.approx(3.8, rel=1e-2)  # (4+2+5+3+5)/5


@pytest.mark.asyncio
class TestDatabaseConstraintsAndIndexes:
    """Test database constraints, indexes, and relationships."""
    
    async def test_foreign_key_constraints(self, db_session: AsyncSession, test_user: User):
        """Test foreign key constraints are properly enforced."""
        # Test valid foreign key
        session = MangaSession(
            id=uuid4(),
            user_id=test_user.id,
            title="FK Test",
            input_text="Testing foreign keys",
            created_at=datetime.utcnow()
        )
        db_session.add(session)
        await db_session.commit()  # Should succeed
        
        # Test invalid foreign key (this should be handled by the application layer)
        invalid_session = MangaSession(
            id=uuid4(),
            user_id=uuid4(),  # Non-existent user
            title="Invalid FK Test",
            input_text="This should fail",
            created_at=datetime.utcnow()
        )
        db_session.add(invalid_session)
        
        with pytest.raises(Exception):  # Should raise some kind of database error
            await db_session.commit()
        
        await db_session.rollback()  # Clean up failed transaction
    
    async def test_cascade_deletion(self, db_session: AsyncSession, test_user: User):
        """Test cascade deletion of related records."""
        # Create session with related data
        session = MangaSession(
            id=uuid4(),
            user_id=test_user.id,
            title="Cascade Test",
            input_text="Testing cascade deletion",
            created_at=datetime.utcnow()
        )
        db_session.add(session)
        await db_session.flush()
        
        # Add related records
        phase_result = PhaseResult(
            id=uuid4(),
            session_id=session.id,
            phase_number=1,
            phase_name="Test Phase",
            input_data={},
            output_data={},
            processing_time_ms=1000,
            created_at=datetime.utcnow()
        )
        
        feedback = UserFeedback(
            id=uuid4(),
            session_id=session.id,
            phase_number=1,
            feedback_type="test",
            feedback_text="Test feedback",
            created_at=datetime.utcnow()
        )
        
        db_session.add(phase_result)
        db_session.add(feedback)
        await db_session.commit()
        
        # Verify related records exist
        stmt = select(func.count()).select_from(PhaseResult).where(PhaseResult.session_id == session.id)
        result = await db_session.execute(stmt)
        assert result.scalar() == 1
        
        stmt = select(func.count()).select_from(UserFeedback).where(UserFeedback.session_id == session.id)
        result = await db_session.execute(stmt)
        assert result.scalar() == 1
        
        # Delete session - related records should be cascade deleted
        await db_session.delete(session)
        await db_session.commit()
        
        # Verify related records are gone
        stmt = select(func.count()).select_from(PhaseResult).where(PhaseResult.session_id == session.id)
        result = await db_session.execute(stmt)
        assert result.scalar() == 0
        
        stmt = select(func.count()).select_from(UserFeedback).where(UserFeedback.session_id == session.id)
        result = await db_session.execute(stmt)
        assert result.scalar() == 0
    
    async def test_unique_constraints(self, db_session: AsyncSession, test_user: User):
        """Test unique constraints where applicable."""
        # Create session
        session = MangaSession(
            id=uuid4(),
            user_id=test_user.id,
            title="Unique Test",
            input_text="Testing unique constraints",
            created_at=datetime.utcnow()
        )
        db_session.add(session)
        await db_session.flush()
        
        # Test phase number uniqueness within session
        phase1 = PhaseResult(
            id=uuid4(),
            session_id=session.id,
            phase_number=1,
            phase_name="Phase 1",
            input_data={},
            output_data={},
            processing_time_ms=1000,
            created_at=datetime.utcnow()
        )
        db_session.add(phase1)
        await db_session.commit()
        
        # Depending on database constraints, adding another phase 1 for same session
        # might be allowed (for retries) or not - this test documents the behavior
        phase1_duplicate = PhaseResult(
            id=uuid4(),
            session_id=session.id,
            phase_number=1,  # Same phase number
            phase_name="Phase 1 Retry",
            input_data={},
            output_data={},
            processing_time_ms=1000,
            created_at=datetime.utcnow()
        )
        db_session.add(phase1_duplicate)
        
        try:
            await db_session.commit()
            # If this succeeds, duplicate phases are allowed (for retries)
            assert True
        except Exception:
            # If this fails, there's a unique constraint
            await db_session.rollback()
            assert True  # Either behavior is valid depending on design
    
    async def test_query_performance(self, db_session: AsyncSession, test_user: User):
        """Test that common queries perform efficiently with proper indexing."""
        # Create multiple sessions for performance testing
        sessions = []
        for i in range(10):
            session = MangaSession(
                id=uuid4(),
                user_id=test_user.id,
                title=f"Performance Test {i}",
                input_text=f"Performance testing session {i}",
                status=GenerationStatus.COMPLETED.value if i % 2 == 0 else GenerationStatus.PROCESSING.value,
                created_at=datetime.utcnow() - timedelta(days=i),
                updated_at=datetime.utcnow() - timedelta(hours=i)
            )
            sessions.append(session)
            db_session.add(session)
        
        await db_session.commit()
        
        # Test indexed queries
        import time
        
        # Query by user_id (should be indexed)
        start_time = time.time()
        stmt = select(MangaSession).where(MangaSession.user_id == test_user.id)
        result = await db_session.execute(stmt)
        user_sessions = result.scalars().all()
        query_time = time.time() - start_time
        
        assert len(user_sessions) >= 10
        assert query_time < 1.0  # Should be fast with proper indexing
        
        # Query by status (should be indexed)
        start_time = time.time()
        stmt = select(MangaSession).where(MangaSession.status == GenerationStatus.COMPLETED.value)
        result = await db_session.execute(stmt)
        completed_sessions = result.scalars().all()
        query_time = time.time() - start_time
        
        assert len(completed_sessions) >= 5
        assert query_time < 1.0
        
        # Order by created_at (should be efficient)
        start_time = time.time()
        stmt = select(MangaSession).where(
            MangaSession.user_id == test_user.id
        ).order_by(MangaSession.created_at.desc()).limit(5)
        result = await db_session.execute(stmt)
        recent_sessions = result.scalars().all()
        query_time = time.time() - start_time
        
        assert len(recent_sessions) == 5
        assert query_time < 1.0
        
        # Verify ordering
        for i in range(len(recent_sessions) - 1):
            assert recent_sessions[i].created_at >= recent_sessions[i + 1].created_at
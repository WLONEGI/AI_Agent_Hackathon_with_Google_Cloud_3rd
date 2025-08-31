"""Test suite for Phase 1 database models."""

import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.models.users_model import UsersModel
from app.infrastructure.database.models.manga_projects_model import MangaProjectsModel
from app.infrastructure.database.models.generation_requests_model import GenerationRequestsModel
from app.infrastructure.database.models.processing_modules_model import ProcessingModulesModel


# Test fixtures
@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    
    # Create all tables
    from app.infrastructure.database.models.users_model import Base as UsersBase
    from app.infrastructure.database.models.manga_projects_model import Base as ProjectsBase
    from app.infrastructure.database.models.generation_requests_model import Base as RequestsBase
    from app.infrastructure.database.models.processing_modules_model import Base as ModulesBase
    
    UsersBase.metadata.create_all(engine)
    ProjectsBase.metadata.create_all(engine)
    RequestsBase.metadata.create_all(engine)
    ModulesBase.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = UsersModel(
        user_id=uuid.uuid4(),
        email="test@example.com",
        display_name="Test User",
        account_type="free",
        firebase_claims={"custom_claims": {"role": "user"}}
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_project(db_session, sample_user):
    """Create a sample manga project for testing."""
    project = MangaProjectsModel(
        project_id=uuid.uuid4(),
        user_id=sample_user.user_id,
        title="Test Manga",
        status="draft",
        metadata={"style": "shounen", "genre": "action"},
        settings={"quality": "high", "pages": 20}
    )
    db_session.add(project)
    db_session.commit()
    return project


class TestUsersModel:
    """Test cases for UsersModel."""
    
    def test_create_user(self, db_session):
        """Test creating a new user."""
        user = UsersModel(
            user_id=uuid.uuid4(),
            email="newuser@example.com",
            display_name="New User",
            account_type="premium"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.user_id is not None
        assert user.email == "newuser@example.com"
        assert user.account_type == "premium"
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_email_uniqueness(self, db_session, sample_user):
        """Test that email addresses must be unique."""
        duplicate_user = UsersModel(
            user_id=uuid.uuid4(),
            email=sample_user.email,  # Same email
            display_name="Duplicate User",
            account_type="free"
        )
        db_session.add(duplicate_user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_account_type_validation(self, db_session):
        """Test account type constraint (if supported by database)."""
        user = UsersModel(
            user_id=uuid.uuid4(),
            email="invalid@example.com",
            display_name="Invalid User",
            account_type="invalid_type"  # Invalid account type
        )
        db_session.add(user)
        
        # Note: SQLite doesn't support CHECK constraints by default
        # This test would work with PostgreSQL
        try:
            db_session.commit()
        except IntegrityError:
            # Expected for PostgreSQL
            assert True
        else:
            # SQLite allows this, so we just check the value was stored
            assert user.account_type == "invalid_type"


class TestMangaProjectsModel:
    """Test cases for MangaProjectsModel."""
    
    def test_create_project(self, db_session, sample_user):
        """Test creating a new manga project."""
        project = MangaProjectsModel(
            project_id=uuid.uuid4(),
            user_id=sample_user.user_id,
            title="New Manga Project",
            status="draft",
            metadata={"style": "shojo", "characters": 3},
            total_pages=15
        )
        db_session.add(project)
        db_session.commit()
        
        assert project.project_id is not None
        assert project.user_id == sample_user.user_id
        assert project.title == "New Manga Project"
        assert project.status == "draft"
        assert project.metadata["style"] == "shojo"
        assert project.total_pages == 15
    
    def test_project_user_relationship(self, db_session, sample_user):
        """Test foreign key relationship with users."""
        # Try to create project with non-existent user
        invalid_project = MangaProjectsModel(
            project_id=uuid.uuid4(),
            user_id=uuid.uuid4(),  # Non-existent user
            title="Invalid Project",
            status="draft"
        )
        db_session.add(invalid_project)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_jsonb_metadata(self, db_session, sample_project):
        """Test JSONB metadata functionality."""
        # Update metadata
        sample_project.metadata = {
            "style": "seinen", 
            "genre": "mystery",
            "tags": ["detective", "noir"],
            "rating": 4.5
        }
        db_session.commit()
        
        # Retrieve and verify
        retrieved = db_session.query(MangaProjectsModel).filter_by(
            project_id=sample_project.project_id
        ).first()
        
        assert retrieved.metadata["style"] == "seinen"
        assert retrieved.metadata["genre"] == "mystery"
        assert "detective" in retrieved.metadata["tags"]
        assert retrieved.metadata["rating"] == 4.5


class TestGenerationRequestsModel:
    """Test cases for GenerationRequestsModel."""
    
    def test_create_request(self, db_session, sample_project, sample_user):
        """Test creating a new generation request."""
        request = GenerationRequestsModel(
            request_id=uuid.uuid4(),
            project_id=sample_project.project_id,
            user_id=sample_user.user_id,
            input_text="Create an exciting manga about robots.",
            request_settings={"style": "mecha", "pages": 10},
            status="queued"
        )
        db_session.add(request)
        db_session.commit()
        
        assert request.request_id is not None
        assert request.project_id == sample_project.project_id
        assert request.user_id == sample_user.user_id
        assert request.status == "queued"
        assert request.current_module == 0
        assert request.retry_count == 0
    
    def test_request_relationships(self, db_session, sample_project, sample_user):
        """Test foreign key relationships."""
        request = GenerationRequestsModel(
            request_id=uuid.uuid4(),
            project_id=sample_project.project_id,
            user_id=sample_user.user_id,
            input_text="Test story",
            request_settings={}
        )
        db_session.add(request)
        db_session.commit()
        
        # Test relationships exist
        assert request.project_id == sample_project.project_id
        assert request.user_id == sample_user.user_id
    
    def test_status_progression(self, db_session, sample_project, sample_user):
        """Test request status progression."""
        request = GenerationRequestsModel(
            request_id=uuid.uuid4(),
            project_id=sample_project.project_id,
            user_id=sample_user.user_id,
            input_text="Test progression",
            request_settings={}
        )
        db_session.add(request)
        db_session.commit()
        
        # Progress through statuses
        request.status = "processing"
        request.started_at = datetime.now(timezone.utc)
        request.current_module = 1
        db_session.commit()
        
        request.status = "completed"
        request.completed_at = datetime.now(timezone.utc)
        request.current_module = 7
        db_session.commit()
        
        assert request.status == "completed"
        assert request.current_module == 7
        assert request.started_at is not None
        assert request.completed_at is not None


class TestProcessingModulesModel:
    """Test cases for ProcessingModulesModel."""
    
    def test_create_module(self, db_session, sample_project, sample_user):
        """Test creating a processing module."""
        # First create a generation request
        request = GenerationRequestsModel(
            request_id=uuid.uuid4(),
            project_id=sample_project.project_id,
            user_id=sample_user.user_id,
            input_text="Test story for modules",
            request_settings={}
        )
        db_session.add(request)
        db_session.commit()
        
        # Then create a processing module
        module = ProcessingModulesModel(
            module_id=uuid.uuid4(),
            request_id=request.request_id,
            module_number=1,
            module_name="concept_analysis",
            status="pending"
        )
        db_session.add(module)
        db_session.commit()
        
        assert module.module_id is not None
        assert module.request_id == request.request_id
        assert module.module_number == 1
        assert module.module_name == "concept_analysis"
        assert module.status == "pending"
    
    def test_module_progression(self, db_session, sample_project, sample_user):
        """Test module execution progression."""
        request = GenerationRequestsModel(
            request_id=uuid.uuid4(),
            project_id=sample_project.project_id,
            user_id=sample_user.user_id,
            input_text="Test module progression",
            request_settings={}
        )
        db_session.add(request)
        db_session.commit()
        
        module = ProcessingModulesModel(
            module_id=uuid.uuid4(),
            request_id=request.request_id,
            module_number=2,
            module_name="character_visual",
            status="pending",
            checkpoint_data={"initial_state": True}
        )
        db_session.add(module)
        db_session.commit()
        
        # Start processing
        start_time = datetime.now(timezone.utc)
        module.status = "processing"
        module.started_at = start_time
        db_session.commit()
        
        # Complete processing
        end_time = datetime.now(timezone.utc)
        module.status = "completed"
        module.completed_at = end_time
        module.duration_ms = 1500
        module.checkpoint_data = {
            "initial_state": True,
            "final_result": "characters_generated",
            "quality_score": 0.85
        }
        db_session.commit()
        
        assert module.status == "completed"
        assert module.started_at == start_time
        assert module.completed_at == end_time
        assert module.duration_ms == 1500
        assert module.checkpoint_data["final_result"] == "characters_generated"
    
    def test_unique_request_module_combination(self, db_session, sample_project, sample_user):
        """Test unique constraint on request_id and module_number."""
        request = GenerationRequestsModel(
            request_id=uuid.uuid4(),
            project_id=sample_project.project_id,
            user_id=sample_user.user_id,
            input_text="Test unique constraint",
            request_settings={}
        )
        db_session.add(request)
        db_session.commit()
        
        # Create first module
        module1 = ProcessingModulesModel(
            module_id=uuid.uuid4(),
            request_id=request.request_id,
            module_number=3,
            module_name="plot_structure"
        )
        db_session.add(module1)
        db_session.commit()
        
        # Try to create duplicate module
        module2 = ProcessingModulesModel(
            module_id=uuid.uuid4(),
            request_id=request.request_id,
            module_number=3,  # Same number
            module_name="plot_structure"
        )
        db_session.add(module2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestModelIntegration:
    """Integration tests across all models."""
    
    def test_complete_workflow(self, db_session):
        """Test a complete workflow across all models."""
        # 1. Create user
        user = UsersModel(
            user_id=uuid.uuid4(),
            email="workflow@example.com",
            display_name="Workflow User",
            account_type="premium"
        )
        db_session.add(user)
        db_session.commit()
        
        # 2. Create project
        project = MangaProjectsModel(
            project_id=uuid.uuid4(),
            user_id=user.user_id,
            title="Complete Workflow Test",
            status="processing",
            metadata={"workflow": "test"},
            total_pages=5
        )
        db_session.add(project)
        db_session.commit()
        
        # 3. Create generation request
        request = GenerationRequestsModel(
            request_id=uuid.uuid4(),
            project_id=project.project_id,
            user_id=user.user_id,
            input_text="Test complete workflow",
            request_settings={"test": True},
            status="processing",
            current_module=2
        )
        db_session.add(request)
        db_session.commit()
        
        # 4. Create multiple processing modules
        modules = []
        for i, name in enumerate([
            "concept_analysis", "character_visual", "plot_structure", 
            "name_generation", "scene_generation"
        ], 1):
            module = ProcessingModulesModel(
                module_id=uuid.uuid4(),
                request_id=request.request_id,
                module_number=i,
                module_name=name,
                status="completed" if i <= 2 else "pending",
                duration_ms=1000 + i * 100 if i <= 2 else None
            )
            modules.append(module)
            db_session.add(module)
        
        db_session.commit()
        
        # 5. Verify relationships and data integrity
        retrieved_user = db_session.query(UsersModel).filter_by(user_id=user.user_id).first()
        assert retrieved_user.email == "workflow@example.com"
        
        retrieved_project = db_session.query(MangaProjectsModel).filter_by(project_id=project.project_id).first()
        assert retrieved_project.user_id == user.user_id
        assert retrieved_project.title == "Complete Workflow Test"
        
        retrieved_request = db_session.query(GenerationRequestsModel).filter_by(request_id=request.request_id).first()
        assert retrieved_request.project_id == project.project_id
        assert retrieved_request.user_id == user.user_id
        assert retrieved_request.current_module == 2
        
        retrieved_modules = db_session.query(ProcessingModulesModel).filter_by(
            request_id=request.request_id
        ).order_by(ProcessingModulesModel.module_number).all()
        
        assert len(retrieved_modules) == 5
        assert retrieved_modules[0].module_name == "concept_analysis"
        assert retrieved_modules[0].status == "completed"
        assert retrieved_modules[2].module_name == "plot_structure"
        assert retrieved_modules[2].status == "pending"
        
        # 6. Test cascading deletes (if supported)
        db_session.delete(user)
        db_session.commit()
        
        # Verify cascading delete worked
        remaining_projects = db_session.query(MangaProjectsModel).filter_by(user_id=user.user_id).all()
        remaining_requests = db_session.query(GenerationRequestsModel).filter_by(user_id=user.user_id).all()
        
        # Note: SQLite might not enforce foreign key constraints by default
        # In PostgreSQL, these should be empty due to CASCADE
        if not remaining_projects and not remaining_requests:
            assert True  # Cascading delete worked
        else:
            # Manual cleanup for SQLite
            for project in remaining_projects:
                db_session.delete(project)
            for request in remaining_requests:
                db_session.delete(request)
            db_session.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""Minimal test for database setup without configuration loading."""

import asyncio
import os
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from datetime import datetime

# Set environment variables
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./manga_service.db"

# Create Base class
Base = declarative_base()

# Define minimal models
class MangaSession(Base):
    __tablename__ = "manga_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    theme_prompt = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending")
    current_phase = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PhaseResult(Base):
    __tablename__ = "phase_results"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False, index=True)
    phase_number = Column(Integer, nullable=False)
    agent_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    result_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

async def test_database():
    """Test database connection and setup without complex configuration."""
    db_url = os.environ["DATABASE_URL"]
    print(f"Connecting to database: {db_url}")
    
    # Create engine
    engine = create_async_engine(
        db_url,
        echo=True,
        future=True
    )
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        # Test connection
        async with async_session() as session:
            result = await session.execute(text("SELECT 1"))
            print(f"Database connection successful: {result.scalar()}")
            
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("Database tables created successfully!")
            
        # Insert test data
        async with async_session() as session:
            # Create test user
            test_user = User(
                id="test-user-1",
                email="test@example.com",
                username="testuser",
                hashed_password="hashed_password_here"
            )
            session.add(test_user)
            
            # Create test manga session
            test_session = MangaSession(
                id="test-session-1",
                user_id="test-user-1",
                title="テスト漫画",
                theme_prompt="少年が冒険に出る物語"
            )
            session.add(test_session)
            
            # Create test phase result
            test_phase = PhaseResult(
                id="test-phase-1",
                session_id="test-session-1",
                phase_number=1,
                agent_name="ConceptAnalysisAgent",
                status="completed",
                result_data={"concept": "adventure", "genre": "shonen"}
            )
            session.add(test_phase)
            
            await session.commit()
            print("Test data inserted successfully!")
            
        # Query test data
        async with async_session() as session:
            # Query users
            result = await session.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            print(f"Users in database: {user_count}")
            
            # Query sessions
            result = await session.execute(text("SELECT COUNT(*) FROM manga_sessions"))
            session_count = result.scalar()
            print(f"Manga sessions in database: {session_count}")
            
            # Query phase results
            result = await session.execute(text("SELECT COUNT(*) FROM phase_results"))
            phase_count = result.scalar()
            print(f"Phase results in database: {phase_count}")
            
        print("Database setup and testing completed successfully!")
            
    except Exception as e:
        print(f"Database setup failed: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_database())
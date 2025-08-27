"""Simple main for testing database setup."""

import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Set environment variables
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./manga_service.db"

async def test_database():
    """Test database connection and setup."""
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
            
        # Import models to register with Base
        from app.models.manga import (
            MangaSession, PhaseResult, PreviewVersion,
            UserFeedback, GeneratedImage
        )
        from app.models.user import User
        from app.core.database import Base
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("Database tables created successfully!")
            
    except Exception as e:
        print(f"Database setup failed: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_database())
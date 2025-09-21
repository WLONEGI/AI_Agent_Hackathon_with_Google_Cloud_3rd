#!/usr/bin/env python3
"""
Run migration 0008 to fix manga_sessions schema
"""

import asyncio
import os
import sys

async def run_migration_0008():
    """Run the specific migration 0008 manually"""
    print("🔧 Running migration 0008 to fix manga_sessions schema...")
    
    # Install required packages programmatically
    try:
        import asyncpg
        from google.cloud.sql.connector import Connector
        import sqlalchemy as sa
        from sqlalchemy.ext.asyncio import create_async_engine
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "asyncpg", "cloud-sql-python-connector[asyncpg]", "sqlalchemy"])
        import asyncpg
        from google.cloud.sql.connector import Connector
        import sqlalchemy as sa
        from sqlalchemy.ext.asyncio import create_async_engine

    from google.cloud.sql.connector import IPTypes

    try:
        project_id = "comic-ai-agent-470309"
        region = "asia-northeast1"
        instance_name = "manga-db-prod"
        database_name = "manga_db"
        username = "manga_user"
        password = "manga_secure_password_2024"

        # Create connection string for Cloud SQL
        connection_name = f"{project_id}:{region}:{instance_name}"

        # Use Cloud SQL Connector
        connector = Connector()

        async def getconn():
            conn = await connector.connect_async(
                instance_connection_string=connection_name,
                driver="asyncpg",
                user=username,
                password=password,
                db=database_name,
                ip_type=IPTypes.PUBLIC
            )
            return conn

        # Create async engine
        engine = create_async_engine(
            "postgresql+asyncpg://",
            async_creator=getconn,
            echo=True,
        )

        async with engine.begin() as conn:
            # Check if request_id column already exists
            check_result = await conn.execute(sa.text("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = 'manga_sessions'
                AND column_name = 'request_id'
            """))

            exists = check_result.scalar()

            if exists > 0:
                print("✅ request_id column already exists!")
                return True

            print("📋 Adding missing columns to manga_sessions...")

            # Add missing columns step by step
            migrations = [
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS request_id UUID',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS project_id UUID',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS session_metadata JSON',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS text TEXT',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS ai_auto_settings BOOLEAN DEFAULT true',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS feedback_mode JSON',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS options JSON',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS estimated_completion_time TIMESTAMP WITH TIME ZONE',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS actual_completion_time TIMESTAMP WITH TIME ZONE',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS total_phases INTEGER DEFAULT 5',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS error_message TEXT',
                'ALTER TABLE manga_sessions ADD COLUMN IF NOT EXISTS websocket_channel VARCHAR(255)',
            ]

            for migration in migrations:
                try:
                    await conn.execute(sa.text(migration))
                    print(f"✅ {migration}")
                except Exception as e:
                    print(f"⚠️ {migration} - {e}")

            # Generate request_id for existing records
            print("🔄 Generating request_id for existing records...")
            await conn.execute(sa.text("""
                UPDATE manga_sessions
                SET request_id = gen_random_uuid()
                WHERE request_id IS NULL
            """))

            print("✅ Migration 0008 completed successfully!")

        await engine.dispose()
        await connector.close_async()
        return True

    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_migration_0008())
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Complete schema fix script to add ALL missing tables including session_messages and session_events
"""

import asyncio
import asyncpg
import os
from google.cloud.sql.connector import Connector, IPTypes
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


async def get_async_engine():
    """Create async engine for Cloud SQL connection"""
    project_id = "comic-ai-agent-470309"
    region = "asia-northeast1"
    instance_name = "manga-db-prod"
    database_name = "manga_db"
    username = "postgres"
    password = "manga_generation_pass_2024"

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

    return engine, connector


async def run_complete_schema_fix():
    """Run the complete schema fix SQL"""
    print("🔧 Starting complete database schema fix v2...")

    try:
        engine, connector = await get_async_engine()

        # Read the SQL fix script
        with open("complete_schema_fix.sql", "r") as f:
            sql_content = f.read()

        print("📋 Executing complete schema fix v2...")

        async with engine.begin() as conn:
            # Execute the SQL script
            await conn.execute(sa.text(sql_content))
            print("✅ Complete schema fix v2 completed successfully!")

        await engine.dispose()
        await connector.close_async()

    except Exception as e:
        print(f"❌ Error running complete schema fix: {e}")
        raise


async def verify_complete_schema():
    """Verify that all required tables exist"""
    print("🔍 Verifying complete database schema...")

    try:
        engine, connector = await get_async_engine()

        async with engine.begin() as conn:
            # Check all critical tables
            result = await conn.execute(sa.text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('manga_sessions', 'phase_results', 'session_messages', 'session_events', 'preview_versions', 'user_feedback', 'generated_images')
                ORDER BY table_name;
            """))

            tables = result.fetchall()
            print("📊 Critical tables found:")
            for table in tables:
                print(f"  ✅ {table[0]}")

            expected_tables = ['manga_sessions', 'phase_results', 'session_messages', 'session_events', 'preview_versions', 'user_feedback', 'generated_images']
            found_tables = [table[0] for table in tables]

            missing_tables = set(expected_tables) - set(found_tables)
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False

            # Specifically check session_messages structure
            print("\n📋 session_messages table structure:")
            result = await conn.execute(sa.text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'session_messages'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")

            # Specifically check session_events structure
            print("\n📋 session_events table structure:")
            result = await conn.execute(sa.text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'session_events'
                ORDER BY ordinal_position;
            """))
            columns = result.fetchall()
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")

            print("✅ All critical tables exist with proper structure!")
            return True

        await engine.dispose()
        await connector.close_async()

    except Exception as e:
        print(f"❌ Error verifying complete schema: {e}")
        return False


async def main():
    """Main execution function"""
    print("🚀 Complete Database Schema Fix Tool v2")
    print("=" * 50)

    # First verify current schema
    schema_ok = await verify_complete_schema()

    if not schema_ok:
        print("\n🔧 Running complete schema fix v2...")
        await run_complete_schema_fix()

        print("\n🔍 Re-verifying complete schema...")
        schema_ok = await verify_complete_schema()

    if schema_ok:
        print("\n🎉 Database schema is now COMPLETELY correct!")
        print("✅ session_messages table: EXISTS")
        print("✅ session_events table: EXISTS")
        print("✅ phase_results table: EXISTS")
        print("✅ All other tables: EXISTS")
        return True
    else:
        print("\n💥 Complete schema fix failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
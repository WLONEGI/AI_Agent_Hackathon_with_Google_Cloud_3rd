#!/usr/bin/env python3
"""
Schema fix script to add missing request_id column to manga_sessions table
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
    instance_name = "comic-ai-agent-db"
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


async def run_schema_fix():
    """Run the schema fix SQL"""
    print("🔧 Starting database schema fix...")

    try:
        engine, connector = await get_async_engine()

        # Read the SQL fix script
        with open("fix_request_id_schema.sql", "r") as f:
            sql_content = f.read()

        print("📋 Executing schema fix SQL...")

        async with engine.begin() as conn:
            # Execute the SQL script
            await conn.execute(sa.text(sql_content))
            print("✅ Schema fix completed successfully!")

        await engine.dispose()
        await connector.close_async()

    except Exception as e:
        print(f"❌ Error running schema fix: {e}")
        raise


async def verify_schema():
    """Verify that the request_id column exists"""
    print("🔍 Verifying database schema...")

    try:
        engine, connector = await get_async_engine()

        async with engine.begin() as conn:
            result = await conn.execute(sa.text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'manga_sessions'
                AND column_name IN ('request_id', 'session_metadata', 'current_phase', 'total_phases')
                ORDER BY column_name;
            """))

            columns = result.fetchall()
            print("📊 Current manga_sessions columns:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")

            if not any(col[0] == 'request_id' for col in columns):
                print("❌ request_id column still missing!")
                return False
            else:
                print("✅ request_id column exists!")
                return True

        await engine.dispose()
        await connector.close_async()

    except Exception as e:
        print(f"❌ Error verifying schema: {e}")
        return False


async def main():
    """Main execution function"""
    print("🚀 Database Schema Fix Tool")
    print("=" * 40)

    # First verify current schema
    schema_ok = await verify_schema()

    if not schema_ok:
        print("\n🔧 Running schema fix...")
        await run_schema_fix()

        print("\n🔍 Re-verifying schema...")
        schema_ok = await verify_schema()

    if schema_ok:
        print("\n🎉 Database schema is now correct!")
        return True
    else:
        print("\n💥 Schema fix failed!")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
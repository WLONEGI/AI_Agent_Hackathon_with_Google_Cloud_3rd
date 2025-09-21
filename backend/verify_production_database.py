#!/usr/bin/env python3
"""
Production Database Verification Script
Checks what tables actually exist in the production database and verifies connection configuration
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

    print(f"🔗 Connecting to: {connection_name}")
    print(f"📊 Database: {database_name}")
    print(f"👤 User: {username}")

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
        echo=False,  # Reduce noise
    )

    return engine, connector


async def verify_production_database():
    """Comprehensive production database verification"""
    print("🔍 PRODUCTION DATABASE VERIFICATION")
    print("=" * 60)

    try:
        engine, connector = await get_async_engine()

        async with engine.begin() as conn:
            # 1. Check database connection info
            print("\n📊 DATABASE CONNECTION INFO:")
            result = await conn.execute(sa.text("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();"))
            db_info = result.fetchone()
            print(f"  Database: {db_info[0]}")
            print(f"  User: {db_info[1]}")
            print(f"  Server: {db_info[2]}:{db_info[3]}")

            # 2. List ALL tables in public schema
            print("\n📋 ALL TABLES IN PUBLIC SCHEMA:")
            result = await conn.execute(sa.text("""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = result.fetchall()

            if not tables:
                print("  ❌ NO TABLES FOUND!")
            else:
                for table in tables:
                    print(f"  ✅ {table[0]} ({table[1]})")

            # 3. Check specifically for critical tables
            print("\n🎯 CRITICAL TABLES CHECK:")
            critical_tables = ['manga_sessions', 'session_messages', 'session_events', 'phase_results', 'preview_versions']

            for table_name in critical_tables:
                result = await conn.execute(sa.text(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = '{table_name}'
                    );
                """))
                exists = result.scalar()
                status = "✅ EXISTS" if exists else "❌ MISSING"
                print(f"  {status}: {table_name}")

            # 4. Check if session_messages table exists and show its structure
            print("\n📊 SESSION_MESSAGES TABLE DETAILS:")
            result = await conn.execute(sa.text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'session_messages'
                );
            """))
            session_messages_exists = result.scalar()

            if session_messages_exists:
                print("  ✅ session_messages table EXISTS")
                result = await conn.execute(sa.text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'session_messages'
                    ORDER BY ordinal_position;
                """))
                columns = result.fetchall()
                print("  📊 Columns:")
                for col in columns:
                    print(f"    - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            else:
                print("  ❌ session_messages table MISSING!")

            # 5. Check alembic version
            print("\n📈 ALEMBIC MIGRATION STATUS:")
            result = await conn.execute(sa.text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'alembic_version'
                );
            """))
            alembic_exists = result.scalar()

            if alembic_exists:
                result = await conn.execute(sa.text("SELECT version_num FROM alembic_version;"))
                version = result.scalar()
                print(f"  ✅ Current migration: {version}")
            else:
                print("  ❌ alembic_version table missing - no migrations applied!")

            # 6. Test a simple INSERT/DELETE to verify write permissions
            print("\n🔧 WRITE PERMISSIONS TEST:")
            try:
                # Try to create a test table
                await conn.execute(sa.text("""
                    CREATE TABLE IF NOT EXISTS _test_table (
                        id SERIAL PRIMARY KEY,
                        test_data TEXT
                    );
                """))

                # Insert test data
                await conn.execute(sa.text("INSERT INTO _test_table (test_data) VALUES ('test');"))

                # Clean up
                await conn.execute(sa.text("DROP TABLE _test_table;"))

                print("  ✅ Write permissions OK")
            except Exception as e:
                print(f"  ❌ Write permissions FAILED: {e}")

            print("\n🎯 SUMMARY:")
            if not tables:
                print("  ❌ CRITICAL: No tables found in database!")
            elif not session_messages_exists:
                print("  ❌ CRITICAL: session_messages table missing!")
            else:
                print("  ✅ Database appears to be properly configured")

        await engine.dispose()
        await connector.close_async()

    except Exception as e:
        print(f"❌ Error verifying production database: {e}")
        raise


async def main():
    """Main execution function"""
    print("🚀 Production Database Verification Tool")
    print("This script verifies the actual state of the production database")
    print("to diagnose schema and connection issues.")

    await verify_production_database()


if __name__ == "__main__":
    asyncio.run(main())
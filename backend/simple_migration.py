#!/usr/bin/env python3
"""
Simple migration script to run Alembic migrations
"""
import os
import sys
from alembic.config import Config
from alembic import command
from app.core.settings import get_settings

def run_migration():
    """Run Alembic migrations"""
    try:
        print("=== Simple Migration Start ===")

        # Get settings
        settings = get_settings()
        print(f"APP_ENV: {settings.app_env}")

        # Get database URL from settings
        database_url = str(settings.database_url)
        print(f"Original Database URL: {database_url[:50]}...")

        # Convert to sync URL for Alembic
        sync_database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        print(f"Alembic URL: {sync_database_url[:50]}...")

        # Configure Alembic
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", sync_database_url)

        print("\n=== Running Migrations ===")

        # Run migrations
        command.upgrade(alembic_cfg, "head")

        print("\n=== Migration Complete! ===")
        return True

    except Exception as e:
        print(f"\n=== Migration Error ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
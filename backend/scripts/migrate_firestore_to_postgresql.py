#!/usr/bin/env python3
"""Migration script to transfer data from Firestore to PostgreSQL unified storage."""

import os
import sys
import asyncio
import json
from typing import Dict, Any, List
import structlog

# Add the parent directory to the Python path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.firebase import firebase_manager
from app.core.firebase_postgresql import postgresql_firebase_manager
from app.core.database import get_async_session
from app.models.user import User
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timezone

logger = structlog.get_logger(__name__)


class FirestoreToPostgreSQLMigrator:
    """Migrate Firestore data to PostgreSQL unified storage."""

    def __init__(self):
        self.firestore_manager = firebase_manager
        self.postgresql_manager = postgresql_firebase_manager
        self.migration_stats = {
            'users_migrated': 0,
            'users_failed': 0,
            'documents_processed': 0
        }

    async def initialize_services(self) -> bool:
        """Initialize Firebase services for migration."""
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'comic-ai-agent-470309')
        credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')

        # Initialize original Firestore manager
        if not self.firestore_manager.initialize(project_id, credentials_path):
            logger.error("Failed to initialize Firestore manager")
            return False

        # Initialize PostgreSQL-integrated manager
        if not self.postgresql_manager.initialize(project_id, credentials_path):
            logger.error("Failed to initialize PostgreSQL Firebase manager")
            return False

        logger.info("Migration services initialized successfully")
        return True

    async def migrate_user_collections(self) -> bool:
        """Migrate all user documents from Firestore to PostgreSQL."""
        if not self.firestore_manager.firestore:
            logger.warning("Firestore client not available, skipping migration")
            return True

        try:
            # Get all users from Firestore
            users_ref = self.firestore_manager.firestore.collection('users')
            users = users_ref.stream()

            logger.info("Starting Firestore user collection migration")

            async with get_async_session() as session:
                for user_doc in users:
                    await self._migrate_single_user(session, user_doc.id, user_doc.to_dict())
                    self.migration_stats['documents_processed'] += 1

                await session.commit()

            logger.info("Firestore migration completed",
                       users_migrated=self.migration_stats['users_migrated'],
                       users_failed=self.migration_stats['users_failed'])
            return True

        except Exception as e:
            logger.error("Failed to migrate Firestore users", error=str(e))
            return False

    async def _migrate_single_user(self, session, uid: str, firestore_data: Dict[str, Any]):
        """Migrate a single user document from Firestore to PostgreSQL."""
        try:
            # Transform Firestore data to PostgreSQL JSONB structure
            user_profile = {
                'photo_url': firestore_data.get('profile', {}).get('photo_url'),
                'preferences': firestore_data.get('profile', {}).get('preferences', {}),
                'bio': firestore_data.get('profile', {}).get('bio'),
                'display_settings': firestore_data.get('profile', {}).get('display_settings', {})
            }

            user_preferences = firestore_data.get('profile', {}).get('preferences', {})

            user_metadata = {
                'created_source': 'firestore_migration',
                'original_firestore_data': firestore_data.get('metadata', {}),
                'migration_timestamp': datetime.now(timezone.utc).isoformat(),
                'firestore_created_at': str(firestore_data.get('created_at')) if firestore_data.get('created_at') else None,
                'firestore_last_updated': str(firestore_data.get('last_updated')) if firestore_data.get('last_updated') else None
            }

            generation_history = firestore_data.get('generation_history', [])

            subscription_data = {
                'api_quota': firestore_data.get('api_quota', {'daily_limit': 3, 'monthly_limit': 90}),
                'tier': firestore_data.get('user_type', 'free'),
                'usage_stats': firestore_data.get('usage_stats', {}),
                'billing_info': firestore_data.get('billing_info', {})
            }

            # Create PostgreSQL user record with migrated data
            stmt = insert(User).values(
                id=uid,
                email=firestore_data.get('email'),
                display_name=firestore_data.get('display_name'),
                is_active=True,
                account_type=firestore_data.get('user_type', 'free'),
                provider='google',  # Assume Google auth for Firestore users
                firebase_claims={},
                user_profile=user_profile,
                user_preferences=user_preferences,
                user_metadata=user_metadata,
                generation_history=generation_history,
                subscription_data=subscription_data,
                created_at=self._parse_firestore_timestamp(firestore_data.get('created_at')),
                updated_at=self._parse_firestore_timestamp(firestore_data.get('last_updated'))
            )

            # Use ON CONFLICT for upsert behavior
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=dict(
                    display_name=stmt.excluded.display_name,
                    user_profile=stmt.excluded.user_profile,
                    user_preferences=stmt.excluded.user_preferences,
                    user_metadata=stmt.excluded.user_metadata,
                    generation_history=stmt.excluded.generation_history,
                    subscription_data=stmt.excluded.subscription_data,
                    updated_at=datetime.now(timezone.utc)
                )
            )

            await session.execute(stmt)
            self.migration_stats['users_migrated'] += 1
            logger.info("User migrated from Firestore to PostgreSQL", uid=uid)

        except Exception as e:
            self.migration_stats['users_failed'] += 1
            logger.error("Failed to migrate user from Firestore", uid=uid, error=str(e))

    def _parse_firestore_timestamp(self, timestamp) -> datetime:
        """Parse Firestore timestamp to Python datetime."""
        if not timestamp:
            return datetime.now(timezone.utc)

        try:
            # Handle Firestore server timestamps
            if hasattr(timestamp, 'timestamp'):
                return datetime.fromtimestamp(timestamp.timestamp(), tz=timezone.utc)
            # Handle ISO string timestamps
            elif isinstance(timestamp, str):
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                return datetime.now(timezone.utc)
        except Exception as e:
            logger.warning("Failed to parse timestamp, using current time", timestamp=str(timestamp), error=str(e))
            return datetime.now(timezone.utc)

    async def verify_migration(self) -> bool:
        """Verify that migration was successful by comparing data."""
        try:
            if not self.firestore_manager.firestore:
                logger.info("Firestore not available, skipping verification")
                return True

            # Count documents in Firestore
            users_ref = self.firestore_manager.firestore.collection('users')
            firestore_count = len(list(users_ref.stream()))

            # Count users in PostgreSQL
            async with get_async_session() as session:
                from sqlalchemy import func, select
                result = await session.execute(select(func.count()).select_from(User))
                postgresql_count = result.scalar()

            logger.info("Migration verification",
                       firestore_users=firestore_count,
                       postgresql_users=postgresql_count,
                       users_migrated=self.migration_stats['users_migrated'])

            return True

        except Exception as e:
            logger.error("Migration verification failed", error=str(e))
            return False

    async def create_backup_export(self) -> bool:
        """Create a JSON backup of Firestore data before migration."""
        if not self.firestore_manager.firestore:
            logger.info("Firestore not available, skipping backup")
            return True

        try:
            backup_data = {'users': {}, 'migration_metadata': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'firestore',
                'destination': 'postgresql'
            }}

            # Export all user documents
            users_ref = self.firestore_manager.firestore.collection('users')
            for user_doc in users_ref.stream():
                backup_data['users'][user_doc.id] = user_doc.to_dict()

            # Save backup file
            backup_path = f"firestore_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)

            logger.info("Firestore backup created", path=backup_path, user_count=len(backup_data['users']))
            return True

        except Exception as e:
            logger.error("Failed to create Firestore backup", error=str(e))
            return False

    def print_migration_summary(self):
        """Print migration summary statistics."""
        print("\n" + "="*60)
        print("FIRESTORE TO POSTGRESQL MIGRATION SUMMARY")
        print("="*60)
        print(f"Documents Processed: {self.migration_stats['documents_processed']}")
        print(f"Users Migrated: {self.migration_stats['users_migrated']}")
        print(f"Users Failed: {self.migration_stats['users_failed']}")
        print(f"Success Rate: {(self.migration_stats['users_migrated'] / max(1, self.migration_stats['documents_processed'])) * 100:.1f}%")
        print("="*60)


async def main():
    """Main migration execution."""
    print("Firestore to PostgreSQL Migration Tool")
    print("======================================")

    migrator = FirestoreToPostgreSQLMigrator()

    # Initialize services
    if not await migrator.initialize_services():
        logger.error("Failed to initialize migration services")
        sys.exit(1)

    # Create backup
    print("Creating Firestore backup...")
    if not await migrator.create_backup_export():
        logger.error("Failed to create backup")
        sys.exit(1)

    # Perform migration
    print("Starting Firestore to PostgreSQL migration...")
    if not await migrator.migrate_user_collections():
        logger.error("Migration failed")
        sys.exit(1)

    # Verify migration
    print("Verifying migration...")
    if not await migrator.verify_migration():
        logger.error("Migration verification failed")
        sys.exit(1)

    migrator.print_migration_summary()
    print("Migration completed successfully!")


if __name__ == "__main__":
    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    asyncio.run(main())
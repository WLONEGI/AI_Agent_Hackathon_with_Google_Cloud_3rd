"""
State Reconciliation Service
Phase 3: Detect and fix inconsistent session states
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.manga_session import MangaSession, MangaSessionStatus
from app.core.db import session_scope
from app.services.realtime_hub import realtime_hub
from app.services.emergency_stop import EmergencyStopManager

logger = logging.getLogger(__name__)


class StateReconciler:
    """
    Handles detection and correction of inconsistent session states

    Prevents infinite loading by identifying stale sessions and fixing them
    """

    # Time thresholds for detecting stale states
    STALE_RUNNING_MINUTES = 30  # Sessions stuck in RUNNING for 30+ minutes
    STALE_QUEUED_MINUTES = 15   # Sessions stuck in QUEUED for 15+ minutes
    STALE_PROCESSING_MINUTES = 45  # Sessions stuck in PROCESSING for 45+ minutes

    @classmethod
    async def reconcile_all_sessions(cls) -> Dict[str, Any]:
        """
        Perform comprehensive state reconciliation

        Returns:
            Statistics about reconciliation actions performed
        """
        logger.info("🔄 Starting comprehensive session state reconciliation")

        stats = {
            "total_checked": 0,
            "stale_running_fixed": 0,
            "stale_queued_fixed": 0,
            "stale_processing_fixed": 0,
            "orphaned_sessions_cleaned": 0,
            "notifications_sent": 0,
            "errors": 0
        }

        try:
            async with session_scope() as db_session:
                # Find all potentially inconsistent sessions
                inconsistent_sessions = await cls._find_inconsistent_sessions(db_session)
                stats["total_checked"] = len(inconsistent_sessions)

                logger.info(f"Found {len(inconsistent_sessions)} potentially inconsistent sessions")

                for session in inconsistent_sessions:
                    try:
                        action_taken = await cls._fix_session_state(db_session, session)
                        if action_taken:
                            stats[f"stale_{action_taken}_fixed"] += 1
                            stats["notifications_sent"] += 1
                    except Exception as e:
                        logger.error(f"Failed to fix session {session.id}: {e}")
                        stats["errors"] += 1

                # Commit all changes
                await db_session.commit()

        except Exception as e:
            logger.error(f"State reconciliation failed: {e}")
            stats["errors"] += 1

        logger.info(f"✅ State reconciliation completed: {stats}")
        return stats

    @classmethod
    async def _find_inconsistent_sessions(cls, db_session: AsyncSession) -> List[MangaSession]:
        """Find sessions with potentially inconsistent states"""
        now = datetime.utcnow()

        # Calculate cutoff times for different states
        running_cutoff = now - timedelta(minutes=cls.STALE_RUNNING_MINUTES)
        queued_cutoff = now - timedelta(minutes=cls.STALE_QUEUED_MINUTES)
        processing_cutoff = now - timedelta(minutes=cls.STALE_PROCESSING_MINUTES)

        # Query for stale sessions
        result = await db_session.execute(
            select(MangaSession).where(
                or_(
                    # Sessions stuck in RUNNING state
                    and_(
                        MangaSession.status == MangaSessionStatus.RUNNING.value,
                        MangaSession.updated_at < running_cutoff
                    ),
                    # Sessions stuck in QUEUED state
                    and_(
                        MangaSession.status == MangaSessionStatus.QUEUED.value,
                        MangaSession.updated_at < queued_cutoff
                    ),
                    # Sessions stuck in PROCESSING state
                    and_(
                        MangaSession.status == MangaSessionStatus.PROCESSING.value,
                        MangaSession.updated_at < processing_cutoff
                    )
                )
            )
        )

        return result.scalars().all()

    @classmethod
    async def _fix_session_state(
        cls,
        db_session: AsyncSession,
        session: MangaSession
    ) -> Optional[str]:
        """
        Fix an inconsistent session state

        Args:
            db_session: Database session
            session: Session to fix

        Returns:
            String describing the action taken, or None if no action needed
        """
        now = datetime.utcnow()
        time_since_update = now - session.updated_at

        logger.warning(
            f"🔧 Fixing stale session {session.id}: "
            f"status={session.status}, stale_for={time_since_update}"
        )

        # Determine the appropriate action based on current state and staleness
        if session.status == MangaSessionStatus.RUNNING.value:
            return await cls._fix_stale_running_session(db_session, session, time_since_update)
        elif session.status == MangaSessionStatus.QUEUED.value:
            return await cls._fix_stale_queued_session(db_session, session, time_since_update)
        elif session.status == MangaSessionStatus.PROCESSING.value:
            return await cls._fix_stale_processing_session(db_session, session, time_since_update)

        return None

    @classmethod
    async def _fix_stale_running_session(
        cls,
        db_session: AsyncSession,
        session: MangaSession,
        time_since_update: timedelta
    ) -> str:
        """Fix a session stuck in RUNNING state"""
        reason = f"Session stale in RUNNING state for {time_since_update}"

        # Update session to FAILED state
        await db_session.execute(
            update(MangaSession)
            .where(MangaSession.id == session.id)
            .values(
                status=MangaSessionStatus.FAILED.value,
                error_message=f"State reconciliation: {reason}",
                updated_at=datetime.utcnow()
            )
        )

        # Notify frontend immediately
        await cls._send_reconciliation_notification(session.request_id, "FAILED", reason)

        return "running"

    @classmethod
    async def _fix_stale_queued_session(
        cls,
        db_session: AsyncSession,
        session: MangaSession,
        time_since_update: timedelta
    ) -> str:
        """Fix a session stuck in QUEUED state"""
        reason = f"Session stale in QUEUED state for {time_since_update}"

        # Update session to FAILED state
        await db_session.execute(
            update(MangaSession)
            .where(MangaSession.id == session.id)
            .values(
                status=MangaSessionStatus.FAILED.value,
                error_message=f"State reconciliation: {reason}",
                updated_at=datetime.utcnow()
            )
        )

        # Notify frontend immediately
        await cls._send_reconciliation_notification(session.request_id, "FAILED", reason)

        return "queued"

    @classmethod
    async def _fix_stale_processing_session(
        cls,
        db_session: AsyncSession,
        session: MangaSession,
        time_since_update: timedelta
    ) -> str:
        """Fix a session stuck in PROCESSING state"""
        reason = f"Session stale in PROCESSING state for {time_since_update}"

        # Update session to FAILED state
        await db_session.execute(
            update(MangaSession)
            .where(MangaSession.id == session.id)
            .values(
                status=MangaSessionStatus.FAILED.value,
                error_message=f"State reconciliation: {reason}",
                updated_at=datetime.utcnow()
            )
        )

        # Notify frontend immediately
        await cls._send_reconciliation_notification(session.request_id, "FAILED", reason)

        return "processing"

    @classmethod
    async def _send_reconciliation_notification(
        cls,
        request_id: UUID,
        new_status: str,
        reason: str
    ) -> None:
        """Send WebSocket notification about state reconciliation"""
        try:
            event = {
                "type": "state_reconciliation",
                "status": new_status,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
                "reconciled": True
            }

            await realtime_hub.publish(request_id, event)
            logger.info(f"✅ Sent reconciliation notification for session {request_id}")

        except Exception as e:
            logger.error(f"❌ Failed to send reconciliation notification: {e}")

    @classmethod
    async def check_session_health(cls, session_id: str) -> Dict[str, Any]:
        """
        Check the health of a specific session

        Args:
            session_id: Session ID to check

        Returns:
            Health status and recommendations
        """
        try:
            async with session_scope() as db_session:
                result = await db_session.execute(
                    select(MangaSession).where(MangaSession.id == session_id)
                )
                session = result.scalar_one_or_none()

                if not session:
                    return {"status": "not_found", "healthy": False}

                now = datetime.utcnow()
                time_since_update = now - session.updated_at

                # Determine if session is healthy based on state and time
                is_healthy = cls._is_session_healthy(session, time_since_update)

                return {
                    "status": session.status,
                    "healthy": is_healthy,
                    "time_since_update_minutes": time_since_update.total_seconds() / 60,
                    "needs_reconciliation": not is_healthy,
                    "recommendation": cls._get_health_recommendation(session, time_since_update)
                }

        except Exception as e:
            logger.error(f"Failed to check session health for {session_id}: {e}")
            return {"status": "error", "healthy": False, "error": str(e)}

    @classmethod
    def _is_session_healthy(cls, session: MangaSession, time_since_update: timedelta) -> bool:
        """Determine if a session is healthy based on its state and timing"""
        if session.status in [MangaSessionStatus.COMPLETED.value, MangaSessionStatus.FAILED.value]:
            return True  # Terminal states are always healthy

        # Check if session has been in non-terminal state too long
        if session.status == MangaSessionStatus.RUNNING.value:
            return time_since_update < timedelta(minutes=cls.STALE_RUNNING_MINUTES)
        elif session.status == MangaSessionStatus.QUEUED.value:
            return time_since_update < timedelta(minutes=cls.STALE_QUEUED_MINUTES)
        elif session.status == MangaSessionStatus.PROCESSING.value:
            return time_since_update < timedelta(minutes=cls.STALE_PROCESSING_MINUTES)

        return True

    @classmethod
    def _get_health_recommendation(
        cls,
        session: MangaSession,
        time_since_update: timedelta
    ) -> str:
        """Get recommendation for improving session health"""
        if session.status in [MangaSessionStatus.COMPLETED.value, MangaSessionStatus.FAILED.value]:
            return "Session is in terminal state - no action needed"

        minutes_stale = time_since_update.total_seconds() / 60

        if session.status == MangaSessionStatus.RUNNING.value and minutes_stale > cls.STALE_RUNNING_MINUTES:
            return "Session appears stuck in RUNNING state - consider emergency stop"
        elif session.status == MangaSessionStatus.QUEUED.value and minutes_stale > cls.STALE_QUEUED_MINUTES:
            return "Session appears stuck in QUEUED state - check task queue health"
        elif session.status == MangaSessionStatus.PROCESSING.value and minutes_stale > cls.STALE_PROCESSING_MINUTES:
            return "Session appears stuck in PROCESSING state - check pipeline health"

        return "Session appears healthy"


# Periodic reconciliation task
async def start_periodic_reconciliation(interval_minutes: int = 10):
    """Start a background task for periodic state reconciliation"""
    logger.info(f"🔄 Starting periodic state reconciliation (every {interval_minutes} minutes)")

    while True:
        try:
            await asyncio.sleep(interval_minutes * 60)
            await StateReconciler.reconcile_all_sessions()
        except Exception as e:
            logger.error(f"Periodic reconciliation failed: {e}")
            # Continue running even if one iteration fails
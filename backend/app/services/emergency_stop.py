"""
Emergency Stop Manager for handling critical failures and timeouts
Phase 1 implementation for infinite loading prevention
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.manga_session import MangaSession, MangaSessionStatus
from app.core.db import session_scope
from app.services.realtime_hub import realtime_hub

logger = logging.getLogger(__name__)


class EmergencyStopManager:
    """Handles emergency scenarios where normal processing fails"""

    @staticmethod
    async def force_session_failed(
        session_id: str,
        reason: str,
        phase_number: Optional[int] = None
    ) -> bool:
        """
        Force a session to failed state and notify frontend immediately

        Args:
            session_id: The session to mark as failed
            reason: Human-readable reason for the failure
            phase_number: Optional phase number where failure occurred

        Returns:
            True if successful, False otherwise
        """
        try:
            async with session_scope() as db_session:
                # Update session status in database
                await db_session.execute(
                    update(MangaSession)
                    .where(MangaSession.id == session_id)
                    .values(
                        status=MangaSessionStatus.FAILED.value,
                        error_message=f"Emergency stop: {reason}",
                        updated_at=datetime.utcnow()
                    )
                )
                await db_session.commit()

                logger.warning(
                    f"🚨 Emergency stop executed for session {session_id}: {reason}"
                )

            # Immediate WebSocket notification to frontend
            await EmergencyStopManager._notify_frontend_immediately(
                session_id, reason, phase_number
            )

            return True

        except Exception as e:
            logger.error(f"❌ Emergency stop failed for session {session_id}: {e}")
            return False

    @staticmethod
    async def _notify_frontend_immediately(
        session_id: str,
        reason: str,
        phase_number: Optional[int] = None
    ) -> None:
        """Send immediate WebSocket notification to frontend"""
        try:
            event_data = {
                "type": "emergency_stop",
                "session_id": session_id,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat(),
                "phase_number": phase_number,
                "status": "FAILED"
            }

            # Try multiple notification attempts to ensure delivery
            for attempt in range(3):
                try:
                    await realtime_hub.publish(UUID(session_id), event_data)
                    logger.info(f"✅ Emergency notification sent (attempt {attempt + 1})")
                    break
                except Exception as e:
                    logger.warning(f"⚠️ Emergency notification attempt {attempt + 1} failed: {e}")
                    if attempt < 2:  # Don't wait on final attempt
                        await asyncio.sleep(0.1 * (attempt + 1))

        except Exception as e:
            logger.error(f"❌ Emergency notification completely failed: {e}")

    @staticmethod
    async def execute_with_emergency_protection(
        session_id: str,
        phase_number: int,
        phase_func,
        timeout_seconds: int = 300
    ):
        """
        Execute a phase function with emergency stop protection

        Args:
            session_id: Session ID for emergency recovery
            phase_number: Phase number being executed
            phase_func: Async function to execute
            timeout_seconds: Timeout before emergency stop

        Returns:
            Result of phase_func or raises exception
        """
        try:
            return await asyncio.wait_for(phase_func(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            await EmergencyStopManager.force_session_failed(
                session_id,
                f"Phase {phase_number} timeout after {timeout_seconds}s",
                phase_number
            )
            raise
        except Exception as e:
            await EmergencyStopManager.force_session_failed(
                session_id,
                f"Phase {phase_number} exception: {str(e)}",
                phase_number
            )
            raise


class PhaseTimeoutError(Exception):
    """Raised when a phase exceeds its timeout"""
    pass
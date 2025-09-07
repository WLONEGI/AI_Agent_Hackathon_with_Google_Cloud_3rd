"""Session Management Service - セッション管理の専門サービス"""

from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.logging import LoggerMixin
from app.models.manga import (
    MangaSession,
    PhaseResult,
    GenerationStatus
)


class SessionManagementService(LoggerMixin):
    """セッション管理の専門サービス"""
    
    def __init__(self):
        super().__init__()
    
    async def create_session(
        self,
        user_input: str,
        user_id: str,
        db: AsyncSession,
        session_id: Optional[str] = None
    ) -> MangaSession:
        """マンガセッションの作成"""
        
        if not session_id:
            session_id = str(uuid4())
        
        manga_session = MangaSession(
            id=session_id,
            user_id=user_id,
            input_text=user_input,
            status=GenerationStatus.PROCESSING,
            created_at=datetime.utcnow()
        )
        
        db.add(manga_session)
        await db.flush()
        
        self.logger.info(
            f"Created session {session_id} for user {user_id}"
        )
        
        return manga_session
    
    async def get_session(
        self,
        session_id: str,
        db: AsyncSession
    ) -> Optional[MangaSession]:
        """セッション取得"""
        
        result = await db.execute(
            select(MangaSession).where(MangaSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def update_session_status(
        self,
        session_id: str,
        status: GenerationStatus,
        db: AsyncSession,
        error_message: Optional[str] = None,
        final_quality_score: Optional[float] = None,
        total_processing_time: Optional[float] = None
    ) -> bool:
        """セッション状態の更新"""
        
        update_data = {
            "status": status
        }
        
        if status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED, GenerationStatus.CANCELLED]:
            update_data["completed_at"] = datetime.utcnow()
        
        if error_message:
            update_data["error_message"] = error_message
        
        if final_quality_score is not None:
            update_data["final_quality_score"] = final_quality_score
        
        if total_processing_time is not None:
            update_data["total_processing_time"] = total_processing_time
        
        result = await db.execute(
            update(MangaSession)
            .where(MangaSession.id == session_id)
            .values(**update_data)
        )
        
        await db.commit()
        
        success = result.rowcount > 0
        if success:
            self.logger.info(
                f"Updated session {session_id} status to {status.value}"
            )
        
        return success
    
    async def get_session_status(
        self,
        session_id: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """セッション状態の取得"""
        
        # セッション情報の取得
        session = await self.get_session(session_id, db)
        if not session:
            return None
        
        # フェーズ結果の取得
        phase_results = await db.execute(
            select(PhaseResult)
            .where(PhaseResult.manga_session_id == session_id)
            .order_by(PhaseResult.phase_number)
        )
        phases = phase_results.scalars().all()
        
        return {
            "session_id": session_id,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "current_phase": len(phases),
            "total_phases": 7,
            "quality_score": session.final_quality_score,
            "processing_time": session.total_processing_time,
            "error_message": session.error_message,
            "phases_completed": [
                {
                    "phase": p.phase_number,
                    "name": p.phase_name,
                    "quality_score": p.quality_score,
                    "processing_time": p.processing_time
                }
                for p in phases
            ]
        }
    
    async def cancel_session(
        self,
        session_id: str,
        db: AsyncSession,
        reason: str = "User cancelled"
    ) -> bool:
        """セッションのキャンセル"""
        
        success = await self.update_session_status(
            session_id,
            GenerationStatus.CANCELLED,
            db,
            error_message=reason
        )
        
        if success:
            self.logger.info(f"Cancelled session {session_id}: {reason}")
        
        return success
    
    async def get_user_sessions(
        self,
        user_id: str,
        db: AsyncSession,
        limit: int = 10
    ) -> list[Dict[str, Any]]:
        """ユーザーのセッション一覧取得"""
        
        result = await db.execute(
            select(MangaSession)
            .where(MangaSession.user_id == user_id)
            .order_by(MangaSession.created_at.desc())
            .limit(limit)
        )
        sessions = result.scalars().all()
        
        return [
            {
                "session_id": session.id,
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                "input_text": session.input_text[:100] + "..." if len(session.input_text) > 100 else session.input_text,
                "quality_score": session.final_quality_score,
                "processing_time": session.total_processing_time
            }
            for session in sessions
        ]
    
    async def cleanup_expired_sessions(
        self,
        db: AsyncSession,
        hours: int = 24
    ) -> int:
        """期限切れセッションのクリーンアップ"""
        
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 未完了の古いセッションをキャンセルに更新
        result = await db.execute(
            update(MangaSession)
            .where(MangaSession.created_at < cutoff_time)
            .where(MangaSession.status.in_([
                GenerationStatus.PROCESSING,
                GenerationStatus.WAITING_FEEDBACK
            ]))
            .values(
                status=GenerationStatus.CANCELLED,
                error_message="Session expired due to timeout",
                completed_at=datetime.utcnow()
            )
        )
        
        await db.commit()
        
        cleaned_count = result.rowcount
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} expired sessions")
        
        return cleaned_count
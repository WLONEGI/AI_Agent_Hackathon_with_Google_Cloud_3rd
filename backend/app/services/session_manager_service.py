"""
SessionManagerService - セッション管理専用サービス
マンガ生成セッションのライフサイクル管理
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.logging import LoggerMixin
from app.models.manga import MangaSession, GenerationStatus
from app.core.redis_client import redis_manager


class SessionManagerService(LoggerMixin):
    """セッション管理専用サービス"""
    
    def __init__(self):
        super().__init__()
        self.redis_client = redis_manager
    
    async def create_session(
        self,
        user_id: str,
        initial_prompt: str,
        user_preferences: Dict[str, Any],
        db: AsyncSession
    ) -> str:
        """新しいマンガ生成セッションを作成"""
        session_id = str(uuid4())
        
        try:
            manga_session = MangaSession(
                id=session_id,
                user_id=user_id,
                initial_prompt=initial_prompt,
                user_preferences=user_preferences,
                status=GenerationStatus.PENDING.value,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(manga_session)
            await db.commit()
            
            # Redisにセッション状態を保存
            await self.redis_client.set(
                f"session:{session_id}:status",
                GenerationStatus.PENDING.value,
                ttl=3600
            )
            
            self.logger.info(f"Created manga session", session_id=session_id, user_id=user_id)
            return session_id
            
        except Exception as e:
            self.logger.error(f"Failed to create session: {e}")
            await db.rollback()
            raise
    
    async def get_session_status(
        self,
        session_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """セッション状態の取得"""
        try:
            # データベースからセッション取得
            stmt = select(MangaSession).where(MangaSession.id == session_id)
            result = await db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                return {"error": "Session not found"}
            
            # フェーズ結果の取得
            from app.models.manga import PhaseResult
            phase_stmt = select(PhaseResult).where(
                PhaseResult.session_id == session_id
            ).order_by(PhaseResult.phase_number)
            
            phase_result = await db.execute(phase_stmt)
            phases = phase_result.scalars().all()
            
            # セッション状態の構築
            status_data = {
                "session_id": session_id,
                "user_id": session.user_id,
                "status": session.status,
                "initial_prompt": session.initial_prompt,
                "current_phase": session.current_phase,
                "total_phases": 7,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "phases": []
            }
            
            # フェーズ状態の追加
            for phase in phases:
                phase_data = {
                    "phase_number": phase.phase_number,
                    "status": phase.status,
                    "result": phase.result,
                    "quality_score": phase.quality_score,
                    "processing_time": phase.processing_time_seconds,
                    "completed_at": phase.completed_at.isoformat() if phase.completed_at else None
                }
                status_data["phases"].append(phase_data)
            
            return status_data
            
        except Exception as e:
            self.logger.error(f"Failed to get session status: {e}")
            return {"error": str(e)}
    
    async def update_session_status(
        self,
        session_id: str,
        status: GenerationStatus,
        current_phase: Optional[int] = None,
        db: AsyncSession = None
    ) -> bool:
        """セッション状態の更新"""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow()
            }
            
            if current_phase is not None:
                update_data["current_phase"] = current_phase
            
            stmt = update(MangaSession).where(
                MangaSession.id == session_id
            ).values(**update_data)
            
            result = await db.execute(stmt)
            await db.commit()
            
            # Redisの状態も更新
            await self.redis_client.set(
                f"session:{session_id}:status",
                status.value,
                ttl=3600
            )
            
            if current_phase is not None:
                await self.redis_client.set(
                    f"session:{session_id}:phase",
                    str(current_phase),
                    ttl=3600
                )
            
            self.logger.info(f"Updated session status", session_id=session_id, status=status.value)
            return result.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Failed to update session status: {e}")
            return False
    
    async def cancel_session(
        self,
        session_id: str,
        reason: str,
        db: AsyncSession
    ) -> bool:
        """セッションのキャンセル処理"""
        try:
            # セッション状態の更新
            await self.update_session_status(
                session_id,
                GenerationStatus.CANCELLED,
                db=db
            )
            
            # キャンセル理由の記録
            stmt = update(MangaSession).where(
                MangaSession.id == session_id
            ).values(
                cancellation_reason=reason,
                cancelled_at=datetime.utcnow()
            )
            
            await db.execute(stmt)
            await db.commit()
            
            # Redisのセッション関連データをクリア
            session_keys = [
                f"session:{session_id}:*",
                f"phase:*:{session_id}",
                f"preview:{session_id}:*"
            ]
            
            for pattern in session_keys:
                keys = await self.redis_client.scan_keys(pattern)
                for key in keys:
                    await self.redis_client.delete(key)
            
            self.logger.info(f"Session cancelled", session_id=session_id, reason=reason)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel session: {e}")
            return False
    
    async def cleanup_expired_sessions(self, db: AsyncSession, hours_old: int = 24) -> int:
        """期限切れセッションのクリーンアップ"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
            
            # 期限切れで未完了のセッションを取得
            stmt = select(MangaSession).where(
                MangaSession.created_at < cutoff_time,
                MangaSession.status.in_([
                    GenerationStatus.PENDING.value,
                    GenerationStatus.PROCESSING.value
                ])
            )
            
            result = await db.execute(stmt)
            expired_sessions = result.scalars().all()
            
            cleanup_count = 0
            for session in expired_sessions:
                await self.cancel_session(
                    session.id,
                    f"Automatic cleanup: session expired after {hours_old} hours",
                    db
                )
                cleanup_count += 1
            
            self.logger.info(f"Cleaned up {cleanup_count} expired sessions")
            return cleanup_count
            
        except Exception as e:
            self.logger.error(f"Session cleanup failed: {e}")
            return 0
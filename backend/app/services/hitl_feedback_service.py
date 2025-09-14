"""
HITLFeedbackService - Human-in-the-Loop フィードバック管理
フィードバック収集、処理、適用を専門的に管理
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import LoggerMixin
from app.models.manga import UserFeedback, MangaSession
from app.schemas.pipeline_schemas import HITLFeedback


class HITLFeedbackService(LoggerMixin):
    """Human-in-the-Loop フィードバック管理サービス"""
    
    def __init__(self):
        super().__init__()
        self.pending_feedback: Dict[str, asyncio.Event] = {}
        self.feedback_timeout = 300  # 5分
    
    async def submit_feedback(
        self,
        session_id: str,
        phase_num: int,
        feedback: HITLFeedback,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """HITLフィードバックの提出処理"""
        try:
            # フィードバック保存
            user_feedback = UserFeedback(
                session_id=session_id,
                phase_number=phase_num,
                user_id=user_id,
                feedback_type=feedback.feedback_type,
                content=feedback.content,
                quality_score=feedback.quality_score,
                suggestions=feedback.suggestions,
                created_at=datetime.utcnow()
            )
            
            db.add(user_feedback)
            await db.commit()
            
            # フィードバック完了イベントをセット
            feedback_key = f"{session_id}:{phase_num}"
            if feedback_key in self.pending_feedback:
                self.pending_feedback[feedback_key].set()
            
            self.logger.info(
                f"HITL feedback submitted",
                session_id=session_id,
                phase=phase_num,
                user_id=user_id,
                feedback_type=feedback.feedback_type
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to submit HITL feedback: {e}")
            return False
    
    async def wait_for_feedback(
        self,
        session_id: str,
        phase_num: int,
        timeout_seconds: Optional[int] = None
    ) -> bool:
        """フィードバック待機処理"""
        feedback_key = f"{session_id}:{phase_num}"
        timeout = timeout_seconds or self.feedback_timeout
        
        # イベント作成
        if feedback_key not in self.pending_feedback:
            self.pending_feedback[feedback_key] = asyncio.Event()
        
        try:
            self.logger.info(f"Waiting for HITL feedback", session_id=session_id, phase=phase_num)
            
            # タイムアウト付きで待機
            await asyncio.wait_for(
                self.pending_feedback[feedback_key].wait(),
                timeout=timeout
            )
            
            return True
            
        except asyncio.TimeoutError:
            self.logger.warning(f"HITL feedback timeout", session_id=session_id, phase=phase_num)
            return False
        
        finally:
            # クリーンアップ
            self.pending_feedback.pop(feedback_key, None)
    
    async def apply_feedback(
        self,
        session_id: str,
        phase_num: int,
        phase_result: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """フィードバックの適用処理"""
        try:
            # 最新のフィードバック取得
            feedback_stmt = select(UserFeedback).where(
                UserFeedback.session_id == session_id,
                UserFeedback.phase_number == phase_num
            ).order_by(UserFeedback.created_at.desc()).limit(1)
            
            result = await db.execute(feedback_stmt)
            feedback = result.scalar_one_or_none()
            
            if not feedback:
                self.logger.warning(f"No feedback found for application", session_id=session_id, phase=phase_num)
                return phase_result
            
            # フィードバック内容に基づく調整
            adjusted_result = phase_result.copy()
            
            # 品質スコア調整
            if feedback.quality_score:
                adjusted_result["quality_score"] = feedback.quality_score
            
            # 提案の反映
            if feedback.suggestions:
                if "style_adjustments" in feedback.suggestions:
                    adjusted_result.update(feedback.suggestions["style_adjustments"])
                
                if "content_modifications" in feedback.suggestions:
                    content_mods = feedback.suggestions["content_modifications"]
                    for key, value in content_mods.items():
                        if key in adjusted_result:
                            adjusted_result[key] = value
            
            # フィードバック履歴の記録
            adjusted_result["feedback_applied"] = {
                "feedback_id": str(feedback.id),
                "user_id": feedback.user_id,
                "applied_at": datetime.utcnow().isoformat(),
                "original_quality": phase_result.get("quality_score"),
                "adjusted_quality": adjusted_result.get("quality_score")
            }
            
            self.logger.info(
                f"HITL feedback applied",
                session_id=session_id,
                phase=phase_num,
                feedback_id=str(feedback.id)
            )
            
            return adjusted_result
            
        except Exception as e:
            self.logger.error(f"Failed to apply HITL feedback: {e}")
            return phase_result
    
    async def get_feedback_history(
        self,
        session_id: str,
        phase_num: Optional[int] = None,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """フィードバック履歴の取得"""
        conditions = [UserFeedback.session_id == session_id]
        
        if phase_num is not None:
            conditions.append(UserFeedback.phase_number == phase_num)
        
        stmt = select(UserFeedback).where(*conditions).order_by(UserFeedback.created_at.desc())
        
        result = await db.execute(stmt)
        feedbacks = result.scalars().all()
        
        return [
            {
                "id": str(feedback.id),
                "phase_number": feedback.phase_number,
                "user_id": feedback.user_id,
                "feedback_type": feedback.feedback_type,
                "content": feedback.content,
                "quality_score": feedback.quality_score,
                "suggestions": feedback.suggestions,
                "created_at": feedback.created_at.isoformat()
            }
            for feedback in feedbacks
        ]
    
    async def cleanup_pending_feedback(self):
        """保留中のフィードバック待機をクリーンアップ"""
        self.pending_feedback.clear()
        self.logger.info("Pending feedback cleanup completed")
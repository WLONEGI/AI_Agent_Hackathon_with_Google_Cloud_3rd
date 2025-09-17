from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.manga import FeedbackRequest
from app.db.models import MangaSession, UserAccount, UserFeedback


class FeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def submit_feedback(
        self,
        request_id: UUID,
        payload: FeedbackRequest,
        user: UserAccount | None = None,
    ) -> dict[str, str]:
        session_result = await self.db.execute(
            select(MangaSession).where(MangaSession.request_id == request_id)
        )
        session_obj = session_result.scalar_one_or_none()
        if session_obj is None:
            raise ValueError("session_not_found")
        if user and session_obj.user_id and session_obj.user_id != user.id:
            raise ValueError("session_not_found")

        feedback = UserFeedback(
            session_id=session_obj.id,
            phase=payload.phase,
            feedback_type=payload.payload.feedback_type,
            payload=payload.payload.content,
        )
        self.db.add(feedback)
        await self.db.flush()
        return {"status": "accepted"}

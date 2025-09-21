from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas.manga import MessageRequest, MessageResponse, MessagesListResponse
from app.db.models import MangaSession, SessionMessage, UserAccount


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_session_messages(
        self,
        request_id: UUID,
        current_user: UserAccount,
        limit: int = 50,
        offset: int = 0,
    ) -> MessagesListResponse:
        """Get paginated messages for a session."""
        # Get session
        session = await self._get_user_session(request_id, current_user)

        # Get total count
        total_query = func.count(SessionMessage.id).filter(
            SessionMessage.session_id == session.id
        )
        total = await self.db.scalar(total_query)

        # Get messages with pagination
        from sqlalchemy import select
        messages_query = (
            select(SessionMessage)
            .where(SessionMessage.session_id == session.id)
            .order_by(desc(SessionMessage.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(messages_query)
        messages = result.scalars().all()

        # Convert to response format
        message_responses = [
            MessageResponse(
                id=str(msg.id),
                session_id=str(msg.session_id),
                message_type=msg.message_type,
                content=msg.content,
                phase=msg.phase,
                metadata=msg.metadata,
                created_at=msg.created_at,
                updated_at=msg.updated_at,
            )
            for msg in messages
        ]

        has_more = (offset + limit) < total

        return MessagesListResponse(
            messages=message_responses,
            total=total,
            has_more=has_more,
        )

    async def create_message(
        self,
        request_id: UUID,
        payload: MessageRequest,
        current_user: UserAccount,
    ) -> MessageResponse:
        """Create a new message in the session."""
        # Get session
        session = await self._get_user_session(request_id, current_user)

        # Create message
        message = SessionMessage(
            session_id=session.id,
            message_type=payload.message_type,
            content=payload.content,
            phase=payload.phase,
            metadata=payload.metadata or {},
        )

        self.db.add(message)
        await self.db.flush()
        await self.db.commit()

        # Create event for real-time updates
        await self._create_session_event(
            session.id,
            "message_created",
            {
                "message_id": str(message.id),
                "message_type": message.message_type,
                "content": message.content[:100] + "..." if len(message.content) > 100 else message.content,
                "phase": message.phase,
            },
        )

        return MessageResponse(
            id=str(message.id),
            session_id=str(message.session_id),
            message_type=message.message_type,
            content=message.content,
            phase=message.phase,
            metadata=message.metadata,
            created_at=message.created_at,
            updated_at=message.updated_at,
        )

    async def _get_user_session(self, request_id: UUID, current_user: UserAccount) -> MangaSession:
        """Get session and verify ownership."""
        from sqlalchemy import select

        query = (
            select(MangaSession)
            .where(MangaSession.request_id == request_id)
            .where(MangaSession.user_id == current_user.id)
        )

        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        return session

    async def _create_session_event(self, session_id: UUID, event_type: str, event_data: dict):
        """Create a session event for real-time updates."""
        from app.db.models import SessionEvent

        event = SessionEvent(
            session_id=session_id,
            event_type=event_type,
            event_data=event_data,
        )

        self.db.add(event)
        await self.db.flush()
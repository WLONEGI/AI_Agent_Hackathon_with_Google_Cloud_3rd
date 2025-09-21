from __future__ import annotations

import json
import asyncio
from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SessionEvent, MangaSession, UserAccount


class WebSocketManager:
    def __init__(self):
        # Map of session_id to set of websockets
        self.connections: Dict[str, Set[WebSocket]] = {}
        # Map of websocket to user info
        self.websocket_users: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str):
        """Accept a new websocket connection."""
        await websocket.accept()

        if session_id not in self.connections:
            self.connections[session_id] = set()

        self.connections[session_id].add(websocket)
        self.websocket_users[websocket] = {
            "session_id": session_id,
            "user_id": user_id
        }

    def disconnect(self, websocket: WebSocket):
        """Remove a websocket connection."""
        if websocket in self.websocket_users:
            user_info = self.websocket_users[websocket]
            session_id = user_info["session_id"]

            # Remove from session connections
            if session_id in self.connections:
                self.connections[session_id].discard(websocket)
                if not self.connections[session_id]:
                    del self.connections[session_id]

            # Remove user mapping
            del self.websocket_users[websocket]

    async def send_to_session(self, session_id: str, message: dict):
        """Send a message to all websockets connected to a session."""
        if session_id in self.connections:
            disconnected = set()

            for websocket in self.connections[session_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception:
                    # Mark for removal if send fails
                    disconnected.add(websocket)

            # Clean up disconnected websockets
            for websocket in disconnected:
                self.disconnect(websocket)

    async def broadcast_session_event(self, session_id: UUID, event_type: str, event_data: dict):
        """Broadcast an event to all websockets in a session."""
        message = {
            "type": "session_event",
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": str(event_data.get("timestamp", ""))
        }

        await self.send_to_session(str(session_id), message)


# Global websocket manager instance
websocket_manager = WebSocketManager()


class WebSocketService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.manager = websocket_manager

    async def handle_websocket_connection(
        self,
        websocket: WebSocket,
        request_id: UUID,
        current_user: UserAccount,
    ):
        """Handle a websocket connection for a session."""
        # Verify session ownership
        session = await self._get_user_session(request_id, current_user)

        await self.manager.connect(websocket, str(session.id), str(current_user.id))

        try:
            # Send initial session data
            await self._send_initial_data(websocket, session)

            # Listen for messages
            while True:
                data = await websocket.receive_text()
                await self._handle_websocket_message(websocket, session, data)

        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            self.manager.disconnect(websocket)

    async def _send_initial_data(self, websocket: WebSocket, session: MangaSession):
        """Send initial session data to a new websocket connection."""
        # Get recent messages
        from app.services.message_service import MessageService
        from app.services.phase_preview_service import PhasePreviewService

        message_service = MessageService(self.db)
        preview_service = PhasePreviewService(self.db)

        # Get session owner (simplified for this context)
        user_query = select(UserAccount).where(UserAccount.id == session.user_id)
        result = await self.db.execute(user_query)
        user = result.scalar_one()

        # Get messages and previews
        messages = await message_service.get_session_messages(session.request_id, user, limit=20)
        previews = await preview_service.get_phase_previews(session.request_id, user)

        initial_data = {
            "type": "initial_data",
            "session": {
                "id": str(session.id),
                "request_id": str(session.request_id),
                "status": session.status,
                "current_phase": session.current_phase,
                "title": session.title,
            },
            "messages": [msg.dict() for msg in messages.messages],
            "phases": [preview.dict() for preview in previews],
        }

        await websocket.send_text(json.dumps(initial_data))

    async def _handle_websocket_message(self, websocket: WebSocket, session: MangaSession, data: str):
        """Handle incoming websocket message."""
        try:
            message = json.loads(data)
            message_type = message.get("type")

            if message_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message_type == "chat_message":
                # Handle chat message through API
                content = message.get("content", "")
                if content.strip():
                    # This would typically trigger the message API
                    await self._broadcast_new_message(session, content, "user")

        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))

    async def _broadcast_new_message(self, session: MangaSession, content: str, message_type: str):
        """Broadcast a new message to all session websockets."""
        event_data = {
            "session_id": str(session.id),
            "message_type": message_type,
            "content": content,
            "timestamp": str(asyncio.get_event_loop().time())
        }

        await self.manager.broadcast_session_event(
            session.id,
            "message_created",
            event_data
        )

    async def _get_user_session(self, request_id: UUID, current_user: UserAccount) -> MangaSession:
        """Get session and verify ownership."""
        from fastapi import HTTPException, status

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
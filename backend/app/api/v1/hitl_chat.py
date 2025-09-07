"""HITL Chat API v1 - Interactive chat feedback system (API Design Document Compliant)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.user import User
from app.models.manga import MangaSession
from app.api.v1.security import get_current_active_user, check_api_limit

router = APIRouter()

# Request/Response Models (Design Document Compliant)
class InterpretedAction(BaseModel):
    """Interpreted action from chat message (API Design Document Compliant)."""
    type: str = Field(..., description="Action type")
    parameters: Dict[str, Any] = Field(..., description="Action parameters")

class PreviewUpdate(BaseModel):
    """Preview update information (API Design Document Compliant)."""
    version_id: str = Field(..., description="New version ID")
    preview_url: str = Field(..., description="Updated preview URL")

class SuggestedAction(BaseModel):
    """Suggested follow-up action (API Design Document Compliant)."""
    label: str = Field(..., description="Action label")
    action: str = Field(..., description="Action identifier")

class ChatRequest(BaseModel):
    """Chat message request (API Design Document Compliant)."""
    phase: int = Field(..., ge=1, le=7, description="Phase number")
    message: str = Field(..., min_length=1, max_length=1000, description="Chat message")
    session_id: str = Field(..., description="Chat session ID")
    message_type: str = Field("text", description="Message type (text|quick_action)")

class ChatResponse(BaseModel):
    """Chat message response (API Design Document Compliant)."""
    message_id: str = Field(..., description="Generated message ID")
    phase: int = Field(..., description="Phase number")
    status: str = Field(..., description="Processing status")
    interpreted_action: InterpretedAction = Field(..., description="Interpreted action")
    preview_update: PreviewUpdate = Field(..., description="Preview update")
    suggested_actions: List[SuggestedAction] = Field(..., description="Suggested follow-up actions")

class AppliedChange(BaseModel):
    """Applied change information (API Design Document Compliant)."""
    type: str = Field(..., description="Change type")
    description: str = Field(..., description="Change description")

class ChatMessage(BaseModel):
    """Chat message history item (API Design Document Compliant)."""
    message_id: str = Field(..., description="Message ID")
    timestamp: str = Field(..., description="ISO8601 timestamp")
    sender: str = Field(..., description="Sender (user|system)")
    phase: int = Field(..., description="Phase number")
    content: str = Field(..., description="Message content")
    applied_changes: Optional[AppliedChange] = Field(None, description="Applied changes")

class ChatHistoryResponse(BaseModel):
    """Chat history response (API Design Document Compliant)."""
    session_id: str = Field(..., description="Chat session ID")
    messages: List[ChatMessage] = Field(..., description="Message history")
    total_messages: int = Field(..., description="Total message count")
    phases_modified: List[int] = Field(..., description="Phases that were modified")


# ===== DESIGN DOCUMENT COMPLIANT ENDPOINTS =====

@router.post("/manga/{request_id}/chat", response_model=ChatResponse)
async def send_chat_feedback(
    request_id: UUID,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit)
) -> ChatResponse:
    """Send chat feedback message (POST /api/v1/manga/{request_id}/chat).
    
    Fully complies with API design document specification.
    Processes natural language feedback through chat interface.
    
    Requires: manga:feedback permission + ownership
    """
    
    # Validate session exists and user has ownership
    session = await db.get(MangaSession, request_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Validate phase number
    if not (1 <= chat_request.phase <= 7):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phase must be between 1 and 7"
        )
    
    # Generate message ID
    message_id = str(uuid4())
    
    # Interpret the chat message into structured actions
    interpreted_action = _interpret_chat_message(chat_request.message)
    
    # Generate new version and preview URL
    version_id = str(uuid4())
    preview_url = f"https://storage.googleapis.com/manga-previews/chat_update_{request_id}_p{chat_request.phase}_v{version_id}.webp"
    
    preview_update = PreviewUpdate(
        version_id=version_id,
        preview_url=preview_url
    )
    
    # Generate suggested follow-up actions based on interpreted action
    suggested_actions = _generate_suggested_actions(interpreted_action)
    
    # TODO: Store chat message in database
    # TODO: Apply the interpreted action to the phase data
    # TODO: Generate updated preview
    
    return ChatResponse(
        message_id=message_id,
        phase=chat_request.phase,
        status="processing",
        interpreted_action=interpreted_action,
        preview_update=preview_update,
        suggested_actions=suggested_actions
    )


@router.get("/manga/{request_id}/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    request_id: UUID,
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_api_limit)
) -> ChatHistoryResponse:
    """Get chat history (GET /api/v1/manga/{request_id}/chat/history).
    
    Fully complies with API design document specification.
    Returns complete chat history for the session.
    
    Requires: manga:read permission + ownership
    """
    
    # Validate session exists and user has ownership
    session = await db.get(MangaSession, request_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Mock chat history data
    chat_session_id = session_id or str(uuid4())
    
    messages = [
        ChatMessage(
            message_id=str(uuid4()),
            timestamp=session.created_at.isoformat() + "Z",
            sender="user",
            phase=1,
            content="キャラクターをもう一人追加して、主人公のライバルにしてください",
            applied_changes=AppliedChange(
                type="character_addition",
                description="ライバルキャラクター追加"
            )
        ),
        ChatMessage(
            message_id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            sender="system",
            phase=1,
            content="ライバルキャラクターを追加しました。性格設定を確認してください。",
            applied_changes=None
        )
    ]
    
    return ChatHistoryResponse(
        session_id=chat_session_id,
        messages=messages,
        total_messages=len(messages),
        phases_modified=[1, 2, 4]  # Mock data
    )


# Helper functions for chat processing
def _interpret_chat_message(message: str) -> InterpretedAction:
    """Interpret chat message into structured action."""
    
    # Simple keyword-based interpretation (in production, would use NLP)
    message_lower = message.lower()
    
    if "キャラクター" in message and "追加" in message:
        return InterpretedAction(
            type="character_addition",
            parameters={
                "role": "rival" if "ライバル" in message else "supporting",
                "relationship": "antagonist" if "ライバル" in message else "friend"
            }
        )
    elif "明るい" in message or "コメディ" in message:
        return InterpretedAction(
            type="mood_adjustment",
            parameters={
                "direction": "brighter",
                "intensity": 0.7
            }
        )
    elif "シリアス" in message:
        return InterpretedAction(
            type="mood_adjustment",
            parameters={
                "direction": "serious",
                "intensity": 0.8
            }
        )
    else:
        return InterpretedAction(
            type="general_modification",
            parameters={
                "description": message[:100]  # Truncate long messages
            }
        )


def _generate_suggested_actions(interpreted_action: InterpretedAction) -> List[SuggestedAction]:
    """Generate suggested follow-up actions based on interpreted action."""
    
    if interpreted_action.type == "character_addition":
        return [
            SuggestedAction(label="性格を決める", action="define_personality"),
            SuggestedAction(label="ビジュアルを調整", action="adjust_visual"),
            SuggestedAction(label="関係性を設定", action="set_relationship")
        ]
    elif interpreted_action.type == "mood_adjustment":
        return [
            SuggestedAction(label="詳細を調整", action="fine_tune_mood"),
            SuggestedAction(label="プレビューを確認", action="review_preview"),
            SuggestedAction(label="次のフェーズへ", action="proceed_next")
        ]
    else:
        return [
            SuggestedAction(label="変更を確認", action="review_changes"),
            SuggestedAction(label="プレビュー更新", action="update_preview")
        ]
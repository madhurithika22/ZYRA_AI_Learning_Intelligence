from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.learner import Learner
from app.schemas.conversation import (
    CreateSessionRequest,
    MessageResponse,
    SendMessageRequest,
    SessionDetailResponse,
    SessionResponse,
)
from app.services.conversation.conversational_service import ConversationalService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Grounded Conversational Learning Intelligence"])


@router.post("/v1/learners/{learner_id}/conversation/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation_session(
    learner_id: UUID,
    payload: CreateSessionRequest | None = None,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> SessionResponse:
    """Create a new conversation session for a learner."""
    verify_learner_access(learner_id, current_learner)
    title = payload.title if payload else None
    service = ConversationalService(db)
    try:
        return await service.create_session(learner_id, title)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post("/v1/conversation/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_conversation_message(
    session_id: UUID,
    payload: SendMessageRequest,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    """Submit a user message to a conversation session and receive a grounded assistant response."""
    verify_learner_access(payload.learner_id, current_learner)
    service = ConversationalService(db)
    try:
        return await service.send_message(session_id, payload.learner_id, payload.message)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err


@router.get("/v1/conversation/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_conversation_session(
    session_id: UUID,
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> SessionDetailResponse:
    """Retrieve session details and complete message history."""
    verify_learner_access(learner_id, current_learner)
    service = ConversationalService(db)
    try:
        return await service.get_session(session_id, learner_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err


@router.get("/v1/conversation/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_session_messages(
    session_id: UUID,
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> list[MessageResponse]:
    """Retrieve message history for a conversation session."""
    verify_learner_access(learner_id, current_learner)
    service = ConversationalService(db)
    try:
        detail = await service.get_session(session_id, learner_id)
        return detail.messages
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except PermissionError as err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(err)) from err

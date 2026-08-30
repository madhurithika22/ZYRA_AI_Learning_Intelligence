from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.learner import Learner
from app.schemas.next_action import (
    NextActionCandidatesResponse,
    NextActionResponse,
)
from app.services.next_action_service import NextActionService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["next-action"])


@router.get(
    "/v1/learners/{learner_id}/next-action",
    response_model=NextActionResponse,
)
async def get_learner_next_action(
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> NextActionResponse:
    """Fetch the top Next-Best-Action recommendation with alternatives for a learner."""
    verify_learner_access(learner_id, current_learner)
    service = NextActionService(db)
    try:
        return await service.get_next_action(learner_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get(
    "/v1/learners/{learner_id}/goals/{goal_id}/next-action",
    response_model=NextActionResponse,
)
async def get_goal_next_action(
    learner_id: UUID,
    goal_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> NextActionResponse:
    verify_learner_access(learner_id, current_learner)
    """Fetch the top Next-Best-Action recommendation for a specific goal."""
    service = NextActionService(db)
    try:
        return await service.get_next_action(learner_id, goal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get(
    "/v1/learners/{learner_id}/goals/{goal_id}/next-actions",
    response_model=NextActionCandidatesResponse,
)
async def get_goal_next_actions(
    learner_id: UUID,
    goal_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> NextActionCandidatesResponse:
    """Fetch ranked candidate actions for a specific goal."""
    verify_learner_access(learner_id, current_learner)
    service = NextActionService(db)
    try:
        return await service.get_action_candidates(learner_id, goal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

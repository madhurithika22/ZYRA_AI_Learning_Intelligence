from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.learner import Learner
from app.schemas.app_state import LearnerAppStateResponse
from app.services.app_state_service import AppStateService
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/learners", tags=["Learner App State"])


@router.get("/me/state", response_model=LearnerAppStateResponse)
async def get_my_app_state(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    current_learner: Learner = Depends(get_current_learner),
):
    return await AppStateService.get_learner_app_state(db, current_learner.id)


@router.get("/{learner_id}/app-state", response_model=LearnerAppStateResponse)
async def get_learner_app_state(
    learner_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    current_learner: Learner = Depends(get_current_learner),
):
    verify_learner_access(learner_id, current_learner)
    return await AppStateService.get_learner_app_state(db, learner_id)

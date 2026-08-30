from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.learner import Learner
from app.schemas.progress import (
    GoalSkillProgressResponse,
    LearnerProgressSummary,
    PathProgressResponse,
    SkillHistoryItem,
)
from app.services.progress_service import ProgressService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["progress"])


@router.get(
    "/v1/learners/{learner_id}/progress",
    response_model=LearnerProgressSummary,
)
async def get_learner_progress_summary(
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> LearnerProgressSummary:
    """Fetch complete longitudinal progress summary for a learner."""
    verify_learner_access(learner_id, current_learner)
    service = ProgressService(db)
    try:
        return await service.get_learner_progress_summary(learner_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get(
    "/v1/learners/{learner_id}/goals/{goal_id}/progress",
    response_model=GoalSkillProgressResponse,
)
async def get_goal_progress(
    learner_id: UUID,
    goal_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> GoalSkillProgressResponse:
    """Fetch goal skill progress proxy and bottleneck breakdown for a specific goal."""
    verify_learner_access(learner_id, current_learner)
    service = ProgressService(db)
    try:
        return await service.get_goal_progress(learner_id, goal_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get(
    "/v1/learning-paths/{path_id}/progress",
    response_model=PathProgressResponse,
)
async def get_path_progress(
    path_id: UUID,
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> PathProgressResponse:
    """Fetch node completion and time progress for a learning path."""
    verify_learner_access(learner_id, current_learner)
    service = ProgressService(db)
    try:
        return await service.get_path_progress(learner_id, path_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get(
    "/v1/learners/{learner_id}/skills/{skill_id}/history",
    response_model=list[SkillHistoryItem],
)
async def get_skill_history(
    learner_id: UUID,
    skill_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> list[SkillHistoryItem]:
    """Fetch chronological mastery and evidence history for a target skill."""
    verify_learner_access(learner_id, current_learner)
    service = ProgressService(db)
    try:
        return await service.get_skill_history(learner_id, skill_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

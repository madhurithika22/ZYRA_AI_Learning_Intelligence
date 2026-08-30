from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.learner import Learner
from app.models.learning_path import LearningPath
from app.schemas.replanning import (
    PathDiffResponse,
    PathVersionItem,
    ReplanDecision,
    ReplanStatusResponse,
)
from app.services.replanning_service import ReplanningService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1", tags=["Dynamic Replanning Engine"])


@router.get(
    "/learners/{learner_id}/goals/{goal_id}/replan-status",
    response_model=ReplanStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def check_replan_status(
    learner_id: UUID,
    goal_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> ReplanStatusResponse:
    verify_learner_access(learner_id, current_learner)
    """Check if dynamic replanning condition is triggered (delta > threshold)."""
    try:
        service = ReplanningService(db)
        return await service.check_replan_needed(learner_id, goal_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post(
    "/learners/{learner_id}/goals/{goal_id}/replan",
    response_model=ReplanDecision,
    status_code=status.HTTP_200_OK,
)
async def trigger_replan(
    learner_id: UUID,
    goal_id: UUID,
    manual: bool = Query(False),
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> ReplanDecision:
    verify_learner_access(learner_id, current_learner)
    """Trigger dynamic replanning to generate draft path version V_{k+1}."""
    try:
        service = ReplanningService(db)
        return await service.generate_replan(learner_id, goal_id, manual_trigger=manual)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get(
    "/learning-paths/{path_id}/versions",
    response_model=list[PathVersionItem],
    status_code=status.HTTP_200_OK,
)
async def get_path_versions(
    path_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> list[PathVersionItem]:
    """Fetch historical path versions and lineage."""
    path_res = await db.execute(select(LearningPath).where(LearningPath.id == path_id))
    path = path_res.scalars().first()
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Learning path {path_id} not found.")
    verify_learner_access(path.learner_id, current_learner)

    try:
        service = ReplanningService(db)
        return await service.get_path_versions(path_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get(
    "/learning-paths/{from_path_id}/diff/{to_path_id}",
    response_model=PathDiffResponse,
    status_code=status.HTTP_200_OK,
)
async def get_path_diff(
    from_path_id: UUID,
    to_path_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> PathDiffResponse:
    """Fetch structured path delta diff between two path versions."""
    path_res = await db.execute(select(LearningPath).where(LearningPath.id == from_path_id))
    path = path_res.scalars().first()
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Learning path {from_path_id} not found.")
    verify_learner_access(path.learner_id, current_learner)

    try:
        service = ReplanningService(db)
        return await service.get_path_diff(from_path_id, to_path_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post(
    "/learning-paths/{draft_path_id}/accept",
    response_model=PathVersionItem,
    status_code=status.HTTP_200_OK,
)
async def accept_replan(
    draft_path_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> PathVersionItem:
    """Accept draft path version, activating V_{k+1} and superseding V_k."""
    path_res = await db.execute(select(LearningPath).where(LearningPath.id == draft_path_id))
    path = path_res.scalars().first()
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Learning path {draft_path_id} not found.")
    verify_learner_access(path.learner_id, current_learner)

    try:
        service = ReplanningService(db)
        return await service.accept_replan(draft_path_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.post(
    "/learning-paths/{draft_path_id}/reject",
    response_model=PathVersionItem,
    status_code=status.HTTP_200_OK,
)
async def reject_replan(
    draft_path_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> PathVersionItem:
    """Reject draft path version, keeping previous version active."""
    path_res = await db.execute(select(LearningPath).where(LearningPath.id == draft_path_id))
    path = path_res.scalars().first()
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Learning path {draft_path_id} not found.")
    verify_learner_access(path.learner_id, current_learner)

    try:
        service = ReplanningService(db)
        return await service.reject_replan(draft_path_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

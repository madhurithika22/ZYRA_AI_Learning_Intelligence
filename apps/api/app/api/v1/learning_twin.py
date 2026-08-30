from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.learner import Learner
from app.schemas.learning_twin import DecisionTrace, LearningTwinResponse
from app.services.learning_twin_service import LearningTwinService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1", tags=["Learning Twin & Decision Center"])


async def _verify_learner_exists(learner_id: UUID, db: AsyncSession) -> None:
    """Verify that learner exists in database for ownership/authorization enforcement."""
    stmt = select(Learner).where(Learner.id == learner_id)
    learner = (await db.execute(stmt)).scalar_one_or_none()
    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner with ID '{learner_id}' not found.",
        )


@router.get(
    "/learners/{learner_id}/learning-twin",
    response_model=LearningTwinResponse,
    summary="Fetch unified Learning Twin snapshot",
)
async def get_learning_twin(
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> LearningTwinResponse:
    """Fetch the complete, unified learner-state computational snapshot."""
    verify_learner_access(learner_id, current_learner)
    try:
        service = LearningTwinService(db)
        return await service.get_learning_twin(learner_id, include_trace=True)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.get(
    "/learners/{learner_id}/learning-twin/trace",
    response_model=DecisionTrace,
    summary="Fetch decision trace for Learning Twin",
)
async def get_learning_twin_trace(
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> DecisionTrace:
    """Fetch the deterministic decision trace explaining the current Learning Twin snapshot."""
    verify_learner_access(learner_id, current_learner)
    try:
        service = LearningTwinService(db)
        twin = await service.get_learning_twin(learner_id, include_trace=True)
        if not twin.decision_trace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Decision trace unavailable for learner.",
            )
        return twin.decision_trace
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err

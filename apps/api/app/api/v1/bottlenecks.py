from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.learner import Learner
from app.schemas.bottleneck import BottleneckAnalysisResponse
from app.services.bottleneck_analysis import BottleneckAnalysisService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1", tags=["bottlenecks"])


@router.get(
    "/learners/{learner_id}/goals/{goal_id}/bottlenecks",
    response_model=BottleneckAnalysisResponse,
    summary="Get derived bottleneck analysis and skill gap intelligence",
)
async def get_bottleneck_analysis(
    learner_id: UUID,
    goal_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> BottleneckAnalysisResponse:
    """Analyze learner demonstrated competencies, role skill requirements, and dependency graphs to rank and explain learning bottlenecks."""
    verify_learner_access(learner_id, current_learner)
    service = BottleneckAnalysisService(session=session)
    try:
        response = await service.analyze_bottlenecks(
            learner_id=learner_id,
            goal_id=goal_id,
        )
        return response
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err

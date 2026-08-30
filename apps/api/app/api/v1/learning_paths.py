from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.learner import Learner
from app.models.learning_path import LearningPath
from app.models.learning_path_node import LearningPathNode
from app.schemas.learning_path import (
    ActivatePathResponse,
    PathComparisonResponse,
    PathNodeResponse,
    PathStrategyOption,
)
from app.services.learning_path_service import LearningPathService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/v1", tags=["learning_paths"])


@router.post(
    "/learners/{learner_id}/goals/{goal_id}/paths/generate",
    response_model=PathComparisonResponse,
    summary="Generate and optimize 4 learning path strategy options",
)
async def generate_learning_paths(
    learner_id: UUID,
    goal_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> PathComparisonResponse:
    """Generate 4 strategy-optimized learning path candidates (FASTEST, BALANCED, DEEP MASTERY, PROJECT FIRST)."""
    verify_learner_access(learner_id, current_learner)
    service = LearningPathService(session=session)
    try:
        return await service.generate_candidate_paths(learner_id=learner_id, goal_id=goal_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.get(
    "/learners/{learner_id}/goals/{goal_id}/paths",
    response_model=PathComparisonResponse,
    summary="Retrieve candidate learning path options for a goal",
)
async def get_learning_path_options(
    learner_id: UUID,
    goal_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> PathComparisonResponse:
    verify_learner_access(learner_id, current_learner)
    """Retrieve existing or generated learning path strategy options for a learner goal."""
    service = LearningPathService(session=session)
    try:
        return await service.generate_candidate_paths(learner_id=learner_id, goal_id=goal_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.get(
    "/learning-paths/{path_id}",
    response_model=PathStrategyOption,
    summary="Get single learning path by ID",
)
async def get_learning_path_by_id(
    path_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> PathStrategyOption:
    """Retrieve details and sequence nodes of a single learning path."""
    stmt = (
        select(LearningPath)
        .where(LearningPath.id == path_id)
        .options(
            selectinload(LearningPath.nodes).selectinload(LearningPathNode.resource),
            selectinload(LearningPath.nodes).selectinload(LearningPathNode.skill),
        )
    )
    res = await session.execute(stmt)
    path = res.scalars().first()
    if not path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learning path with ID '{path_id}' not found.",
        )
    verify_learner_access(path.learner_id, current_learner)

    nodes_resp = [
        PathNodeResponse(
            id=n.id,
            sequence=n.sequence,
            resource_id=n.resource_id,
            resource_title=n.resource.title if n.resource else f"Resource Step {n.sequence}",
            resource_type=n.resource.resource_type if n.resource else "learning_activity",
            skill_id=n.skill_id,
            skill_name=n.skill.name if n.skill else "Target Skill",
            estimated_minutes=n.estimated_minutes or 60,
            rationale=n.rationale or "",
        )
        for n in path.nodes
    ]

    total_mins = path.estimated_minutes or sum(n.estimated_minutes or 60 for n in path.nodes)

    return PathStrategyOption(
        path_id=path.id,
        strategy=path.strategy,
        name=path.name,
        status=path.status,
        feasible=True,
        estimated_minutes=total_mins,
        estimated_weeks=round(total_mins / (60 * 7), 1),
        total_resources=len(path.nodes),
        target_skill_coverage=1.0,
        bottleneck_coverage=1.0,
        practical_value=0.8,
        redundancy_score=0.0,
        risk_score=0.0,
        path_score=path.expected_readiness or 1.0,
        explanation=f"Learning path '{path.name}' targeting goal.",
        nodes=nodes_resp,
    )


@router.post(
    "/learning-paths/{path_id}/activate",
    response_model=ActivatePathResponse,
    summary="Activate a chosen learning path option",
)
async def activate_learning_path(
    path_id: UUID,
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> ActivatePathResponse:
    """Mark chosen learning path as active and archive other candidate options for the goal."""
    verify_learner_access(learner_id, current_learner)
    service = LearningPathService(session=session)
    try:
        return await service.activate_path(path_id=path_id, learner_id=learner_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err

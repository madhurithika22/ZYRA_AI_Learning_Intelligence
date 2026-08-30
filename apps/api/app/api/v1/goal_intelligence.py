from typing import Any
from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.learner import Learner
from app.models.learner_profile import LearnerProfile
from app.models.user_account import UserAccount
from app.schemas.goal_intelligence import (
    GoalCreationResponse,
    GoalIntelligenceResult,
    GoalInterpretationRequest,
)
from app.services.goal_creation_service import GoalCreationService
from app.services.goal_intelligence_service import GoalIntelligenceService
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/v1", tags=["goal-intelligence"])


@router.post(
    "/goal-intelligence/interpret",
    response_model=GoalIntelligenceResult,
    summary="Interpret natural language learner goal",
)
async def interpret_goal(
    payload: GoalInterpretationRequest,
    session: AsyncSession = Depends(get_db_session),
) -> GoalIntelligenceResult:
    """Interpret natural language prompt, extract structured goals, and resolve target role & skills."""
    service = GoalIntelligenceService(session=session)
    try:
        return await service.interpret_goal(payload.natural_language_goal)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        ) from err
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during goal interpretation: {str(err)}",
        ) from err


@router.post(
    "/learners/{learner_id}/goals",
    response_model=GoalCreationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create learner goal from natural language",
)
async def create_learner_goal(
    learner_id: UUID,
    payload: GoalInterpretationRequest,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> GoalCreationResponse:
    """Interpret natural language prompt, validate constraints & role resolution, and persist Goal."""
    verify_learner_access(learner_id, current_learner)
    service = GoalCreationService(session=session)
    try:
        response = await service.create_goal_from_natural_language(
            learner_id=learner_id,
            natural_language_goal=payload.natural_language_goal,
        )
        return response
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        ) from err


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)
    experience_level: str | None = Field(default=None, max_length=50)
    preferred_learning_mode: str | None = Field(default=None, max_length=50)
    weekly_availability_hours: float | None = Field(default=None, ge=0, le=168)
    stated_background: str | None = None


@router.get(
    "/learners/{learner_id}/profile",
    summary="Get learner profile and persisted goals",
)
async def get_learner_profile(
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Retrieve authenticated learner identity, profile background metadata, and goals."""
    verify_learner_access(learner_id, current_learner)

    stmt = (
        select(Learner)
        .where(Learner.id == learner_id)
        .options(
            selectinload(Learner.profile),
            selectinload(Learner.goals),
        )
    )
    res = await session.execute(stmt)
    learner = res.scalar_one_or_none()

    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner with identifier '{learner_id}' not found.",
        )

    return {
        "learner_id": str(learner.id),
        "display_name": learner.display_name,
        "email": learner.email,
        "profile": {
            "experience_level": learner.profile.experience_level if learner.profile else None,
            "preferred_learning_mode": learner.profile.preferred_learning_mode
            if learner.profile
            else None,
            "weekly_availability_hours": learner.profile.weekly_availability_hours
            if learner.profile
            else None,
            "stated_background": learner.profile.stated_background if learner.profile else None,
            "profile_metadata": learner.profile.profile_metadata if learner.profile else {},
        }
        if learner.profile
        else None,
        "goals": [
            {
                "goal_id": str(g.id),
                "target_role_id": str(g.target_role_id),
                "objective": g.objective,
                "timeline_weeks": g.timeline_weeks,
                "daily_minutes": g.daily_minutes,
            }
            for g in learner.goals
        ],
    }


@router.put(
    "/learners/{learner_id}/profile",
    summary="Update learner profile and display preferences",
)
async def update_learner_profile(
    learner_id: UUID,
    payload: UpdateProfileRequest,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Update authenticated learner name, experience, availability, and background details in PostgreSQL."""
    verify_learner_access(learner_id, current_learner)

    stmt = (
        select(Learner)
        .where(Learner.id == learner_id)
        .options(
            selectinload(Learner.profile),
            selectinload(Learner.goals),
        )
    )
    res = await session.execute(stmt)
    learner = res.scalar_one_or_none()

    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learner with identifier '{learner_id}' not found.",
        )

    if payload.display_name is not None and payload.display_name.strip():
        new_name = payload.display_name.strip()
        learner.display_name = new_name

        # Update matching UserAccount
        ua_stmt = select(UserAccount).where(UserAccount.learner_id == learner.id)
        ua_res = await session.execute(ua_stmt)
        user_acct = ua_res.scalar_one_or_none()
        if user_acct:
            user_acct.display_name = new_name

    # Update or create LearnerProfile
    if not learner.profile:
        prof = LearnerProfile(learner_id=learner.id)
        session.add(prof)
        learner.profile = prof

    if payload.experience_level is not None:
        learner.profile.experience_level = payload.experience_level.strip()
    if payload.preferred_learning_mode is not None:
        learner.profile.preferred_learning_mode = payload.preferred_learning_mode.strip()
    if payload.weekly_availability_hours is not None:
        learner.profile.weekly_availability_hours = payload.weekly_availability_hours
    if payload.stated_background is not None:
        learner.profile.stated_background = payload.stated_background.strip()

    await session.commit()
    await session.refresh(learner)

    return await get_learner_profile(learner_id, current_learner, session)

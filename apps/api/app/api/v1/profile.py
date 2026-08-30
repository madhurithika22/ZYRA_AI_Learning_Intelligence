from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user_account
from app.core.database import get_db_session
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learner_profile import LearnerProfile
from app.models.skill_mastery import SkillMastery
from app.models.user_account import UserAccount
from app.schemas.profile import (
    LearnerGamificationStats,
    LearnerGoalProgressSummary,
    LearnerProfileDetail,
    LearnerProfileResponse,
    LearnerProfileUpdateRequest,
)
from app.services.learner_gamification_service import LearnerGamificationService

router = APIRouter(prefix="/v1/learners", tags=["learner-profile"])


async def _get_streak_days(session: AsyncSession, learner_id: UUID) -> int:
    """Calculate consecutive daily engagement streak ending today/yesterday."""
    dates: set[datetime.date] = set()

    # 1. Activity attempts
    act_stmt = select(func.date(LearningActivityAttempt.started_at)).where(
        LearningActivityAttempt.learner_id == learner_id
    )
    act_res = await session.execute(act_stmt)
    for d in act_res.scalars():
        if d:
            dates.add(d)

    # 2. Mastery attempts
    m_stmt = select(func.date(MasteryCheckAttempt.started_at)).where(
        MasteryCheckAttempt.learner_id == learner_id
    )
    m_res = await session.execute(m_stmt)
    for d in m_res.scalars():
        if d:
            dates.add(d)

    # 3. Diagnostic responses
    d_stmt = select(func.date(DiagnosticResponse.created_at)).join(
        DiagnosticResponse.session
    ).where(DiagnosticResponse.session.has(learner_id=learner_id))
    d_res = await session.execute(d_stmt)
    for d in d_res.scalars():
        if d:
            dates.add(d)

    # 4. Evidence
    e_stmt = select(func.date(SkillEvidence.created_at)).where(
        SkillEvidence.learner_id == learner_id
    )
    e_res = await session.execute(e_stmt)
    for d in e_res.scalars():
        if d:
            dates.add(d)

    if not dates:
        return 0

    today = datetime.now(timezone.utc).date()
    sorted_dates = sorted(dates, reverse=True)

    streak = 0
    current_check = today

    # If no activity today, check if yesterday had activity
    if current_check not in dates:
        from datetime import timedelta
        current_check = today - timedelta(days=1)

    while current_check in dates:
        streak += 1
        from datetime import timedelta
        current_check -= timedelta(days=1)

    return streak


async def _get_gamification_stats(
    session: AsyncSession, learner_id: UUID, goals_count: int
) -> LearnerGamificationStats:
    """Compute XP, level, evidence count, and achievements based on real database records."""
    # Count completed activities
    act_stmt = select(func.count(LearningActivityAttempt.id)).where(
        LearningActivityAttempt.learner_id == learner_id,
        LearningActivityAttempt.status == "completed",
    )
    act_count = (await session.execute(act_stmt)).scalar() or 0

    # Count passed mastery checks
    mastery_stmt = select(func.count(MasteryCheckAttempt.id)).where(
        MasteryCheckAttempt.learner_id == learner_id,
        MasteryCheckAttempt.is_passed == True,
    )
    mastery_count = (await session.execute(mastery_stmt)).scalar() or 0

    # Count diagnostic responses
    diag_stmt = select(func.count(DiagnosticResponse.id)).join(
        DiagnosticResponse.session
    ).where(DiagnosticResponse.session.has(learner_id=learner_id))
    diag_count = (await session.execute(diag_stmt)).scalar() or 0

    # Count evidence records
    ev_stmt = select(func.count(SkillEvidence.id)).where(
        SkillEvidence.learner_id == learner_id
    )
    evidence_count = (await session.execute(ev_stmt)).scalar() or 0

    # Calculate streak
    streak_days = await _get_streak_days(session, learner_id)

    # XP Calculation: Activity=50, Diagnostic=20, Mastery=100, Evidence=75
    xp = (act_count * 50) + (diag_count * 20) + (mastery_count * 100) + (evidence_count * 75)
    level = 1 + (xp // 250)

    # Achievements
    achievements: list[AchievementBadge] = [
        AchievementBadge(
            id="goal_defined",
            title="Goal Defined",
            description="Established a target career goal and learning path.",
            unlocked=goals_count > 0,
            icon="target",
        ),
        AchievementBadge(
            id="diagnostic_completed",
            title="Diagnostic Evaluated",
            description="Completed baseline diagnostic evaluation to map knowledge gaps.",
            unlocked=diag_count > 0,
            icon="clipboard",
        ),
        AchievementBadge(
            id="first_activity",
            title="First Activity Completed",
            description="Engaged with and completed a curated learning path resource.",
            unlocked=act_count > 0,
            icon="book",
        ),
        AchievementBadge(
            id="first_proof",
            title="First Proof of Mastery",
            description="Successfully passed a mastery check assessment.",
            unlocked=mastery_count > 0,
            icon="award",
        ),
        AchievementBadge(
            id="evidence_collector",
            title="Evidence Collector",
            description="Demonstrated skill mastery backed by verifiable evidence records.",
            unlocked=evidence_count >= 1,
            icon="shield",
        ),
        AchievementBadge(
            id="streak_starter",
            title="Streak Starter",
            description="Maintained daily learning activity engagement.",
            unlocked=streak_days >= 1,
            icon="flame",
        ),
    ]

    return LearnerGamificationStats(
        streak_days=streak_days,
        xp=xp,
        level=level,
        evidence_count=evidence_count,
        achievements=achievements,
    )


async def _get_current_journey(
    session: AsyncSession, learner_id: UUID
) -> LearnerGoalProgressSummary | None:
    """Fetch active goal and compute real goal progress percentage."""
    goal_stmt = (
        select(Goal)
        .options(selectinload(Goal.target_role))
        .where(Goal.learner_id == learner_id)
        .order_by(Goal.created_at.desc())
    )
    goal_res = await session.execute(goal_stmt)
    goal = goal_res.scalars().first()

    if not goal:
        return None

    # Calculate average mastery for this goal's target role skills
    mastery_stmt = select(func.avg(SkillMastery.mastery_score)).where(
        SkillMastery.learner_id == learner_id
    )
    avg_mastery = (await session.execute(mastery_stmt)).scalar()
    progress_pct = round(float(avg_mastery * 100), 1) if avg_mastery is not None else 0.0

    target_role_name = goal.target_role.name if goal.target_role else None

    return LearnerGoalProgressSummary(
        goal_id=str(goal.id),
        target_role=target_role_name,
        progress_percentage=progress_pct,
    )


@router.get(
    "/{learner_id}/profile",
    response_model=LearnerProfileResponse,
    summary="Get comprehensive learner profile with gamification and goal progress",
)
async def get_learner_profile(
    learner_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user_account),
) -> LearnerProfileResponse:
    """Return profile details, preferences, gamification stats, and active journey for learner."""
    # Ensure learner ownership
    if current_user.learner_id != learner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot access another learner's profile.",
        )

    stmt = (
        select(Learner)
        .options(selectinload(Learner.profile), selectinload(Learner.goals))
        .where(Learner.id == learner_id)
    )
    res = await session.execute(stmt)
    learner = res.scalar_one_or_none()

    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner profile not found.",
        )

    goals_count = len(learner.goals) if learner.goals else 0
    gamification = await LearnerGamificationService.compute_gamification_stats(session, learner_id)
    current_journey = await _get_current_journey(session, learner_id)

    raw_meta = learner.profile.profile_metadata if learner.profile and learner.profile.profile_metadata else {}
    gender_val = learner.profile.avatar_gender if learner.profile and learner.profile.avatar_gender else raw_meta.get("gender")

    profile_detail = LearnerProfileDetail(
        experience_level=learner.profile.experience_level if learner.profile else None,
        preferred_learning_mode=learner.profile.preferred_learning_mode if learner.profile else None,
        weekly_availability_hours=learner.profile.weekly_availability_hours if learner.profile else None,
        stated_background=learner.profile.stated_background if learner.profile else None,
        gender=gender_val,
        avatar_gender=learner.profile.avatar_gender if learner.profile else None,
        avatar_variant=learner.profile.avatar_variant if learner.profile else None,
        profile_metadata=learner.profile.profile_metadata if learner.profile else None,
    )

    return LearnerProfileResponse(
        learner_id=str(learner.id),
        display_name=learner.display_name,
        email=learner.email,
        profile=profile_detail,
        gamification=gamification,
        current_journey=current_journey,
        goals_count=goals_count,
    )


@router.put(
    "/{learner_id}/profile",
    response_model=LearnerProfileResponse,
    summary="Update learner display name, profile preferences, and metadata",
)
async def update_learner_profile(
    learner_id: UUID,
    payload: LearnerProfileUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: UserAccount = Depends(get_current_user_account),
) -> LearnerProfileResponse:
    """Update Learner, UserAccount, and LearnerProfile records."""
    if current_user.learner_id != learner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot modify another learner's profile.",
        )

    stmt = (
        select(Learner)
        .options(selectinload(Learner.profile), selectinload(Learner.goals))
        .where(Learner.id == learner_id)
    )
    res = await session.execute(stmt)
    learner = res.scalar_one_or_none()

    if not learner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learner profile not found.",
        )

    # 1. Update Display Name across Learner & UserAccount if provided
    if payload.display_name and payload.display_name.strip():
        clean_name = payload.display_name.strip()
        learner.display_name = clean_name
        current_user.display_name = clean_name

    # 2. Ensure LearnerProfile exists or create
    if not learner.profile:
        learner.profile = LearnerProfile(learner_id=learner.id)
        session.add(learner.profile)

    if payload.experience_level is not None:
        learner.profile.experience_level = payload.experience_level
    if payload.preferred_learning_mode is not None:
        learner.profile.preferred_learning_mode = payload.preferred_learning_mode
    if payload.weekly_availability_hours is not None:
        learner.profile.weekly_availability_hours = payload.weekly_availability_hours
    if payload.stated_background is not None:
        learner.profile.stated_background = payload.stated_background

    # Update avatar_gender and avatar_variant
    if payload.avatar_gender is not None:
        learner.profile.avatar_gender = payload.avatar_gender
    elif payload.gender is not None:
        learner.profile.avatar_gender = payload.gender

    if payload.avatar_variant is not None:
        learner.profile.avatar_variant = payload.avatar_variant

    # Update profile_metadata JSON
    current_meta = dict(learner.profile.profile_metadata or {})
    if payload.gender is not None:
        current_meta["gender"] = payload.gender
    if payload.profile_metadata is not None:
        current_meta.update(payload.profile_metadata)
    learner.profile.profile_metadata = current_meta

    await session.commit()
    await session.refresh(learner)
    if learner.profile:
        await session.refresh(learner.profile)

    return await get_learner_profile(learner_id, session, current_user)

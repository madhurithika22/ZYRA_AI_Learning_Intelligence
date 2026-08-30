from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.diagnostic_session import DiagnosticSession
from app.models.learner import Learner
from app.models.role_skill import RoleSkill
from app.models.goal import Goal
from app.schemas.diagnostic import (
    DiagnosticHistoryItem,
    DiagnosticHistoryResponse,
    DiagnosticQuestionResponse,
    DiagnosticSessionResponse,
    LearnerSkillStateResponse,
    SelfAssessmentRequest,
    StartDiagnosticRequest,
    SubmitResponseRequest,
    SubmitResponseResult,
)
from app.services.diagnostic_service import DiagnosticService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1", tags=["adaptive-diagnostic"])


@router.post(
    "/diagnostics",
    response_model=DiagnosticSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start adaptive diagnostic session",
)
async def start_diagnostic_session(
    payload: StartDiagnosticRequest,
    learner_id: UUID = Query(..., description="ID of learner starting the session"),
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> DiagnosticSessionResponse:
    """Initialize or resume an adaptive diagnostic session for a learner and target goal."""
    verify_learner_access(learner_id, current_learner)
    service = DiagnosticService(session=session)
    try:
        response = await service.start_session(
            learner_id=learner_id,
            goal_id=payload.goal_id,
            max_questions=payload.max_questions,
            force_new=payload.force_new,
        )
        return response
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.get(
    "/learners/{learner_id}/diagnostics/latest",
    response_model=DiagnosticSessionResponse | None,
    summary="Get latest diagnostic session for learner",
)
async def get_latest_diagnostic_session(
    learner_id: UUID,
    goal_id: UUID = Query(..., description="Target goal ID"),
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> DiagnosticSessionResponse | None:
    """Retrieve the most recent diagnostic session for a learner and goal."""
    verify_learner_access(learner_id, current_learner)
    stmt = (
        select(DiagnosticSession)
        .where(
            DiagnosticSession.learner_id == learner_id,
            DiagnosticSession.goal_id == goal_id,
        )
        .order_by(DiagnosticSession.started_at.desc(), DiagnosticSession.created_at.desc())
    )
    res = await session.execute(stmt)
    diag_obj = res.scalars().first()
    if not diag_obj:
        return None
    service = DiagnosticService(session=session)
    return service._to_session_response(diag_obj)


@router.get(
    "/learners/{learner_id}/diagnostics/history",
    response_model=DiagnosticHistoryResponse,
    summary="Retrieve diagnostic session history for learner",
)
async def get_diagnostic_history(
    learner_id: UUID,
    goal_id: UUID = Query(..., description="Target goal ID"),
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> DiagnosticHistoryResponse:
    """Retrieve all historical diagnostic sessions for a learner and goal."""
    verify_learner_access(learner_id, current_learner)
    goal = await session.get(Goal, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal '{goal_id}' not found.",
        )

    # Count role skills for the goal
    skills_cnt_stmt = select(func.count(RoleSkill.skill_id)).where(RoleSkill.role_id == goal.target_role_id)
    skills_cnt = (await session.execute(skills_cnt_stmt)).scalar() or 0

    stmt = (
        select(DiagnosticSession)
        .where(
            DiagnosticSession.learner_id == learner_id,
            DiagnosticSession.goal_id == goal_id,
        )
        .order_by(DiagnosticSession.started_at.desc())
    )
    res = await session.execute(stmt)
    sessions = res.scalars().all()

    history_items = [
        DiagnosticHistoryItem(
            session_id=s.id,
            started_at=s.started_at,
            completed_at=s.completed_at,
            status=s.status,
            question_count=s.question_count,
            skills_count=skills_cnt,
            termination_reason=s.session_metadata.get("termination_reason") if s.session_metadata else None,
        )
        for s in sessions
    ]

    return DiagnosticHistoryResponse(
        learner_id=learner_id,
        goal_id=goal_id,
        history=history_items,
    )


@router.get(
    "/diagnostics/{diagnostic_id}",
    response_model=DiagnosticSessionResponse,
    summary="Get diagnostic session status",
)
async def get_diagnostic_session(
    diagnostic_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> DiagnosticSessionResponse:
    """Retrieve current state and question progress for a diagnostic session."""
    diag_stmt = select(DiagnosticSession).where(DiagnosticSession.id == diagnostic_id)
    diag_res = await session.execute(diag_stmt)
    diag_obj = diag_res.scalar_one_or_none()
    if not diag_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic session '{diagnostic_id}' not found.",
        )
    verify_learner_access(diag_obj.learner_id, current_learner)

    service = DiagnosticService(session=session)
    try:
        return await service.get_session(diagnostic_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.post(
    "/diagnostics/{diagnostic_id}/self-assessment",
    response_model=DiagnosticSessionResponse,
    summary="Record pre-diagnostic self-assessment ratings",
)
async def submit_self_assessment(
    diagnostic_id: UUID,
    payload: SelfAssessmentRequest,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> DiagnosticSessionResponse:
    """Record prior self-assessment ratings into session metadata."""
    diag_stmt = select(DiagnosticSession).where(DiagnosticSession.id == diagnostic_id)
    diag_res = await session.execute(diag_stmt)
    diag_obj = diag_res.scalar_one_or_none()
    if not diag_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic session '{diagnostic_id}' not found.",
        )
    verify_learner_access(diag_obj.learner_id, current_learner)

    meta = dict(diag_obj.session_metadata or {})
    meta["self_assessment_priors"] = payload.ratings
    diag_obj.session_metadata = meta
    await session.commit()
    await session.refresh(diag_obj)

    service = DiagnosticService(session=session)
    return service._to_session_response(diag_obj)


@router.post(
    "/diagnostics/{diagnostic_id}/next-question",
    response_model=DiagnosticQuestionResponse | None,
    summary="Select next adaptive diagnostic question",
)
async def get_next_diagnostic_question(
    diagnostic_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> DiagnosticQuestionResponse | None:
    """Select the next optimal question based on information gain, difficulty fit, and novelty."""
    diag_stmt = select(DiagnosticSession).where(DiagnosticSession.id == diagnostic_id)
    diag_res = await session.execute(diag_stmt)
    diag_obj = diag_res.scalar_one_or_none()
    if not diag_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic session '{diagnostic_id}' not found.",
        )
    verify_learner_access(diag_obj.learner_id, current_learner)

    service = DiagnosticService(session=session)
    try:
        return await service.select_next_question(diagnostic_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err


@router.post(
    "/diagnostics/{diagnostic_id}/responses",
    response_model=SubmitResponseResult,
    summary="Submit answer for evaluation and mastery update",
)
async def submit_diagnostic_response(
    diagnostic_id: UUID,
    payload: SubmitResponseRequest,
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> SubmitResponseResult:
    """Evaluate response transactionally, persist evidence, update mastery, and advance session."""
    diag_stmt = select(DiagnosticSession).where(DiagnosticSession.id == diagnostic_id)
    diag_res = await session.execute(diag_stmt)
    diag_obj = diag_res.scalar_one_or_none()
    if not diag_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic session '{diagnostic_id}' not found.",
        )
    verify_learner_access(diag_obj.learner_id, current_learner)

    service = DiagnosticService(session=session)
    try:
        result = await service.submit_response(
            session_id=diagnostic_id,
            idempotency_key=payload.idempotency_key,
            question_id=payload.question_id,
            learner_answer=payload.learner_answer,
        )
        return result
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        ) from err


@router.get(
    "/learners/{learner_id}/skill-state",
    response_model=LearnerSkillStateResponse,
    summary="Retrieve current Learning Twin skill state",
)
async def get_learner_skill_state(
    learner_id: UUID,
    goal_id: UUID = Query(..., description="Target goal ID"),
    current_learner: Learner = Depends(get_current_learner),
    session: AsyncSession = Depends(get_db_session),
) -> LearnerSkillStateResponse:
    """Retrieve learner's current estimated mastery and confidence state across target role skills."""
    verify_learner_access(learner_id, current_learner)
    service = DiagnosticService(session=session)
    try:
        return await service.get_learner_skill_state(learner_id=learner_id, goal_id=goal_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        ) from err

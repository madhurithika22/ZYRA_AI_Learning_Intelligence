from typing import Any
from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.learner import Learner
from app.schemas.proof_of_mastery import (
    ActivityAttemptResponse,
    CompleteActivityRequest,
    ProofOfMasteryOutcomeResponse,
    SaveDraftActivityRequest,
    StartActivityRequest,
)
from app.services.proof_of_mastery_service import ProofOfMasteryService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/learning-activities", tags=["learning-activities"])


@router.post("/{path_node_id}/start", response_model=ActivityAttemptResponse)
async def start_learning_activity(
    path_node_id: UUID,
    req: StartActivityRequest,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> ActivityAttemptResponse:
    """Start an attempt for a learning path node activity."""
    verify_learner_access(req.learner_id, current_learner)
    service = ProofOfMasteryService(db)
    try:
        return await service.start_activity_attempt(
            learner_id=req.learner_id,
            learning_path_node_id=path_node_id,
            idempotency_key=req.idempotency_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{attempt_id}/save-draft", response_model=ActivityAttemptResponse)
async def save_activity_draft(
    attempt_id: UUID,
    req: SaveDraftActivityRequest,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> ActivityAttemptResponse:
    """Save draft submission data for a learning activity attempt without completing it."""
    verify_learner_access(req.learner_id, current_learner)
    service = ProofOfMasteryService(db)
    try:
        return await service.save_activity_draft(
            learner_id=req.learner_id,
            attempt_id=attempt_id,
            submission_data=req.submission_data,
            idempotency_key=req.idempotency_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{attempt_id}/complete", response_model=ActivityAttemptResponse)
async def complete_learning_activity(
    attempt_id: UUID,
    req: CompleteActivityRequest,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> ActivityAttemptResponse:
    """Mark a learning activity attempt as completed. Note: SkillMastery remains unchanged until post-learning assessment."""
    verify_learner_access(req.learner_id, current_learner)
    service = ProofOfMasteryService(db)
    try:
        return await service.complete_activity_attempt(
            learner_id=req.learner_id,
            attempt_id=attempt_id,
            time_spent_minutes=req.time_spent_minutes,
            completion_percentage=req.completion_percentage,
            submission_data=req.submission_data,
            idempotency_key=req.idempotency_key,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e



@router.get("/latest-attempt", response_model=ActivityAttemptResponse | None)
async def get_latest_activity_attempt(
    learner_id: UUID,
    node_id: UUID | None = None,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> ActivityAttemptResponse | None:
    """Retrieve the most recent learning activity attempt for a learner and optional path node."""
    verify_learner_access(learner_id, current_learner)
    from app.models.learning_activity_attempt import LearningActivityAttempt
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    stmt = (
        select(LearningActivityAttempt)
        .where(LearningActivityAttempt.learner_id == learner_id)
        .options(selectinload(LearningActivityAttempt.resource))
    )
    if node_id:
        stmt = stmt.where(LearningActivityAttempt.learning_path_node_id == node_id)
    stmt = stmt.order_by(LearningActivityAttempt.started_at.desc())
    res = await db.execute(stmt)
    attempt = res.scalars().first()
    if not attempt:
        return None
    service = ProofOfMasteryService(db)
    return service._to_activity_response(attempt)


@router.get("/active-attempt", response_model=dict[str, Any])
async def get_active_activity_attempt(
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Resolves the current active learning activity attempt (or active path node) for the authenticated learner."""
    from app.models.learning_activity_attempt import LearningActivityAttempt
    from app.models.learning_path import LearningPath
    from app.models.learning_path_node import LearningPathNode
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # 1. Check latest attempt for authenticated learner
    attempt_stmt = (
        select(LearningActivityAttempt)
        .where(LearningActivityAttempt.learner_id == current_learner.id)
        .options(
            selectinload(LearningActivityAttempt.resource),
            selectinload(LearningActivityAttempt.learning_path_node).selectinload(LearningPathNode.skill),
        )
        .order_by(LearningActivityAttempt.started_at.desc())
    )
    attempt = (await db.execute(attempt_stmt)).scalars().first()

    if attempt:
        service = ProofOfMasteryService(db)
        resp = service._to_activity_response(attempt)
        return {
            "attempt": resp.model_dump(mode="json"),
            "node_id": str(attempt.learning_path_node_id),
            "skill_name": attempt.learning_path_node.skill.name if attempt.learning_path_node and attempt.learning_path_node.skill else "Docker",
        }

    # 2. If no attempt exists yet, find active/draft learning path & first node (prioritizing 'active')
    path_stmt = (
        select(LearningPath)
        .where(
            LearningPath.learner_id == current_learner.id,
            LearningPath.status.in_(["active", "draft"]),
        )
        .options(
            selectinload(LearningPath.nodes).selectinload(LearningPathNode.skill),
            selectinload(LearningPath.nodes).selectinload(LearningPathNode.resource),
        )
        .order_by(
            (LearningPath.status == "active").desc(),
            LearningPath.updated_at.desc(),
        )
    )
    path = (await db.execute(path_stmt)).scalars().first()

    if path and path.nodes:
        first_node = path.nodes[0]
        return {
            "attempt": None,
            "node_id": str(first_node.id),
            "skill_name": first_node.skill.name if first_node.skill else "Docker",
            "resource_title": first_node.resource.title if first_node.resource else "Hands-on Learning Activity",
        }

    # 3. If no path exists, check learner's goals and generate paths automatically
    from app.models.goal import Goal
    goal_stmt = select(Goal).where(Goal.learner_id == current_learner.id).order_by(Goal.created_at.desc())
    goal = (await db.execute(goal_stmt)).scalars().first()

    if goal:
        from app.services.learning_path_service import LearningPathService
        lp_service = LearningPathService(db)
        try:
            comparison = await lp_service.generate_candidate_paths(current_learner.id, goal.id)
            if comparison and comparison.options:
                opt = list(comparison.options.values())[0]
                if opt.nodes:
                    first_n = opt.nodes[0]
                    return {
                        "attempt": None,
                        "node_id": str(first_n.id),
                        "skill_name": first_n.skill_name or "Docker",
                        "resource_title": first_n.resource_title or "Hands-on Learning Activity",
                    }
        except Exception:
            pass

    return {
        "attempt": None,
        "node_id": None,
        "skill_name": "Docker",
    }




@router.get("/{attempt_id}", response_model=ActivityAttemptResponse)
async def get_learning_activity_attempt(
    attempt_id: UUID,
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> ActivityAttemptResponse:
    """Fetch details for a learning activity attempt."""
    verify_learner_access(learner_id, current_learner)
    service = ProofOfMasteryService(db)
    try:
        return await service.get_activity_attempt(attempt_id, learner_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/{attempt_id}/outcome", response_model=ProofOfMasteryOutcomeResponse)
async def get_learning_activity_outcome(
    attempt_id: UUID,
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> ProofOfMasteryOutcomeResponse:
    """Fetch measured proof-of-mastery outcome for a completed activity attempt."""
    verify_learner_access(learner_id, current_learner)
    service = ProofOfMasteryService(db)
    try:
        return await service.get_attempt_outcome(learner_id, attempt_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

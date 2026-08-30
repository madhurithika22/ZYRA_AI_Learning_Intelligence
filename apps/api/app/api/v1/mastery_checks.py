from uuid import UUID

from app.api.dependencies import get_current_learner, verify_learner_access
from app.core.database import get_db_session
from app.models.learner import Learner
from app.schemas.proof_of_mastery import (
    ProofOfMasteryOutcomeResponse,
    StartMasteryCheckResponse,
    SubmitMasteryCheckRequest,
)
from app.services.proof_of_mastery_service import ProofOfMasteryService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/v1/mastery-checks", tags=["mastery-checks"])


@router.post("/{activity_attempt_id}/start", response_model=StartMasteryCheckResponse)
async def start_mastery_check(
    activity_attempt_id: UUID,
    learner_id: UUID,
    idempotency_key: str | None = None,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> StartMasteryCheckResponse:
    """Start a post-learning proof-of-mastery check for a completed learning activity."""
    verify_learner_access(learner_id, current_learner)
    service = ProofOfMasteryService(db)
    try:
        return await service.start_mastery_check(
            learner_id=learner_id,
            activity_attempt_id=activity_attempt_id,
            idempotency_key=idempotency_key,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg) from e
        if "does not own" in msg.lower():
            raise HTTPException(status_code=403, detail=msg) from e
        raise HTTPException(status_code=400, detail=msg) from e


@router.post("/{check_id}/submit", response_model=ProofOfMasteryOutcomeResponse)
async def submit_mastery_check(
    check_id: UUID,
    req: SubmitMasteryCheckRequest,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> ProofOfMasteryOutcomeResponse:
    """Submit post-learning assessment answers, evaluate evidence, update MasteryEngine, and return measured outcomes."""
    verify_learner_access(req.learner_id, current_learner)
    service = ProofOfMasteryService(db)
    try:
        return await service.submit_mastery_check(
            learner_id=req.learner_id,
            check_id=check_id,
            answers=req.answers,
            idempotency_key=req.idempotency_key,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg) from e
        if "does not own" in msg.lower():
            raise HTTPException(status_code=403, detail=msg) from e
        raise HTTPException(status_code=400, detail=msg) from e


@router.get("/active", response_model=StartMasteryCheckResponse | None)
async def get_active_mastery_check(
    activity_attempt_id: UUID,
    learner_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> StartMasteryCheckResponse | None:
    """Fetch active or recent mastery check session for a given activity attempt."""
    verify_learner_access(learner_id, current_learner)
    service = ProofOfMasteryService(db)
    return await service.get_active_mastery_check(
        learner_id=learner_id,
        activity_attempt_id=activity_attempt_id,
    )


@router.get("/{check_id}", response_model=dict)
async def get_mastery_check_by_id(
    check_id: UUID,
    current_learner: Learner = Depends(get_current_learner),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Fetch canonical database MasteryCheckAttempt object by primary key."""
    from app.models.mastery_check_attempt import MasteryCheckAttempt
    check = await db.get(MasteryCheckAttempt, check_id)
    if not check:
        raise HTTPException(status_code=404, detail=f"Mastery check attempt '{check_id}' not found.")
    verify_learner_access(check.learner_id, current_learner)
    return {
        "id": str(check.id),
        "learner_id": str(check.learner_id),
        "activity_attempt_id": str(check.activity_attempt_id),
        "learning_path_node_id": str(check.learning_path_node_id),
        "status": check.status,
        "started_at": check.started_at.isoformat() if check.started_at else None,
        "completed_at": check.completed_at.isoformat() if check.completed_at else None,
        "attempt_number": check.attempt_number,
    }

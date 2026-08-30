from uuid import uuid4

import pytest
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learning_path import LearningPath
from app.schemas.learning_twin import TwinConfidenceLevel, TwinFreshnessStatus
from app.services.learning_path_service import LearningPathService
from app.services.learning_twin_service import LearningTwinService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _ensure_active_path(db_session: AsyncSession, learner_id, goal_id) -> LearningPath:
    path_stmt = select(LearningPath).where(
        LearningPath.learner_id == learner_id,
        LearningPath.goal_id == goal_id,
        LearningPath.status == "active",
    )
    active_path = (await db_session.execute(path_stmt)).scalars().first()

    if not active_path:
        path_service = LearningPathService(db_session)
        path_resp = await path_service.generate_candidate_paths(learner_id, goal_id)
        fastest_path_id = path_resp.options["FASTEST"].path_id
        await path_service.activate_path(fastest_path_id, learner_id)
        active_path = (await db_session.execute(path_stmt)).scalars().first()

    return active_path


@pytest.mark.asyncio
async def test_get_learning_twin_success(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    goal = (await db_session.execute(select(Goal).where(Goal.learner_id == alex.id).order_by(Goal.created_at.desc()))).scalars().first()
    await _ensure_active_path(db_session, alex.id, goal.id)

    service = LearningTwinService(db_session)
    twin = await service.get_learning_twin(alex.id, include_trace=True)

    assert twin.learner_id == alex.id
    assert twin.goal.goal_id == goal.id
    assert twin.goal.target_role_name == "ML Engineer"
    assert twin.state_completeness >= 0.80
    assert twin.state_confidence.level == TwinConfidenceLevel.HIGH
    assert twin.freshness.status in (TwinFreshnessStatus.FRESH, TwinFreshnessStatus.STALE)
    assert twin.decision_trace is not None
    assert twin.bottleneck is not None
    assert twin.next_action is not None
    assert twin.path is not None


@pytest.mark.asyncio
async def test_get_learning_twin_no_goal(db_session: AsyncSession) -> None:
    new_learner = Learner(display_name="Test No Goal", email=f"no.goal.{uuid4().hex[:6]}@example.com")
    db_session.add(new_learner)
    await db_session.flush()

    service = LearningTwinService(db_session)
    twin = await service.get_learning_twin(new_learner.id, include_trace=False)

    assert twin.learner_id == new_learner.id
    assert twin.goal.objective == "No Goal Set"
    assert twin.state_confidence.level == TwinConfidenceLevel.LOW
    assert twin.state_completeness == 0.20
    assert twin.path is None
    assert twin.bottleneck is None
    assert twin.next_action is None


@pytest.mark.asyncio
async def test_get_learning_twin_nonexistent_learner(db_session: AsyncSession) -> None:
    service = LearningTwinService(db_session)
    fake_id = uuid4()
    with pytest.raises(ValueError, match="not found"):
        await service.get_learning_twin(fake_id)


@pytest.mark.asyncio
async def test_learning_twin_determinism(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    goal = (await db_session.execute(select(Goal).where(Goal.learner_id == alex.id).order_by(Goal.created_at.desc()))).scalars().first()
    await _ensure_active_path(db_session, alex.id, goal.id)

    service = LearningTwinService(db_session)
    twin1 = await service.get_learning_twin(alex.id, include_trace=True)
    twin2 = await service.get_learning_twin(alex.id, include_trace=True)

    assert twin1.goal.goal_skill_progress == twin2.goal.goal_skill_progress
    assert twin1.state_completeness == twin2.state_completeness
    assert twin1.bottleneck.skill_name == twin2.bottleneck.skill_name if twin1.bottleneck and twin2.bottleneck else True
    assert twin1.next_action.title == twin2.next_action.title if twin1.next_action and twin2.next_action else True

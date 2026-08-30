import pytest
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learning_path import LearningPath
from app.schemas.replanning import ReplanTriggerType
from app.services.learning_path_service import LearningPathService
from app.services.replanning_service import ReplanningService
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
async def test_replan_status_fresh_path(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    goal = (await db_session.execute(select(Goal).where(Goal.learner_id == alex.id).order_by(Goal.created_at.desc()))).scalars().first()
    await _ensure_active_path(db_session, alex.id, goal.id)

    service = ReplanningService(db_session)
    status_resp = await service.get_replan_status(alex.id, goal.id)

    assert status_resp.learner_id == alex.id
    assert status_resp.goal_id == goal.id
    assert status_resp.current_path_version >= 1
    assert status_resp.staleness_score >= 0.0


@pytest.mark.asyncio
async def test_generate_and_accept_replan_lifecycle(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    goal = (await db_session.execute(select(Goal).where(Goal.learner_id == alex.id).order_by(Goal.created_at.desc()))).scalars().first()
    await _ensure_active_path(db_session, alex.id, goal.id)

    service = ReplanningService(db_session)
    decision = await service.generate_replan(alex.id, goal.id, manual_trigger=True)

    assert decision.should_replan is True
    assert decision.trigger_type == ReplanTriggerType.MANUAL_REPLAN
    assert decision.draft_path_id is not None
    assert decision.path_delta is not None

    draft_id = decision.draft_path_id
    accepted = await service.accept_replan(draft_id)

    assert accepted.path_id == draft_id
    assert accepted.status == "active"

    # Verify parent path is superseded
    parent = (await db_session.execute(select(LearningPath).where(LearningPath.id == accepted.parent_path_id))).scalar_one()
    assert parent.status == "superseded"


@pytest.mark.asyncio
async def test_reject_replan_lifecycle(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    goal = (await db_session.execute(select(Goal).where(Goal.learner_id == alex.id).order_by(Goal.created_at.desc()))).scalars().first()
    await _ensure_active_path(db_session, alex.id, goal.id)

    service = ReplanningService(db_session)
    decision = await service.generate_replan(alex.id, goal.id, manual_trigger=True)
    draft_id = decision.draft_path_id

    rejected = await service.reject_replan(draft_id)
    assert rejected.path_id == draft_id
    assert rejected.status == "rejected"

    parent = (await db_session.execute(select(LearningPath).where(LearningPath.id == rejected.parent_path_id))).scalar_one()
    assert parent.status == "active"

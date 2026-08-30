import pytest
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learning_path_node import LearningPathNode
from app.schemas.next_action import ActionType
from app.services.learning_path_service import LearningPathService
from app.services.next_action_service import NextActionService
from app.services.proof_of_mastery_service import ProofOfMasteryService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_next_action_service_baseline(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    goal = (await db_session.execute(select(Goal).where(Goal.learner_id == alex.id).order_by(Goal.created_at.desc()))).scalars().first()

    service = NextActionService(db_session)
    response = await service.get_next_action(alex.id, goal.id)

    assert response.learner_id == alex.id
    assert response.selected_action is not None
    assert response.selected_action.score > 0.0
    assert response.action_confidence >= 0.40
    assert response.confidence_label in ("HIGH", "MEDIUM", "LOW")
    assert isinstance(response.alternatives, list)


@pytest.mark.asyncio
async def test_next_action_unproven_activity_favors_mastery_check(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    goal = (await db_session.execute(select(Goal).where(Goal.learner_id == alex.id).order_by(Goal.created_at.desc()))).scalars().first()

    path_service = LearningPathService(db_session)
    path_resp = await path_service.generate_candidate_paths(alex.id, goal.id)
    fastest_path_id = path_resp.options["FASTEST"].path_id
    await path_service.activate_path(fastest_path_id, alex.id)

    nodes = (await db_session.execute(
        select(LearningPathNode).where(LearningPathNode.learning_path_id == fastest_path_id).order_by(LearningPathNode.sequence)
    )).scalars().all()
    target_node = nodes[0]

    pom_service = ProofOfMasteryService(db_session)
    att = await pom_service.start_activity_attempt(alex.id, target_node.id)
    await pom_service.complete_activity_attempt(alex.id, att.id, time_spent_minutes=30)

    service = NextActionService(db_session)
    response = await service.get_next_action(alex.id, goal.id)

    assert response.selected_action.action_type in (ActionType.MASTERY_CHECK, ActionType.REASSESS)
    assert any(kw in response.selected_action.primary_reason.lower() for kw in ["activity", "proof", "mastery", "reassess", "check"])


@pytest.mark.asyncio
async def test_next_action_candidates_list(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    goal = (await db_session.execute(select(Goal).where(Goal.learner_id == alex.id).order_by(Goal.created_at.desc()))).scalars().first()

    service = NextActionService(db_session)
    candidates_resp = await service.get_action_candidates(alex.id, goal.id)

    assert candidates_resp.learner_id == alex.id
    assert len(candidates_resp.candidates) > 0
    # Verify rankings are ordered by score desc
    scores = [c.score for c in candidates_resp.candidates]
    assert scores == sorted(scores, reverse=True)

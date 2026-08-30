import pytest
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learning_path_node import LearningPathNode
from app.models.role import Role
from app.models.skill_mastery import SkillMastery
from app.services.learning_path_service import LearningPathService
from app.services.proof_of_mastery_service import ProofOfMasteryService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_completion_is_not_mastery(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    ai_role = (await db_session.execute(select(Role).where(Role.name == "AI Engineer"))).scalar_one()
    alex_goal = (await db_session.execute(select(Goal).where(Goal.learner_id == alex.id, Goal.target_role_id == ai_role.id))).scalar_one()

    path_service = LearningPathService(db_session)
    path_resp = await path_service.generate_candidate_paths(alex.id, alex_goal.id)
    fastest_path_id = path_resp.options["FASTEST"].path_id
    await path_service.activate_path(fastest_path_id, alex.id)

    nodes = (await db_session.execute(
        select(LearningPathNode).where(LearningPathNode.learning_path_id == fastest_path_id).order_by(LearningPathNode.sequence)
    )).scalars().all()
    target_node = nodes[0]

    sm_before = (await db_session.execute(
        select(SkillMastery).where(SkillMastery.learner_id == alex.id, SkillMastery.skill_id == target_node.skill_id)
    )).scalar_one_or_none()
    m_before = sm_before.mastery_score if sm_before else 0.0

    service = ProofOfMasteryService(db_session)
    start_att = await service.start_activity_attempt(alex.id, target_node.id)
    comp_att = await service.complete_activity_attempt(alex.id, start_att.id, time_spent_minutes=30)

    assert comp_att.status == "completed"

    sm_after = (await db_session.execute(
        select(SkillMastery).where(SkillMastery.learner_id == alex.id, SkillMastery.skill_id == target_node.skill_id)
    )).scalar_one_or_none()
    m_after = sm_after.mastery_score if sm_after else 0.0

    # Critical requirement: completion alone MUST NOT change mastery
    assert m_before == m_after


@pytest.mark.asyncio
async def test_mastery_check_lifecycle_and_api(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    ai_role = (await db_session.execute(select(Role).where(Role.name == "AI Engineer"))).scalar_one()
    alex_goal = (await db_session.execute(select(Goal).where(Goal.learner_id == alex.id, Goal.target_role_id == ai_role.id))).scalar_one()

    path_service = LearningPathService(db_session)
    path_resp = await path_service.generate_candidate_paths(alex.id, alex_goal.id)
    fastest_path_id = path_resp.options["FASTEST"].path_id
    await path_service.activate_path(fastest_path_id, alex.id)

    nodes = (await db_session.execute(
        select(LearningPathNode).where(LearningPathNode.learning_path_id == fastest_path_id).order_by(LearningPathNode.sequence)
    )).scalars().all()
    target_node = nodes[0]

    service = ProofOfMasteryService(db_session)
    start_att = await service.start_activity_attempt(alex.id, target_node.id)
    comp_att = await service.complete_activity_attempt(alex.id, start_att.id)

    check_resp = await service.start_mastery_check(alex.id, comp_att.id)
    assert check_resp.status == "started"
    assert len(check_resp.questions) > 0

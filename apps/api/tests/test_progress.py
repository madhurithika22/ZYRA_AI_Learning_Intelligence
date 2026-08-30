import pytest
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learning_path_node import LearningPathNode
from app.models.role import Role
from app.services.learning_path_service import LearningPathService
from app.services.progress_service import ProgressService
from app.services.proof_of_mastery_service import ProofOfMasteryService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_progress_service_path_and_skills(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    ai_role = (await db_session.execute(select(Role).where(Role.name == "AI Engineer"))).scalar_one()
    goal = (await db_session.execute(select(Goal).where(Goal.learner_id == alex.id, Goal.target_role_id == ai_role.id))).scalars().first()

    path_service = LearningPathService(db_session)
    path_resp = await path_service.generate_candidate_paths(alex.id, goal.id)
    fastest_path_id = path_resp.options["FASTEST"].path_id
    await path_service.activate_path(fastest_path_id, alex.id)

    nodes = (await db_session.execute(
        select(LearningPathNode).where(LearningPathNode.learning_path_id == fastest_path_id).order_by(LearningPathNode.sequence)
    )).scalars().all()
    target_node = nodes[0]

    prog_service = ProgressService(db_session)
    pom_service = ProofOfMasteryService(db_session)

    # 1. Check path progress before activity
    path_p_before = await prog_service.get_path_progress(alex.id, fastest_path_id)
    assert path_p_before.completed_nodes == 0

    # 2. Complete activity attempt
    att = await pom_service.start_activity_attempt(alex.id, target_node.id)
    await pom_service.complete_activity_attempt(alex.id, att.id, time_spent_minutes=30)

    # 3. Path progress increases, mastery unchanged
    path_p_after = await prog_service.get_path_progress(alex.id, fastest_path_id)
    assert path_p_after.completed_nodes == 1
    assert path_p_after.completion_percentage > 0.0

    # 4. Full Summary
    summary = await prog_service.get_learner_progress_summary(alex.id)
    assert summary.learner_id == alex.id
    assert len(summary.skills_progress) > 0


@pytest.mark.asyncio
async def test_skill_history(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
    prog_service = ProgressService(db_session)
    summary = await prog_service.get_learner_progress_summary(alex.id)
    target_skill_id = summary.skills_progress[0].skill_id

    history = await prog_service.get_skill_history(alex.id, target_skill_id)
    assert isinstance(history, list)

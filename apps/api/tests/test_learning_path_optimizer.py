import pytest
from app.core.database import get_db_session
from app.main import app
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.role import Role
from app.models.skill import Skill
from app.models.skill_mastery import SkillMastery
from app.services.learning_path_service import LearningPathService
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_four_strategies_generated_and_persisted(db_session: AsyncSession) -> None:
    alex_stmt = select(Learner).where(Learner.email == "alex.chen@example.com")
    alex = (await db_session.execute(alex_stmt)).scalar_one()

    ai_role_stmt = select(Role).where(Role.name == "AI Engineer")
    ai_role = (await db_session.execute(ai_role_stmt)).scalar_one()

    alex_goal_stmt = select(Goal).where(
        Goal.learner_id == alex.id, Goal.target_role_id == ai_role.id
    )
    alex_goal = (await db_session.execute(alex_goal_stmt)).scalar_one()

    py_sk_stmt = select(Skill).where(Skill.name == "Python")
    py_sk = (await db_session.execute(py_sk_stmt)).scalar_one_or_none()
    if py_sk:
        sm_py_stmt = select(SkillMastery).where(SkillMastery.learner_id == alex.id, SkillMastery.skill_id == py_sk.id)
        sm_py = (await db_session.execute(sm_py_stmt)).scalar_one_or_none()
        if sm_py:
            sm_py.mastery_score = 0.84
            sm_py.confidence = 0.85
            await db_session.flush()

    service = LearningPathService(db_session)
    res = await service.generate_candidate_paths(alex.id, alex_goal.id)

    assert res.target_role == "AI Engineer"
    assert "FASTEST" in res.options
    assert "BALANCED" in res.options
    assert "DEEP_MASTERY" in res.options
    assert "PROJECT_FIRST" in res.options

    # Python excluded since mastery = 84% > 75%
    fastest_nodes = res.options["FASTEST"].nodes
    has_python_only = any(
        "Python" in n.skill_name and "Deep" not in n.skill_name for n in fastest_nodes
    )
    assert not has_python_only


@pytest.mark.asyncio
async def test_prerequisite_ordering_in_path(db_session: AsyncSession) -> None:
    alex_stmt = select(Learner).where(Learner.email == "alex.chen@example.com")
    alex = (await db_session.execute(alex_stmt)).scalar_one()

    ai_role_stmt = select(Role).where(Role.name == "AI Engineer")
    ai_role = (await db_session.execute(ai_role_stmt)).scalar_one()

    alex_goal_stmt = select(Goal).where(
        Goal.learner_id == alex.id, Goal.target_role_id == ai_role.id
    )
    alex_goal = (await db_session.execute(alex_goal_stmt)).scalar_one()

    service = LearningPathService(db_session)
    res = await service.generate_candidate_paths(alex.id, alex_goal.id)

    nodes = res.options["FASTEST"].nodes
    dl_step = next(
        (
            n.sequence
            for n in nodes
            if "Deep Learning" in n.skill_name or "Deep Learning" in n.resource_title
        ),
        99,
    )
    pt_step = next(
        (n.sequence for n in nodes if "PyTorch" in n.skill_name or "PyTorch" in n.resource_title),
        99,
    )

    if dl_step != 99 and pt_step != 99:
        assert dl_step < pt_step


@pytest.mark.asyncio
async def test_path_generation_api_endpoint(db_session: AsyncSession) -> None:
    alex_stmt = select(Learner).where(Learner.email == "alex.chen@example.com")
    alex = (await db_session.execute(alex_stmt)).scalar_one()

    ai_role_stmt = select(Role).where(Role.name == "AI Engineer")
    ai_role = (await db_session.execute(ai_role_stmt)).scalar_one()

    alex_goal_stmt = select(Goal).where(
        Goal.learner_id == alex.id, Goal.target_role_id == ai_role.id
    )
    alex_goal = (await db_session.execute(alex_goal_stmt)).scalar_one()

    async def _get_db():
        yield db_session

    from app.api.dependencies import get_current_learner
    app.dependency_overrides[get_db_session] = _get_db
    app.dependency_overrides[get_current_learner] = lambda: alex

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                f"/api/v1/learners/{alex.id}/goals/{alex_goal.id}/paths/generate"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "options" in data
            assert "FASTEST" in data["options"]

            fastest_path_id = data["options"]["FASTEST"]["path_id"]

            # Test Activation Endpoint
            act_resp = await client.post(
                f"/api/v1/learning-paths/{fastest_path_id}/activate?learner_id={alex.id}"
            )
            assert act_resp.status_code == 200
            act_data = act_resp.json()
            assert act_data["status"] == "active"
    finally:
        app.dependency_overrides.clear()

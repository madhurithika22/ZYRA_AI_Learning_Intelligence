from uuid import uuid4

import pytest
from app.main import app
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.role import Role
from app.models.role_skill import RoleSkill
from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence
from app.models.skill_mastery import SkillMastery
from app.models.skill_relation import SkillRelation
from app.services.bottleneck_analysis import BottleneckAnalysisService
from app.services.dependency_impact import DependencyImpactService
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_gap_calculation_and_normalization(db_session: AsyncSession) -> None:
    learner = Learner(display_name="Gap Learner", email=f"gap_{uuid4().hex[:6]}@example.com")
    role = Role(name=f"Gap Role {uuid4().hex[:4]}")
    skill = Skill(name=f"Gap Skill {uuid4().hex[:4]}", difficulty=2.0)
    db_session.add_all([learner, role, skill])
    await db_session.flush()

    # required_level = 4.0 on 1.0-5.0 scale -> normalized = 0.75
    rs = RoleSkill(role_id=role.id, skill_id=skill.id, importance=0.8, required_level=4.0)
    goal = Goal(learner_id=learner.id, target_role_id=role.id, objective="Gap Goal")
    db_session.add_all([rs, goal])
    await db_session.flush()

    mastery = SkillMastery(
        learner_id=learner.id, skill_id=skill.id, mastery_score=0.25, confidence=0.80
    )
    db_session.add(mastery)
    await db_session.flush()

    service = BottleneckAnalysisService(db_session)
    res = await service.analyze_bottlenecks(learner.id, goal.id)

    assert len(res.all_gaps) == 1
    item = res.all_gaps[0]
    assert item.required_level == 0.75
    assert item.mastery == 0.25
    assert item.gap == 0.50


@pytest.mark.asyncio
async def test_lowest_mastery_is_not_bottleneck(db_session: AsyncSession) -> None:
    learner = Learner(display_name="Case A Learner", email=f"casea_{uuid4().hex[:6]}@example.com")
    role = Role(name=f"Case A Role {uuid4().hex[:4]}")
    skill_low_imp = Skill(name=f"Low Imp {uuid4().hex[:4]}", difficulty=1.0)
    skill_high_imp = Skill(name=f"High Imp {uuid4().hex[:4]}", difficulty=3.0)
    db_session.add_all([learner, role, skill_low_imp, skill_high_imp])
    await db_session.flush()

    rs_low = RoleSkill(
        role_id=role.id, skill_id=skill_low_imp.id, importance=0.1, required_level=4.0
    )
    rs_high = RoleSkill(
        role_id=role.id, skill_id=skill_high_imp.id, importance=1.0, required_level=4.0
    )
    goal = Goal(learner_id=learner.id, target_role_id=role.id, objective="Case A Goal")
    db_session.add_all([rs_low, rs_high, goal])
    await db_session.flush()

    # Low importance skill has 0% mastery
    # High importance skill has 40% mastery
    m_low = SkillMastery(
        learner_id=learner.id, skill_id=skill_low_imp.id, mastery_score=0.0, confidence=0.80
    )
    m_high = SkillMastery(
        learner_id=learner.id, skill_id=skill_high_imp.id, mastery_score=0.40, confidence=0.80
    )
    ev_low = SkillEvidence(
        learner_id=learner.id,
        skill_id=skill_low_imp.id,
        evidence_type="test",
        score=0.0,
        confidence=0.8,
    )
    ev_high = SkillEvidence(
        learner_id=learner.id,
        skill_id=skill_high_imp.id,
        evidence_type="test",
        score=0.4,
        confidence=0.8,
    )

    db_session.add_all([m_low, m_high, ev_low, ev_high])
    await db_session.flush()

    service = BottleneckAnalysisService(db_session)
    res = await service.analyze_bottlenecks(learner.id, goal.id)

    high_imp_item = next(i for i in res.all_gaps if i.skill_id == skill_high_imp.id)
    low_imp_item = next(i for i in res.all_gaps if i.skill_id == skill_low_imp.id)

    assert high_imp_item.rank < low_imp_item.rank


@pytest.mark.asyncio
async def test_graph_cycle_protection(db_session: AsyncSession) -> None:
    learner = Learner(display_name="Cycle Learner", email=f"cycle_{uuid4().hex[:6]}@example.com")
    role = Role(name=f"Cycle Role {uuid4().hex[:4]}")
    skill_a = Skill(name=f"Skill A {uuid4().hex[:4]}", difficulty=2.0)
    skill_b = Skill(name=f"Skill B {uuid4().hex[:4]}", difficulty=2.0)
    db_session.add_all([learner, role, skill_a, skill_b])
    await db_session.flush()

    rs_a = RoleSkill(role_id=role.id, skill_id=skill_a.id, importance=0.8, required_level=3.0)
    rs_b = RoleSkill(role_id=role.id, skill_id=skill_b.id, importance=0.8, required_level=3.0)
    rel_a_b = SkillRelation(
        source_skill_id=skill_a.id,
        target_skill_id=skill_b.id,
        relation_type="prerequisite",
        strength=1.0,
    )
    rel_b_a = SkillRelation(
        source_skill_id=skill_b.id,
        target_skill_id=skill_a.id,
        relation_type="prerequisite",
        strength=1.0,
    )
    goal = Goal(learner_id=learner.id, target_role_id=role.id, objective="Cycle Goal")

    db_session.add_all([rs_a, rs_b, rel_a_b, rel_b_a, goal])
    await db_session.flush()

    service = DependencyImpactService(db_session)
    impacts = await service.compute_dependency_impacts(
        [skill_a.id, skill_b.id], {skill_a.id: 0.8, skill_b.id: 0.8}
    )

    assert skill_a.id in impacts
    assert skill_b.id in impacts
    assert impacts[skill_a.id].impact_score > 1.0


@pytest.mark.asyncio
async def test_deterministic_tie_breaking(db_session: AsyncSession) -> None:
    learner = Learner(display_name="Tie Learner", email=f"tie_{uuid4().hex[:6]}@example.com")
    role = Role(name=f"Tie Role {uuid4().hex[:4]}")
    skill_alpha = Skill(name="Alpha Skill", difficulty=2.0)
    skill_beta = Skill(name="Beta Skill", difficulty=2.0)
    db_session.add_all([learner, role, skill_alpha, skill_beta])
    await db_session.flush()

    rs_a = RoleSkill(role_id=role.id, skill_id=skill_alpha.id, importance=0.8, required_level=3.0)
    rs_b = RoleSkill(role_id=role.id, skill_id=skill_beta.id, importance=0.8, required_level=3.0)
    goal = Goal(learner_id=learner.id, target_role_id=role.id, objective="Tie Goal")
    db_session.add_all([rs_a, rs_b, goal])
    await db_session.flush()

    service = BottleneckAnalysisService(db_session)
    res = await service.analyze_bottlenecks(learner.id, goal.id)

    # Identical score & importance -> name asc ("Alpha Skill" before "Beta Skill")
    assert res.all_gaps[0].skill_name == "Alpha Skill"
    assert res.all_gaps[1].skill_name == "Beta Skill"


@pytest.mark.asyncio
async def test_bottlenecks_api_endpoint(db_session: AsyncSession) -> None:
    learner_stmt = select(Learner).where(Learner.email == "alex.chen@example.com")
    learner = (await db_session.execute(learner_stmt)).scalar_one()

    role_stmt = select(Role).where(Role.name == "AI Engineer")
    role = (await db_session.execute(role_stmt)).scalar_one()

    goal_stmt = select(Goal).where(Goal.learner_id == learner.id, Goal.target_role_id == role.id)
    goal = (await db_session.execute(goal_stmt)).scalar_one()

    async def _get_db():
        yield db_session

    from app.api.dependencies import get_current_learner
    from app.core.database import get_db_session

    app.dependency_overrides[get_db_session] = _get_db
    app.dependency_overrides[get_current_learner] = lambda: learner

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/v1/learners/{learner.id}/goals/{goal.id}/bottlenecks")
            assert resp.status_code == 200
            data = resp.json()
            assert data["target_role"] == "AI Engineer"
            assert len(data["all_gaps"]) > 0
            assert "primary_bottleneck" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_bottlenecks_api_nonexistent_learner(db_session: AsyncSession) -> None:
    dummy_learner = Learner(id=uuid4(), display_name="Dummy", email="dummy@example.com")
    async def _get_db():
        yield db_session

    from app.api.dependencies import get_current_learner
    from app.core.database import get_db_session

    app.dependency_overrides[get_db_session] = _get_db
    app.dependency_overrides[get_current_learner] = lambda: dummy_learner

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/v1/learners/{dummy_learner.id}/goals/{uuid4()}/bottlenecks")
            assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()

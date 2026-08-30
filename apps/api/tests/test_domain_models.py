from uuid import uuid4

import pytest
from app.models.assessment import Assessment
from app.models.assessment_question import AssessmentQuestion
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learning_path import LearningPath
from app.models.learning_path_node import LearningPathNode
from app.models.learning_resource import LearningResource
from app.models.role import Role
from app.models.role_skill import RoleSkill
from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence
from app.models.skill_mastery import SkillMastery
from app.models.skill_relation import SkillRelation
from app.models.skill_resource import SkillResource
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_database_connection(db_session: AsyncSession) -> None:
    """1. Test basic database connection."""
    result = await db_session.execute(select(1))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_learner_creation(db_session: AsyncSession) -> None:
    """2. Test learner creation."""
    learner = Learner(
        display_name="Test User",
        email=f"test_{uuid4().hex[:8]}@example.com",
    )
    db_session.add(learner)
    await db_session.flush()

    assert learner.id is not None
    assert learner.created_at is not None
    assert learner.updated_at is not None


@pytest.mark.asyncio
async def test_role_creation(db_session: AsyncSession) -> None:
    """3. Test role creation."""
    role = Role(
        name=f"Test Role {uuid4().hex[:8]}",
        description="A test role for unit testing",
    )
    db_session.add(role)
    await db_session.flush()

    assert role.id is not None
    assert role.name.startswith("Test Role")


@pytest.mark.asyncio
async def test_goal_foreign_keys(db_session: AsyncSession) -> None:
    """4. Test goal foreign keys linking Learner and Role."""
    learner = Learner(display_name="Goal User", email=f"goal_{uuid4().hex[:8]}@example.com")
    role = Role(name=f"Goal Role {uuid4().hex[:8]}", description="Target role")
    db_session.add_all([learner, role])
    await db_session.flush()

    goal = Goal(
        learner_id=learner.id,
        target_role_id=role.id,
        objective="Become proficient in AI",
        timeline_weeks=8,
        daily_minutes=45,
    )
    db_session.add(goal)
    await db_session.flush()

    assert goal.learner_id == learner.id
    assert goal.target_role_id == role.id


@pytest.mark.asyncio
async def test_unique_learner_email(db_session: AsyncSession) -> None:
    """5. Test unique constraint on learner email."""
    email = f"duplicate_{uuid4().hex[:8]}@example.com"
    l1 = Learner(display_name="User 1", email=email)
    l2 = Learner(display_name="User 2", email=email)

    db_session.add(l1)
    await db_session.flush()

    db_session.add(l2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_skill_hierarchy(db_session: AsyncSession) -> None:
    """6. Test parent-child self-referential skill hierarchy."""
    parent = Skill(name=f"Parent Skill {uuid4().hex[:8]}", difficulty=2.0)
    db_session.add(parent)
    await db_session.flush()

    child = Skill(
        name=f"Child Skill {uuid4().hex[:8]}",
        difficulty=3.0,
        parent_skill_id=parent.id,
    )
    db_session.add(child)
    await db_session.flush()

    assert child.parent_skill_id == parent.id


@pytest.mark.asyncio
async def test_role_skill_composite_key(db_session: AsyncSession) -> None:
    """7. Test role-skill composite primary key association."""
    role = Role(name=f"Role {uuid4().hex[:8]}")
    skill = Skill(name=f"Skill {uuid4().hex[:8]}")
    db_session.add_all([role, skill])
    await db_session.flush()

    rs = RoleSkill(role_id=role.id, skill_id=skill.id, importance=1.5, required_level=3.5)
    db_session.add(rs)
    await db_session.flush()

    assert rs.role_id == role.id
    assert rs.skill_id == skill.id


@pytest.mark.asyncio
async def test_skill_prerequisite_relation(db_session: AsyncSession) -> None:
    """8. Test skill prerequisite directed graph relationship."""
    s1 = Skill(name=f"Source Skill {uuid4().hex[:8]}")
    s2 = Skill(name=f"Target Skill {uuid4().hex[:8]}")
    db_session.add_all([s1, s2])
    await db_session.flush()

    relation = SkillRelation(
        source_skill_id=s1.id,
        target_skill_id=s2.id,
        relation_type="prerequisite",
        strength=1.0,
    )
    db_session.add(relation)
    await db_session.flush()

    assert relation.source_skill_id == s1.id
    assert relation.target_skill_id == s2.id


@pytest.mark.asyncio
async def test_learning_resource_skill_relationship(db_session: AsyncSession) -> None:
    """9. Test resource and skill relationship via SkillResource."""

    skill = Skill(name=f"Resource Skill {uuid4().hex[:8]}")
    resource = LearningResource(
        title="Python Guide",
        resource_type="article",
        difficulty=1.0,
        estimated_minutes=30,
        source_url="/docs/python",
    )
    db_session.add_all([skill, resource])
    await db_session.flush()

    sr = SkillResource(skill_id=skill.id, resource_id=resource.id, relevance=0.9)
    db_session.add(sr)
    await db_session.flush()

    assert sr.skill_id == skill.id
    assert sr.resource_id == resource.id


@pytest.mark.asyncio
async def test_assessment_question_relationship(db_session: AsyncSession) -> None:
    """10. Test assessment and assessment question relationship."""
    skill = Skill(name=f"Assessment Skill {uuid4().hex[:8]}")
    db_session.add(skill)
    await db_session.flush()

    assessment = Assessment(
        title="Skill Check Quiz",
        assessment_type="skill_check",
        skill_id=skill.id,
    )
    db_session.add(assessment)
    await db_session.flush()

    question = AssessmentQuestion(
        assessment_id=assessment.id,
        skill_id=skill.id,
        prompt="What is async/await?",
        question_type="free_response",
        difficulty=2.0,
        expected_answer={"keywords": ["asyncio", "coroutine"]},
    )
    db_session.add(question)
    await db_session.flush()

    assert question.assessment_id == assessment.id
    assert question.skill_id == skill.id


@pytest.mark.asyncio
async def test_skill_evidence_persistence(db_session: AsyncSession) -> None:
    """11. Test skill evidence persistence."""
    learner = Learner(display_name="Evidence Learner", email=f"ev_{uuid4().hex[:8]}@example.com")
    skill = Skill(name=f"Evidence Skill {uuid4().hex[:8]}")
    db_session.add_all([learner, skill])
    await db_session.flush()

    evidence = SkillEvidence(
        learner_id=learner.id,
        skill_id=skill.id,
        evidence_type="project",
        score=0.95,
        confidence=0.90,
        metadata_json={"repo": "github.com/example/project"},
    )
    db_session.add(evidence)
    await db_session.flush()

    assert evidence.id is not None
    assert evidence.score == 0.95
    assert evidence.metadata_json == {"repo": "github.com/example/project"}


@pytest.mark.asyncio
async def test_unique_learner_skill_mastery(db_session: AsyncSession) -> None:
    """12. Test unique constraint on (learner_id, skill_id) for SkillMastery."""
    learner = Learner(display_name="Mastery Learner", email=f"mas_{uuid4().hex[:8]}@example.com")
    skill = Skill(name=f"Mastery Skill {uuid4().hex[:8]}")
    db_session.add_all([learner, skill])
    await db_session.flush()

    m1 = SkillMastery(learner_id=learner.id, skill_id=skill.id, mastery_score=3.0)
    m2 = SkillMastery(learner_id=learner.id, skill_id=skill.id, mastery_score=4.0)

    db_session.add(m1)
    await db_session.flush()

    db_session.add(m2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_learning_path_nodes(db_session: AsyncSession) -> None:
    """13. Test learning path and sequential nodes relationship."""
    learner = Learner(display_name="Path User", email=f"path_{uuid4().hex[:8]}@example.com")
    role = Role(name=f"Path Role {uuid4().hex[:8]}")
    db_session.add_all([learner, role])
    await db_session.flush()

    goal = Goal(learner_id=learner.id, target_role_id=role.id, objective="Path Objective")
    db_session.add(goal)
    await db_session.flush()

    path = LearningPath(
        learner_id=learner.id,
        goal_id=goal.id,
        name="Custom Path",
        strategy="fastest",
    )
    db_session.add(path)
    await db_session.flush()

    n1 = LearningPathNode(learning_path_id=path.id, sequence=1, milestone_label="Step 1")
    n2 = LearningPathNode(learning_path_id=path.id, sequence=2, milestone_label="Step 2")
    db_session.add_all([n1, n2])
    await db_session.flush()

    assert n1.learning_path_id == path.id
    assert n2.sequence == 2


@pytest.mark.asyncio
async def test_node_sequence_uniqueness(db_session: AsyncSession) -> None:
    """14. Test sequence uniqueness constraint within a learning path."""
    learner = Learner(display_name="Seq User", email=f"seq_{uuid4().hex[:8]}@example.com")
    role = Role(name=f"Seq Role {uuid4().hex[:8]}")
    db_session.add_all([learner, role])
    await db_session.flush()

    goal = Goal(learner_id=learner.id, target_role_id=role.id, objective="Seq Objective")
    db_session.add(goal)
    await db_session.flush()

    path = LearningPath(
        learner_id=learner.id, goal_id=goal.id, name="Seq Path", strategy="balanced"
    )
    db_session.add(path)
    await db_session.flush()

    n1 = LearningPathNode(learning_path_id=path.id, sequence=1, milestone_label="Step A")
    n2 = LearningPathNode(learning_path_id=path.id, sequence=1, milestone_label="Step B")

    db_session.add(n1)
    await db_session.flush()

    db_session.add(n2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()

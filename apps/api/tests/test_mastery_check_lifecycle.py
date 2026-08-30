from uuid import uuid4

import pytest
from app.models.assessment import Assessment
from app.models.assessment_question import AssessmentQuestion
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learning_path import LearningPath
from app.models.learning_path_node import LearningPathNode
from app.models.learning_resource import LearningResource
from app.models.mastery_check_attempt import MasteryCheckAttempt
from app.models.role import Role
from app.models.skill import Skill
from app.services.proof_of_mastery_service import ProofOfMasteryService
from sqlalchemy import select


@pytest.mark.asyncio
async def test_mastery_check_lifecycle_end_to_end(db_session):
    learner = Learner(email=f"test_{uuid4()}@example.com", display_name="Test Learner")
    role_res = await db_session.execute(select(Role))
    role = role_res.scalars().first()
    if not role:
        role = Role(name="DevOps Engineer", description="DevOps Role")
        db_session.add(role)
        await db_session.flush()

    db_session.add(learner)
    await db_session.flush()

    service = ProofOfMasteryService(db_session)

    skill = Skill(name=f"Docker Test {uuid4()}")
    db_session.add(skill)
    await db_session.flush()

    resource = LearningResource(title="Docker Activity", resource_type="hands_on")
    db_session.add(resource)
    await db_session.flush()

    assessment = Assessment(title="Docker Assessment", assessment_type="proof_of_mastery", skill_id=skill.id)
    db_session.add(assessment)
    await db_session.flush()

    question = AssessmentQuestion(
        assessment_id=assessment.id,
        skill_id=skill.id,
        prompt="Explain Docker containerization.",
        question_type="free_text",
        difficulty=3.0,
    )
    db_session.add(question)

    goal = Goal(learner_id=learner.id, target_role_id=role.id, objective="Master Docker Test")
    db_session.add(goal)
    await db_session.flush()

    path = LearningPath(learner_id=learner.id, goal_id=goal.id, name="Test Path", strategy="FASTEST", status="active")
    db_session.add(path)
    await db_session.flush()

    node = LearningPathNode(learning_path_id=path.id, sequence=1, resource_id=resource.id, skill_id=skill.id, milestone_label="Step 1: Docker Test")
    db_session.add(node)
    await db_session.flush()

    activity_attempt = await service.start_activity_attempt(learner.id, node.id)
    assert activity_attempt.status == "started"

    completed_activity = await service.complete_activity_attempt(
        learner.id,
        activity_attempt.id,
        submission_data={"repository_url": "https://github.com/test/repo", "project_description": "Built docker app", "implementation_summary": "Added dockerfile"},
    )
    assert completed_activity.status == "completed"

    start_resp = await service.start_mastery_check(learner.id, activity_attempt.id)
    assert start_resp.check_id is not None

    db_check = await db_session.get(MasteryCheckAttempt, start_resp.check_id)
    assert db_check is not None
    assert db_check.id == start_resp.check_id
    assert db_check.learner_id == learner.id

    q_id = start_resp.questions[0].question_id
    from app.schemas.proof_of_mastery import MasteryCheckAnswerSubmission
    sub_resp = await service.submit_mastery_check(
        learner.id,
        start_resp.check_id,
        answers=[MasteryCheckAnswerSubmission(question_id=q_id, learner_answer="Docker packages dependencies into isolated containers.")],
    )
    assert sub_resp.evaluated_at is not None

    await db_session.refresh(db_check)
    assert db_check.status == "completed"


@pytest.mark.asyncio
async def test_submit_nonexistent_mastery_check(db_session):
    learner = Learner(email=f"test_{uuid4()}@example.com", display_name="Test Learner")
    db_session.add(learner)
    await db_session.flush()

    service = ProofOfMasteryService(db_session)
    non_existent_id = uuid4()
    with pytest.raises(ValueError, match="not found"):
        await service.submit_mastery_check(
            learner.id,
            non_existent_id,
            answers=[],
        )


@pytest.mark.asyncio
async def test_submit_unowned_mastery_check(db_session):
    learner1 = Learner(email=f"test1_{uuid4()}@example.com", display_name="Test Learner 1")
    learner2 = Learner(email=f"test2_{uuid4()}@example.com", display_name="Test Learner 2")
    role_res = await db_session.execute(select(Role))
    role = role_res.scalars().first()
    if not role:
        role = Role(name="DevOps Engineer", description="DevOps Role")
        db_session.add(role)
        await db_session.flush()

    db_session.add_all([learner1, learner2])
    await db_session.flush()

    skill = Skill(name=f"Docker Unowned Test {uuid4()}")
    db_session.add(skill)
    await db_session.flush()

    resource = LearningResource(title="Docker Activity Unowned", resource_type="hands_on")
    db_session.add(resource)
    await db_session.flush()

    service = ProofOfMasteryService(db_session)

    goal = Goal(learner_id=learner1.id, target_role_id=role.id, objective="Unowned Goal")
    db_session.add(goal)
    await db_session.flush()

    path = LearningPath(learner_id=learner1.id, goal_id=goal.id, name="Test Path", strategy="FASTEST", status="active")
    db_session.add(path)
    await db_session.flush()

    node = LearningPathNode(learning_path_id=path.id, sequence=1, resource_id=resource.id, skill_id=skill.id, milestone_label="Step 1")
    db_session.add(node)
    await db_session.flush()

    activity_attempt = await service.start_activity_attempt(learner1.id, node.id)
    start_resp = await service.start_mastery_check(learner1.id, activity_attempt.id)

    with pytest.raises(ValueError, match="does not own"):
        await service.submit_mastery_check(
            learner2.id,
            start_resp.check_id,
            answers=[],
        )

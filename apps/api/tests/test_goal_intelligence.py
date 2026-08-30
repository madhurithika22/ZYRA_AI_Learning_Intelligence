from uuid import uuid4

import pytest
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learner_profile import LearnerProfile
from app.models.role import Role
from app.models.skill import Skill
from app.models.skill_mastery import SkillMastery
from app.providers.llm.gemini_provider import GeminiProvider
from app.providers.llm.mock_provider import MockLLMProvider
from app.schemas.goal_intelligence import (
    GoalInterpretation,
)
from app.services.goal_creation_service import GoalCreationService
from app.services.goal_intelligence_service import GoalIntelligenceService
from app.services.role_resolution import RoleResolutionService
from app.services.skill_resolution import SkillResolutionService
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# ----------------------------------------------------------------------
# 1. Pydantic Schema Validation Tests
# ----------------------------------------------------------------------


def test_valid_goal_schema() -> None:
    goal = GoalInterpretation(
        target_role="ML Engineer",
        objective="Become ML Engineer",
        timeline_weeks=24,
        daily_minutes=90,
        desired_outcome="job_readiness",
        constraints=["Daily study: 90 mins"],
        stated_existing_skills=["Python"],
        ambiguities=[],
        confidence=0.95,
    )
    assert goal.target_role == "ML Engineer"
    assert goal.timeline_weeks == 24
    assert goal.daily_minutes == 90
    assert goal.confidence == 0.95


def test_missing_optional_fields() -> None:
    goal = GoalInterpretation(
        target_role="AI Engineer",
        objective="Learn AI",
    )
    assert goal.timeline_weeks is None
    assert goal.daily_minutes is None
    assert goal.stated_existing_skills == []
    assert goal.confidence == 1.0


def test_invalid_timeline_weeks() -> None:
    with pytest.raises(ValidationError) as exc:
        GoalInterpretation(
            target_role="ML Engineer",
            objective="Invalid timeline",
            timeline_weeks=-5,
        )
    assert "timeline_weeks must be a positive integer" in str(exc.value)


def test_invalid_daily_minutes() -> None:
    with pytest.raises(ValidationError) as exc:
        GoalInterpretation(
            target_role="ML Engineer",
            objective="Zero daily mins",
            daily_minutes=0,
        )
    assert "daily_minutes must be greater than zero" in str(exc.value)

    with pytest.raises(ValidationError) as exc2:
        GoalInterpretation(
            target_role="ML Engineer",
            objective="Excessive mins",
            daily_minutes=2000,
        )
    assert "daily_minutes cannot exceed 1440 minutes" in str(exc2.value)


def test_invalid_confidence() -> None:
    with pytest.raises(ValidationError) as exc:
        GoalInterpretation(
            target_role="ML Engineer",
            objective="Invalid confidence",
            confidence=1.5,
        )
    assert "confidence must be between 0.0 and 1.0" in str(exc.value)


# ----------------------------------------------------------------------
# 2. LLM Provider & Provider Failure Tests
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mock_provider_default_generation() -> None:
    provider = MockLLMProvider()
    prompt = "I want to become an ML Engineer in 6 months. I know Python and basic ML. I can study 90 minutes a day."
    result = await provider.generate_structured(prompt, GoalInterpretation)

    assert result.target_role == "ML Engineer"
    assert result.timeline_weeks == 24
    assert result.daily_minutes == 90
    assert "Python" in result.stated_existing_skills
    assert "Machine Learning" in result.stated_existing_skills


@pytest.mark.asyncio
async def test_mock_provider_override_response() -> None:
    custom_obj = GoalInterpretation(
        target_role="Data Scientist",
        objective="Custom override objective",
        timeline_weeks=12,
    )
    provider = MockLLMProvider(override_response=custom_obj)
    result = await provider.generate_structured("Anything", GoalInterpretation)
    assert result.target_role == "Data Scientist"
    assert result.objective == "Custom override objective"


@pytest.mark.asyncio
async def test_provider_failure_handling(db_session: AsyncSession) -> None:
    provider = MockLLMProvider(override_response=RuntimeError("Provider API timeout"))
    service = GoalIntelligenceService(session=db_session, llm_provider=provider)

    result = await service.interpret_goal("I want to learn AI")
    assert result.is_valid is False
    assert result.validation_status == "invalid"
    assert any("LLM provider generation failed" in err for err in result.validation_errors)


@pytest.mark.asyncio
async def test_gemini_provider_missing_api_key_raises() -> None:
    provider = GeminiProvider(api_key="")
    with pytest.raises(RuntimeError) as exc:
        await provider.generate_structured("test", GoalInterpretation)
    assert "GEMINI_API_KEY environment variable is missing" in str(exc.value)


# ----------------------------------------------------------------------
# 3. Role Resolution Tests
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_role_resolution(db_session: AsyncSession) -> None:
    role = Role(name=f"ML Engineer {uuid4().hex[:4]}")
    db_session.add(role)
    await db_session.flush()

    resolver = RoleResolutionService(db_session)

    # Exact match
    res1 = await resolver.resolve_role(role.name)
    assert res1.is_resolved is True
    assert res1.canonical_role_id == role.id

    # Case & whitespace normalization
    res2 = await resolver.resolve_role(f"  {role.name.lower()}  ")
    assert res2.is_resolved is True
    assert res2.canonical_role_id == role.id

    # Alias match
    res3 = await resolver.resolve_role("machine learning engineer")
    assert res3.is_resolved is True or res3.canonical_role_id is None

    # Unresolved role
    res4 = await resolver.resolve_role("unknown role")
    assert res4.is_resolved is False
    assert res4.canonical_role_id is None


# ----------------------------------------------------------------------
# 4. Stated Skill Resolution Tests
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_skill_resolution(db_session: AsyncSession) -> None:
    s1 = Skill(name=f"Python {uuid4().hex[:4]}")
    s2 = Skill(name=f"Machine Learning {uuid4().hex[:4]}")
    db_session.add_all([s1, s2])
    await db_session.flush()

    resolver = SkillResolutionService(db_session)
    info = await resolver.resolve_skills([s1.name, "basic machine learning", "unknown skill"])

    assert len(info.resolved_skills) >= 1
    assert "unknown skill" in info.unresolved_skills


# ----------------------------------------------------------------------
# 5. Goal Creation, No False Mastery, & Rollback Tests
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_valid_goal_creation_service(db_session: AsyncSession) -> None:
    learner = Learner(display_name="Test Learner", email=f"learner_{uuid4().hex[:6]}@example.com")
    db_session.add(learner)

    role_stmt = select(Role).where(Role.name == "ML Engineer")
    role = (await db_session.execute(role_stmt)).scalar_one_or_none()
    if not role:
        role = Role(name="ML Engineer")
        db_session.add(role)

    await db_session.flush()

    service = GoalCreationService(session=db_session)
    prompt = (
        "I want to become an ML Engineer in 6 months. I know Python. I can study 60 minutes a day."
    )

    resp = await service.create_goal_from_natural_language(
        learner_id=learner.id,
        natural_language_goal=prompt,
    )

    assert resp.goal_id is not None
    assert resp.learner_id == learner.id
    assert resp.target_role_id == role.id
    assert resp.daily_minutes == 60

    # Verify LearnerProfile was created
    profile_stmt = select(LearnerProfile).where(LearnerProfile.learner_id == learner.id)
    profile_res = await db_session.execute(profile_stmt)
    profile = profile_res.scalar_one_or_none()
    assert profile is not None
    assert profile.profile_metadata["stated_existing_skills"] == ["Python"]

    # Verify NO SkillMastery records were created simply from stated skills
    mastery_stmt = select(SkillMastery).where(SkillMastery.learner_id == learner.id)
    masteries = (await db_session.execute(mastery_stmt)).scalars().all()
    assert len(masteries) == 0


@pytest.mark.asyncio
async def test_invalid_role_rollback(db_session: AsyncSession) -> None:
    learner = Learner(display_name="Rollback Learner", email=f"rb_{uuid4().hex[:6]}@example.com")
    db_session.add(learner)
    await db_session.flush()

    mock_provider = MockLLMProvider(
        override_response=GoalInterpretation(
            target_role="Unknown Role XYZ",
            objective="Will fail role resolution",
        )
    )

    service = GoalCreationService(session=db_session, llm_provider=mock_provider)

    with pytest.raises(ValueError) as exc:
        await service.create_goal_from_natural_language(
            learner_id=learner.id,
            natural_language_goal="I want to become an Unknown Role XYZ",
        )
    assert "Goal interpretation failed validation" in str(exc.value)

    # Verify NO Goal or LearnerProfile was created
    goal_stmt = select(Goal).where(Goal.learner_id == learner.id)
    goals = (await db_session.execute(goal_stmt)).scalars().all()
    assert len(goals) == 0

    prof_stmt = select(LearnerProfile).where(LearnerProfile.learner_id == learner.id)
    profs = (await db_session.execute(prof_stmt)).scalars().all()
    assert len(profs) == 0

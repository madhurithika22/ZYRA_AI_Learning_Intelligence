from uuid import UUID

from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learner_profile import LearnerProfile
from app.providers.llm.base import LLMProvider
from app.schemas.goal_intelligence import (
    GoalCreationResponse,
)
from app.services.goal_intelligence_service import GoalIntelligenceService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class GoalCreationService:
    """Application service managing transactional goal creation and learner profile initialization."""

    def __init__(
        self,
        session: AsyncSession,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.session = session
        self.intelligence_service = GoalIntelligenceService(
            session=session,
            llm_provider=llm_provider,
        )

    async def create_goal_from_natural_language(
        self,
        learner_id: UUID,
        natural_language_goal: str,
    ) -> GoalCreationResponse:
        # 1. Ensure learner exists
        learner_stmt = select(Learner).where(Learner.id == learner_id)
        learner_res = await self.session.execute(learner_stmt)
        learner = learner_res.scalar_one_or_none()
        if not learner:
            raise ValueError(f"Learner with ID '{learner_id}' does not exist.")

        # 2. Interpret and validate natural language goal
        result = await self.intelligence_service.interpret_goal(natural_language_goal)

        if not result.is_valid or not result.resolved_role.canonical_role_id:
            errors_summary = "; ".join(result.validation_errors) or "Role resolution failed"
            raise ValueError(f"Goal interpretation failed validation: {errors_summary}")

        target_role_id = result.resolved_role.canonical_role_id

        # 3. Transactional update of LearnerProfile and Goal
        async with self.session.begin_nested():
            # Update/Create LearnerProfile
            profile_stmt = select(LearnerProfile).where(LearnerProfile.learner_id == learner_id)
            profile_res = await self.session.execute(profile_stmt)
            profile = profile_res.scalar_one_or_none()

            meta_skills = [s.name for s in result.resolved_skills.resolved_skills]
            meta_unresolved = result.resolved_skills.unresolved_skills

            if not profile:
                profile = LearnerProfile(
                    learner_id=learner_id,
                    experience_level=result.interpretation.desired_outcome,
                    preferred_learning_mode="balanced",
                    weekly_availability_hours=(
                        (result.interpretation.daily_minutes or 60) * 7 / 60.0
                    ),
                    stated_background=f"Stated prompt: {natural_language_goal}",
                    profile_metadata={
                        "stated_existing_skills": meta_skills,
                        "unresolved_skill_phrases": meta_unresolved,
                        "raw_goal_prompt": natural_language_goal,
                    },
                )
                self.session.add(profile)
            else:
                profile.stated_background = f"Stated prompt: {natural_language_goal}"
                profile.profile_metadata = {
                    **(profile.profile_metadata or {}),
                    "stated_existing_skills": meta_skills,
                    "unresolved_skill_phrases": meta_unresolved,
                    "raw_goal_prompt": natural_language_goal,
                }

            # Create Goal record
            goal = Goal(
                learner_id=learner_id,
                target_role_id=target_role_id,
                objective=result.interpretation.objective,
                timeline_weeks=result.interpretation.timeline_weeks,
                daily_minutes=result.interpretation.daily_minutes,
            )
            self.session.add(goal)
            await self.session.flush()

        await self.session.commit()

        return GoalCreationResponse(
            goal_id=goal.id,
            learner_id=learner.id,
            target_role_id=target_role_id,
            objective=goal.objective,
            timeline_weeks=goal.timeline_weeks,
            daily_minutes=goal.daily_minutes,
            intelligence_result=result,
        )

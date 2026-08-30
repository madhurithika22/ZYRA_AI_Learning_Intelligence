from uuid import UUID

from app.models.assessment_question import AssessmentQuestion
from app.models.diagnostic_response import DiagnosticResponse
from app.models.diagnostic_session import DiagnosticSession
from app.models.goal import Goal
from app.models.role_skill import RoleSkill
from app.models.skill_mastery import SkillMastery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class QuestionSelectionService:
    """Deterministic adaptive question selection algorithm maximizing information gain."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def select_next_question(
        self,
        diagnostic_session: DiagnosticSession,
    ) -> AssessmentQuestion | None:
        # 1. Retrieve goal & role required skills
        goal_stmt = select(Goal).where(Goal.id == diagnostic_session.goal_id)
        goal_res = await self.session.execute(goal_stmt)
        goal = goal_res.scalar_one_or_none()
        if not goal:
            return None

        role_skills_stmt = select(RoleSkill).where(RoleSkill.role_id == goal.target_role_id)
        role_skills_res = await self.session.execute(role_skills_stmt)
        role_skills = role_skills_res.scalars().all()
        if not role_skills:
            return None

        role_skill_map: dict[UUID, float] = {rs.skill_id: rs.importance for rs in role_skills}
        target_skill_ids = list(role_skill_map.keys())

        # 2. Retrieve current learner skill masteries
        mastery_stmt = select(SkillMastery).where(
            SkillMastery.learner_id == diagnostic_session.learner_id,
            SkillMastery.skill_id.in_(target_skill_ids),
        )
        mastery_res = await self.session.execute(mastery_stmt)
        masteries = {m.skill_id: m for m in mastery_res.scalars().all()}

        # 3. Retrieve previously answered question IDs in this session
        session_responses_stmt = select(DiagnosticResponse.question_id).where(
            DiagnosticResponse.session_id == diagnostic_session.id
        )
        answered_res = await self.session.execute(session_responses_stmt)
        session_answered_ids = set(answered_res.scalars().all())

        # Also retrieve all questions answered by learner globally
        global_responses_stmt = select(DiagnosticResponse.question_id).where(
            DiagnosticResponse.session.has(learner_id=diagnostic_session.learner_id)
        )
        global_answered_res = await self.session.execute(global_responses_stmt)
        global_answered_ids = set(global_answered_res.scalars().all())

        # 4. Fetch available assessment questions for target skills
        questions_stmt = select(AssessmentQuestion).where(
            AssessmentQuestion.skill_id.in_(target_skill_ids)
        )
        questions_res = await self.session.execute(questions_stmt)
        candidate_questions = questions_res.scalars().all()

        if not candidate_questions:
            return None

        # Count answered questions per skill in the current session
        session_skill_counts: dict[UUID, int] = {}
        for q in candidate_questions:
            if q.id in session_answered_ids:
                session_skill_counts[q.skill_id] = session_skill_counts.get(q.skill_id, 0) + 1

        # 5. Score candidate questions
        best_question: AssessmentQuestion | None = None
        best_score: float = -1.0

        for question in candidate_questions:
            # Novelty check
            if question.id in session_answered_ids:
                novelty = 0.0
            elif question.id in global_answered_ids:
                novelty = 0.5
            else:
                novelty = 1.0

            if novelty == 0.0:
                continue

            # Skill attributes
            skill_importance = role_skill_map.get(question.skill_id, 1.0)
            mastery_rec = masteries.get(question.skill_id)

            current_mastery = mastery_rec.mastery_score if mastery_rec else 0.0
            current_confidence = mastery_rec.confidence if mastery_rec else 0.0

            # Component 1: Uncertainty (higher when confidence is low)
            uncertainty = max(0.05, 1.0 - current_confidence)

            # Component 2: Difficulty Fit (1.0 to 5.0 scale normalized to [0,1])
            norm_difficulty = max(0.0, min(1.0, (question.difficulty - 1.0) / 4.0))
            difficulty_fit = 1.0 - abs(norm_difficulty - current_mastery)

            # Component 3: Multi-Skill Coverage Balance (boosts unassessed target skills in current session)
            skill_questions_asked = session_skill_counts.get(question.skill_id, 0)
            coverage_balance = 1.5 if skill_questions_asked == 0 else (1.0 / (1.0 + skill_questions_asked))

            # question_priority = uncertainty * skill_importance * difficulty_fit * novelty * coverage_balance
            priority = uncertainty * skill_importance * difficulty_fit * novelty * coverage_balance

            if priority > best_score:
                best_score = priority
                best_question = question

        return best_question

from datetime import datetime, timezone
from uuid import UUID

from app.core.constants import (
    DEFAULT_MAX_DIAGNOSTIC_QUESTIONS,
    SESSION_STATUS_COMPLETED,
    SESSION_STATUS_IN_PROGRESS,
    TARGET_SKILL_CONFIDENCE_THRESHOLD,
)
from app.models.assessment_question import AssessmentQuestion
from app.models.diagnostic_response import DiagnosticResponse
from app.models.diagnostic_session import DiagnosticSession
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.role_skill import RoleSkill
from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence
from app.models.skill_mastery import SkillMastery
from app.providers.llm.base import LLMProvider
from app.schemas.diagnostic import (
    DiagnosticQuestionResponse,
    DiagnosticSessionResponse,
    LearnerSkillStateItem,
    LearnerSkillStateResponse,
    SubmitResponseResult,
)
from app.services.answer_evaluation import LLMEvaluator
from app.services.mastery_engine import MasteryEngine
from app.services.question_selection import QuestionSelectionService
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class DiagnosticService:
    """Application service orchestrating diagnostic session lifecycle, questions, responses, and skill state."""

    def __init__(
        self,
        session: AsyncSession,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.session = session
        self.question_selector = QuestionSelectionService(session)
        self.evaluator = LLMEvaluator(llm_provider)
        self.mastery_engine = MasteryEngine(session)

    async def start_session(
        self,
        learner_id: UUID,
        goal_id: UUID,
        max_questions: int = DEFAULT_MAX_DIAGNOSTIC_QUESTIONS,
        force_new: bool = False,
    ) -> DiagnosticSessionResponse:
        # Validate learner and goal exist
        learner = await self.session.get(Learner, learner_id)
        if not learner:
            raise ValueError(f"Learner with ID '{learner_id}' not found.")

        goal = await self.session.get(Goal, goal_id)
        if not goal:
            raise ValueError(f"Goal with ID '{goal_id}' not found.")

        # Check for existing in_progress session for this learner & goal
        stmt = select(DiagnosticSession).where(
            DiagnosticSession.learner_id == learner_id,
            DiagnosticSession.goal_id == goal_id,
            DiagnosticSession.status == SESSION_STATUS_IN_PROGRESS,
        )
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            if not force_new:
                return self._to_session_response(existing)
            else:
                existing.status = SESSION_STATUS_COMPLETED
                existing.completed_at = datetime.now(timezone.utc)
                existing.session_metadata = {
                    **(existing.session_metadata or {}),
                    "termination_reason": "Archived for new diagnostic session",
                }

        diag_session = DiagnosticSession(
            learner_id=learner_id,
            goal_id=goal_id,
            status=SESSION_STATUS_IN_PROGRESS,
            question_count=0,
            max_questions=max_questions,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(diag_session)
        await self.session.commit()
        await self.session.refresh(diag_session)

        return self._to_session_response(diag_session)

    async def get_session(self, session_id: UUID) -> DiagnosticSessionResponse:
        diag_session = await self.session.get(DiagnosticSession, session_id)
        if not diag_session:
            raise ValueError(f"Diagnostic session '{session_id}' not found.")
        return self._to_session_response(diag_session)

    async def select_next_question(
        self,
        session_id: UUID,
    ) -> DiagnosticQuestionResponse | None:
        diag_session = await self.session.get(DiagnosticSession, session_id)
        if not diag_session:
            raise ValueError(f"Diagnostic session '{session_id}' not found.")

        if diag_session.status != SESSION_STATUS_IN_PROGRESS:
            return None

        question = await self.question_selector.select_next_question(diag_session)
        if not question:
            # Complete session if no available questions remain
            await self._complete_session(
                diag_session,
                reason="No further relevant diagnostic questions remaining.",
            )
            return None

        # Fetch skill details for prompt presentation
        skill = await self.session.get(Skill, question.skill_id)
        skill_name = skill.name if skill else "General Skill"

        diag_session.current_skill_id = question.skill_id
        await self.session.commit()

        options = question.expected_answer.get("options") if question.expected_answer else None

        return DiagnosticQuestionResponse(
            session_id=diag_session.id,
            question_id=question.id,
            skill_id=question.skill_id,
            skill_name=skill_name,
            question_type=question.question_type,
            difficulty=question.difficulty,
            prompt=question.prompt,
            options=options,
            question_number=diag_session.question_count + 1,
            total_questions=diag_session.max_questions,
        )

    async def submit_response(
        self,
        session_id: UUID,
        idempotency_key: str,
        question_id: UUID,
        learner_answer: str,
    ) -> SubmitResponseResult:
        # Idempotency check: Return existing result if key already processed
        dup_stmt = select(DiagnosticResponse).where(
            DiagnosticResponse.idempotency_key == idempotency_key
        )
        dup_res = await self.session.execute(dup_stmt)
        existing_resp = dup_res.scalar_one_or_none()
        if existing_resp:
            diag_session = await self.session.get(DiagnosticSession, session_id)
            is_comp = diag_session.status == SESSION_STATUS_COMPLETED if diag_session else True
            return SubmitResponseResult(
                session_id=session_id,
                question_id=question_id,
                is_correct=existing_resp.is_correct,
                score=existing_resp.score,
                evaluation_summary="Duplicate submission (idempotent result returned).",
                is_session_completed=is_comp,
                termination_reason=diag_session.session_metadata.get("termination_reason")
                if diag_session and diag_session.session_metadata
                else None,
            )

        # Atomic transaction block
        async with self.session.begin_nested():
            diag_session = await self.session.get(DiagnosticSession, session_id)
            if not diag_session:
                raise ValueError(f"Diagnostic session '{session_id}' not found.")

            if diag_session.status != SESSION_STATUS_IN_PROGRESS:
                raise ValueError(
                    f"Diagnostic session is not in progress (status: {diag_session.status})."
                )

            question = await self.session.get(AssessmentQuestion, question_id)
            if not question:
                raise ValueError(f"Question '{question_id}' not found.")

            # Evaluate response
            evaluation = await self.evaluator.evaluate_answer(question, learner_answer)

            # Persist DiagnosticResponse
            response_record = DiagnosticResponse(
                session_id=session_id,
                question_id=question_id,
                idempotency_key=idempotency_key,
                learner_answer=learner_answer,
                is_correct=evaluation.is_correct,
                score=evaluation.score,
                evaluation_metadata={
                    "confidence": evaluation.confidence,
                    "rubric_coverage": evaluation.rubric_coverage,
                    "misconception_code": evaluation.misconception_code,
                    "feedback": evaluation.feedback,
                },
                answered_at=datetime.now(timezone.utc),
            )
            self.session.add(response_record)

            # Update Mastery and record SkillEvidence
            evidence, mastery = await self.mastery_engine.record_evidence_and_update_mastery(
                learner_id=diag_session.learner_id,
                skill_id=question.skill_id,
                question=question,
                evaluation=evaluation,
                evidence_type=f"diagnostic_{question.question_type}",
                source_id=str(session_id),
            )

            diag_session.question_count += 1

            # Termination evaluation
            is_completed = False
            termination_reason: str | None = None

            if diag_session.question_count >= diag_session.max_questions:
                is_completed = True
                termination_reason = (
                    f"Reached maximum question limit ({diag_session.max_questions})."
                )
            else:
                # Check confidence across all target role skills
                confident = await self._check_skills_sufficient_confidence(
                    diag_session.learner_id, diag_session.goal_id
                )
                if confident:
                    is_completed = True
                    termination_reason = "Sufficient confidence reached across target skills."

            if is_completed:
                diag_session.status = SESSION_STATUS_COMPLETED
                diag_session.completed_at = datetime.now(timezone.utc)
                diag_session.session_metadata = {
                    **(diag_session.session_metadata or {}),
                    "termination_reason": termination_reason,
                }

            await self.session.flush()

        await self.session.commit()

        return SubmitResponseResult(
            session_id=session_id,
            question_id=question_id,
            is_correct=evaluation.is_correct,
            score=evaluation.score,
            evaluation_summary=evaluation.feedback,
            is_session_completed=is_completed,
            termination_reason=termination_reason,
            mastery_updates=[
                {
                    "skill_id": str(mastery.skill_id),
                    "mastery_score": mastery.mastery_score,
                    "confidence": mastery.confidence,
                }
            ],
        )

    async def get_learner_skill_state(
        self,
        learner_id: UUID,
        goal_id: UUID,
    ) -> LearnerSkillStateResponse:
        goal = await self.session.get(Goal, goal_id)
        if not goal:
            raise ValueError(f"Goal '{goal_id}' not found.")

        # Query role skills
        role_skills_stmt = (
            select(RoleSkill)
            .where(RoleSkill.role_id == goal.target_role_id)
            .options(selectinload(RoleSkill.skill), selectinload(RoleSkill.role))
        )
        role_skills_res = await self.session.execute(role_skills_stmt)
        role_skills = role_skills_res.scalars().all()

        target_role_name = (
            role_skills[0].role.name if role_skills and role_skills[0].role else "Target Role"
        )

        skill_items: list[LearnerSkillStateItem] = []

        for rs in role_skills:
            # Query mastery
            mastery_stmt = select(SkillMastery).where(
                SkillMastery.learner_id == learner_id,
                SkillMastery.skill_id == rs.skill_id,
            )
            mastery_res = await self.session.execute(mastery_stmt)
            mastery = mastery_res.scalar_one_or_none()

            # Query evidence count
            evidence_cnt_stmt = select(func.count(SkillEvidence.id)).where(
                SkillEvidence.learner_id == learner_id,
                SkillEvidence.skill_id == rs.skill_id,
            )
            evidence_cnt = (await self.session.execute(evidence_cnt_stmt)).scalar() or 0

            skill_items.append(
                LearnerSkillStateItem(
                    skill_id=rs.skill_id,
                    skill_name=rs.skill.name if rs.skill else "Unknown Skill",
                    required_level=rs.required_level,
                    role_importance=rs.importance,
                    mastery_score=mastery.mastery_score if mastery else 0.0,
                    confidence=mastery.confidence if mastery else 0.0,
                    evidence_count=evidence_cnt,
                    last_assessed_at=mastery.last_assessed_at if mastery else None,
                )
            )

        return LearnerSkillStateResponse(
            learner_id=learner_id,
            goal_id=goal_id,
            target_role=target_role_name,
            skills=skill_items,
        )

    async def _check_skills_sufficient_confidence(
        self,
        learner_id: UUID,
        goal_id: UUID,
    ) -> bool:
        goal = await self.session.get(Goal, goal_id)
        if not goal:
            return False

        rs_stmt = select(RoleSkill.skill_id).where(RoleSkill.role_id == goal.target_role_id)
        skill_ids = (await self.session.execute(rs_stmt)).scalars().all()
        if not skill_ids:
            return False

        mastery_stmt = select(SkillMastery).where(
            SkillMastery.learner_id == learner_id,
            SkillMastery.skill_id.in_(skill_ids),
        )
        masteries = (await self.session.execute(mastery_stmt)).scalars().all()
        if len(masteries) < len(skill_ids):
            return False

        return all(m.confidence >= TARGET_SKILL_CONFIDENCE_THRESHOLD for m in masteries)

    async def _complete_session(self, diag_session: DiagnosticSession, reason: str) -> None:
        diag_session.status = SESSION_STATUS_COMPLETED
        diag_session.completed_at = datetime.now(timezone.utc)
        diag_session.session_metadata = {
            **(diag_session.session_metadata or {}),
            "termination_reason": reason,
        }
        await self.session.commit()

    @staticmethod
    def _to_session_response(diag_session: DiagnosticSession) -> DiagnosticSessionResponse:
        return DiagnosticSessionResponse(
            session_id=diag_session.id,
            learner_id=diag_session.learner_id,
            goal_id=diag_session.goal_id,
            status=diag_session.status,
            question_count=diag_session.question_count,
            max_questions=diag_session.max_questions,
            started_at=diag_session.started_at,
            completed_at=diag_session.completed_at,
            session_metadata=diag_session.session_metadata,
        )

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.models.assessment_question import AssessmentQuestion
from app.models.learning_activity_attempt import LearningActivityAttempt
from app.models.learning_path_node import LearningPathNode
from app.models.mastery_check_attempt import MasteryCheckAttempt
from app.models.mastery_outcome import MasteryOutcome
from app.models.skill import Skill
from app.models.skill_mastery import SkillMastery
from app.models.skill_resource import SkillResource
from app.schemas.proof_of_mastery import (
    ActivityAttemptResponse,
    MasteryCheckAnswerSubmission,
    MasteryCheckQuestionItem,
    ProofOfMasteryOutcomeResponse,
    SkillMasteryOutcomeItem,
    StartMasteryCheckResponse,
)
from app.services.answer_evaluation import LLMEvaluator
from app.services.mastery_engine import MasteryEngine
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ProofOfMasteryService:
    """Service orchestrating closed-loop learning activity tracking and proof-of-mastery evaluation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.mastery_engine = MasteryEngine(session)
        self.evaluator = LLMEvaluator()

    async def start_activity_attempt(
        self,
        learner_id: UUID,
        learning_path_node_id: UUID,
        idempotency_key: str | None = None,
    ) -> ActivityAttemptResponse:
        now = datetime.now(timezone.utc)

        # 1. Idempotency check
        if idempotency_key:
            existing_stmt = select(LearningActivityAttempt).where(
                LearningActivityAttempt.learner_id == learner_id,
                LearningActivityAttempt.idempotency_key == idempotency_key,
            ).options(
                selectinload(LearningActivityAttempt.resource),
            )
            existing_res = await self.session.execute(existing_stmt)
            existing_attempt = existing_res.scalar_one_or_none()
            if existing_attempt:
                return self._to_activity_response(existing_attempt)

        # 2. Validate node and ownership
        node_stmt = (
            select(LearningPathNode)
            .where(LearningPathNode.id == learning_path_node_id)
            .options(
                selectinload(LearningPathNode.learning_path),
                selectinload(LearningPathNode.resource),
            )
        )
        node_res = await self.session.execute(node_stmt)
        node = node_res.scalar_one_or_none()

        # Fallback: if node not found directly by ID, check active/latest path for matching resource or first node
        if not node:
            from app.models.learning_path import LearningPath
            fallback_stmt = (
                select(LearningPathNode)
                .join(LearningPath, LearningPathNode.learning_path_id == LearningPath.id)
                .where(
                    LearningPath.learner_id == learner_id,
                    LearningPath.status.in_(["active", "draft"]),
                    (LearningPathNode.resource_id == learning_path_node_id) | (LearningPathNode.id == learning_path_node_id),
                )
                .options(
                    selectinload(LearningPathNode.learning_path),
                    selectinload(LearningPathNode.resource),
                )
                .order_by(
                    (LearningPath.status == "active").desc(),
                    LearningPath.updated_at.desc(),
                )
            )
            node = (await self.session.execute(fallback_stmt)).scalars().first()

        if not node:
            from app.models.learning_path import LearningPath
            active_first_stmt = (
                select(LearningPathNode)
                .join(LearningPath, LearningPathNode.learning_path_id == LearningPath.id)
                .where(
                    LearningPath.learner_id == learner_id,
                )
                .options(
                    selectinload(LearningPathNode.learning_path),
                    selectinload(LearningPathNode.resource),
                )
                .order_by(
                    (LearningPath.status == "active").desc(),
                    LearningPath.updated_at.desc(),
                    LearningPathNode.sequence.asc(),
                )
            )
            node = (await self.session.execute(active_first_stmt)).scalars().first()

        if not node:
            raise ValueError(f"Learning path node '{learning_path_node_id}' not found.")

        if node.learning_path.learner_id != learner_id:
            raise ValueError("Learner does not own this learning path node.")

        # Ensure the underlying learning path is marked active if it was draft
        if node.learning_path.status != "active":
            node.learning_path.status = "active"
            await self.session.flush()


        # Check existing active/draft attempt to enforce idempotency
        existing_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.learner_id == learner_id,
            LearningActivityAttempt.learning_path_node_id == learning_path_node_id,
            LearningActivityAttempt.status.in_(["started", "draft"]),
        ).options(selectinload(LearningActivityAttempt.resource))
        existing_res = await self.session.execute(existing_stmt)
        existing_attempt = existing_res.scalars().first()
        if existing_attempt:
            return self._to_activity_response(existing_attempt)

        # 3. Count prior attempts
        prior_cnt_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.learner_id == learner_id,
            LearningActivityAttempt.learning_path_node_id == node.id,
        )
        prior_res = await self.session.execute(prior_cnt_stmt)
        attempt_num = len(prior_res.scalars().all()) + 1


        # 4. Create attempt record
        attempt = LearningActivityAttempt(
            learner_id=learner_id,
            learning_path_id=node.learning_path_id,
            learning_path_node_id=node.id,
            resource_id=node.resource_id,
            status="started",
            started_at=now,
            attempt_number=attempt_num,
            idempotency_key=idempotency_key,
            completion_percentage=0.0,
        )
        self.session.add(attempt)
        await self.session.flush()
        await self.session.commit()

        # Reload with relationships
        reload_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.id == attempt.id
        ).options(selectinload(LearningActivityAttempt.resource))
        loaded_attempt = (await self.session.execute(reload_stmt)).scalar_one()

        return self._to_activity_response(loaded_attempt)

    async def save_activity_draft(
        self,
        learner_id: UUID,
        attempt_id: UUID,
        submission_data: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> ActivityAttemptResponse:
        attempt_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.id == attempt_id
        ).options(selectinload(LearningActivityAttempt.resource))
        attempt_res = await self.session.execute(attempt_stmt)
        attempt = attempt_res.scalar_one_or_none()

        if not attempt:
            raise ValueError(f"Activity attempt '{attempt_id}' not found.")
        if attempt.learner_id != learner_id:
            raise ValueError("Learner does not own this activity attempt.")

        meta = attempt.metadata_json or {}
        meta["submission_data"] = submission_data
        attempt.metadata_json = meta
        if attempt.status == "started":
            attempt.status = "draft"

        await self.session.flush()
        return self._to_activity_response(attempt)

    async def complete_activity_attempt(
        self,
        learner_id: UUID,
        attempt_id: UUID,
        time_spent_minutes: int | None = None,
        completion_percentage: float = 100.0,
        submission_data: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> ActivityAttemptResponse:
        now = datetime.now(timezone.utc)
        attempt_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.id == attempt_id
        ).options(selectinload(LearningActivityAttempt.resource))
        attempt_res = await self.session.execute(attempt_stmt)
        attempt = attempt_res.scalar_one_or_none()

        if not attempt:
            raise ValueError(f"Activity attempt '{attempt_id}' not found.")
        if attempt.learner_id != learner_id:
            raise ValueError("Learner does not own this activity attempt.")

        if submission_data:
            meta = attempt.metadata_json or {}
            meta["submission_data"] = submission_data
            attempt.metadata_json = meta

        # Completion update: SkillMastery remains UNCHANGED!
        attempt.status = "completed"
        attempt.completed_at = now
        attempt.completion_percentage = completion_percentage
        if time_spent_minutes and time_spent_minutes > 0:
            attempt.time_spent_minutes = time_spent_minutes

        await self.session.flush()
        return self._to_activity_response(attempt)


    async def get_activity_attempt(
        self,
        attempt_id: UUID,
        learner_id: UUID,
    ) -> ActivityAttemptResponse:
        attempt_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.id == attempt_id
        ).options(selectinload(LearningActivityAttempt.resource))
        attempt_res = await self.session.execute(attempt_stmt)
        attempt = attempt_res.scalar_one_or_none()

        if not attempt:
            raise ValueError(f"Activity attempt '{attempt_id}' not found.")
        if attempt.learner_id != learner_id:
            raise ValueError("Learner does not own this activity attempt.")

        return self._to_activity_response(attempt)

    async def start_mastery_check(
        self,
        learner_id: UUID,
        activity_attempt_id: UUID,
        idempotency_key: str | None = None,
    ) -> StartMasteryCheckResponse:
        now = datetime.now(timezone.utc)

        # 1. Fetch & validate activity attempt
        attempt_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.id == activity_attempt_id
        ).options(
            selectinload(LearningActivityAttempt.learning_path_node).selectinload(LearningPathNode.skill)
        )
        attempt_res = await self.session.execute(attempt_stmt)
        attempt = attempt_res.scalar_one_or_none()

        if not attempt:
            raise ValueError(f"Activity attempt '{activity_attempt_id}' not found.")
        if attempt.learner_id != learner_id:
            raise ValueError("Learner does not own this activity attempt.")

        # 2. Find target skills addressed by learning activity node
        node = attempt.learning_path_node
        target_skill_ids: set[UUID] = set()
        if node.skill_id:
            target_skill_ids.add(node.skill_id)

        sr_stmt = select(SkillResource).where(SkillResource.resource_id == attempt.resource_id)
        sr_res = await self.session.execute(sr_stmt)
        for sr in sr_res.scalars().all():
            target_skill_ids.add(sr.skill_id)

        if not target_skill_ids:
            raise ValueError("No target skills associated with this activity.")

        # 3. Find matching assessment questions
        q_stmt = select(AssessmentQuestion).where(AssessmentQuestion.skill_id.in_(list(target_skill_ids)))
        q_res = await self.session.execute(q_stmt)
        questions = q_res.scalars().all()

        if not questions:
            # Fallback query: any questions
            fallback_stmt = select(AssessmentQuestion).limit(3)
            questions = (await self.session.execute(fallback_stmt)).scalars().all()

        # 4. Fetch skill names
        skills_stmt = select(Skill).where(Skill.id.in_(list(target_skill_ids)))
        skills_res = await self.session.execute(skills_stmt)
        skills_map = {s.id: s.name for s in skills_res.scalars().all()}

        # 5. Reuse existing active/started check for this activity attempt or check idempotency
        existing_active_check_stmt = select(MasteryCheckAttempt).where(
            MasteryCheckAttempt.learner_id == learner_id,
            MasteryCheckAttempt.activity_attempt_id == activity_attempt_id,
            MasteryCheckAttempt.status == "started",
        ).order_by(MasteryCheckAttempt.started_at.desc())
        existing_active_check = (await self.session.execute(existing_active_check_stmt)).scalars().first()
        if existing_active_check:
            q_items = self._to_question_items(questions, skills_map)
            return StartMasteryCheckResponse(
                check_id=existing_active_check.id,
                activity_attempt_id=existing_active_check.activity_attempt_id,
                learning_path_node_id=existing_active_check.learning_path_node_id,
                status=existing_active_check.status,
                started_at=existing_active_check.started_at,
                attempt_number=existing_active_check.attempt_number,
                questions=q_items,
            )

        if idempotency_key:
            existing_check_stmt = select(MasteryCheckAttempt).where(
                MasteryCheckAttempt.learner_id == learner_id,
                MasteryCheckAttempt.idempotency_key == idempotency_key,
            )
            existing_check = (await self.session.execute(existing_check_stmt)).scalar_one_or_none()
            if existing_check:
                q_items = self._to_question_items(questions, skills_map)
                return StartMasteryCheckResponse(
                    check_id=existing_check.id,
                    activity_attempt_id=existing_check.activity_attempt_id,
                    learning_path_node_id=existing_check.learning_path_node_id,
                    status=existing_check.status,
                    started_at=existing_check.started_at,
                    attempt_number=existing_check.attempt_number,
                    questions=q_items,
                )

        prior_checks_stmt = select(MasteryCheckAttempt).where(
            MasteryCheckAttempt.learner_id == learner_id,
            MasteryCheckAttempt.activity_attempt_id == activity_attempt_id,
        )
        check_attempt_num = len((await self.session.execute(prior_checks_stmt)).scalars().all()) + 1

        # 6. Create MasteryCheckAttempt record
        check_attempt = MasteryCheckAttempt(
            learner_id=learner_id,
            activity_attempt_id=activity_attempt_id,
            learning_path_node_id=attempt.learning_path_node_id,
            status="started",
            started_at=now,
            attempt_number=check_attempt_num,
            idempotency_key=idempotency_key,
        )
        self.session.add(check_attempt)
        await self.session.flush()
        await self.session.commit()

        q_items = self._to_question_items(questions, skills_map)
        return StartMasteryCheckResponse(
            check_id=check_attempt.id,
            activity_attempt_id=activity_attempt_id,
            learning_path_node_id=attempt.learning_path_node_id,
            status="started",
            started_at=now,
            attempt_number=check_attempt_num,
            questions=q_items,
        )

    async def get_active_mastery_check(
        self,
        learner_id: UUID,
        activity_attempt_id: UUID,
    ) -> StartMasteryCheckResponse | None:
        stmt = select(MasteryCheckAttempt).where(
            MasteryCheckAttempt.learner_id == learner_id,
            MasteryCheckAttempt.activity_attempt_id == activity_attempt_id,
        ).order_by(MasteryCheckAttempt.started_at.desc())
        check = (await self.session.execute(stmt)).scalars().first()
        if not check:
            return None

        attempt_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.id == activity_attempt_id
        ).options(selectinload(LearningActivityAttempt.learning_path_node))
        attempt = (await self.session.execute(attempt_stmt)).scalar_one_or_none()
        if not attempt:
            return None

        target_skill_ids: set[UUID] = set()
        if attempt.learning_path_node and attempt.learning_path_node.skill_id:
            target_skill_ids.add(attempt.learning_path_node.skill_id)

        sr_stmt = select(SkillResource).where(SkillResource.resource_id == attempt.resource_id)
        sr_res = await self.session.execute(sr_stmt)
        for sr in sr_res.scalars().all():
            target_skill_ids.add(sr.skill_id)

        q_stmt = select(AssessmentQuestion).where(AssessmentQuestion.skill_id.in_(list(target_skill_ids)))
        questions = (await self.session.execute(q_stmt)).scalars().all()
        if not questions:
            fallback_stmt = select(AssessmentQuestion).limit(3)
            questions = (await self.session.execute(fallback_stmt)).scalars().all()

        skills_stmt = select(Skill).where(Skill.id.in_(list(target_skill_ids)))
        skills_map = {s.id: s.name for s in (await self.session.execute(skills_stmt)).scalars().all()}

        q_items = self._to_question_items(questions, skills_map)
        return StartMasteryCheckResponse(
            check_id=check.id,
            activity_attempt_id=check.activity_attempt_id,
            learning_path_node_id=check.learning_path_node_id,
            status=check.status,
            started_at=check.started_at,
            attempt_number=check.attempt_number,
            questions=q_items,
        )

    async def submit_mastery_check(
        self,
        learner_id: UUID,
        check_id: UUID,
        answers: list[MasteryCheckAnswerSubmission],
        idempotency_key: str | None = None,
    ) -> ProofOfMasteryOutcomeResponse:
        now = datetime.now(timezone.utc)

        # 1. Fetch & validate check attempt
        check_stmt = select(MasteryCheckAttempt).where(
            MasteryCheckAttempt.id == check_id
        ).options(
            selectinload(MasteryCheckAttempt.activity_attempt),
        )
        check_res = await self.session.execute(check_stmt)
        check = check_res.scalar_one_or_none()

        if not check:
            raise ValueError(f"Mastery check attempt '{check_id}' not found.")
        if check.learner_id != learner_id:
            raise ValueError("Learner does not own this mastery check attempt.")

        # 2. Idempotency check: if attempt is already completed or outcomes already generated, return them
        if check.status == "completed" or idempotency_key:
            existing_outcomes_stmt = select(MasteryOutcome).where(
                MasteryOutcome.learner_id == learner_id,
                MasteryOutcome.mastery_check_id == check_id,
            ).options(selectinload(MasteryOutcome.skill))
            existing_outcomes = (await self.session.execute(existing_outcomes_stmt)).scalars().all()
            if existing_outcomes:
                return self._to_outcome_response(check.activity_attempt_id, check_id, learner_id, now, existing_outcomes)

        # 3. Collect target skills from questions
        answer_map = {ans.question_id: ans.learner_answer for ans in answers}
        q_stmt = select(AssessmentQuestion).where(AssessmentQuestion.id.in_(list(answer_map.keys())))
        questions = (await self.session.execute(q_stmt)).scalars().all()

        target_skill_ids = {q.skill_id for q in questions}

        # 4. Snapshot BEFORE mastery and confidence levels
        before_states: dict[UUID, tuple[float, float]] = {}
        for s_id in target_skill_ids:
            sm_stmt = select(SkillMastery).where(
                SkillMastery.learner_id == learner_id,
                SkillMastery.skill_id == s_id,
            )
            sm = (await self.session.execute(sm_stmt)).scalar_one_or_none()
            b_m = sm.mastery_score if sm else 0.0
            b_c = sm.confidence if sm else 0.0
            before_states[s_id] = (b_m, b_c)

        # 5. Evaluate each answer, compute evidence quality, and update MasteryEngine
        skill_evaluations: dict[UUID, list[tuple[float, float, float]]] = {}
        for q in questions:
            learner_ans = answer_map.get(q.id, "")
            evaluation = await self.evaluator.evaluate_answer(q, learner_ans)

            # Compute Evidence Quality Formula
            norm_diff_factor = 0.5 + 0.5 * max(0.0, min(1.0, (q.difficulty - 1.0) / 4.0))
            ev_quality = evaluation.score * norm_diff_factor * evaluation.rubric_coverage

            # Update MasteryEngine (persists SkillEvidence & updates SkillMastery)
            _, _ = await self.mastery_engine.record_evidence_and_update_mastery(
                learner_id=learner_id,
                skill_id=q.skill_id,
                question=q,
                evaluation=evaluation,
                evidence_type="proof_of_mastery",
                source_id=str(check_id),
            )

            skill_evaluations.setdefault(q.skill_id, []).append((evaluation.score, ev_quality, evaluation.confidence))

        # 6. Build AFTER metrics, Proof Strength, and Outcome Classifications per skill
        outcome_records: list[MasteryOutcome] = []

        for s_id in target_skill_ids:
            b_mastery, b_conf = before_states[s_id]

            # Fetch AFTER state from updated SkillMastery
            sm_stmt = select(SkillMastery).where(
                SkillMastery.learner_id == learner_id,
                SkillMastery.skill_id == s_id,
            )
            sm_after = (await self.session.execute(sm_stmt)).scalar_one()

            a_mastery = sm_after.mastery_score
            a_conf = sm_after.confidence
            m_delta = round(a_mastery - b_mastery, 4)
            c_delta = round(a_conf - b_conf, 4)

            evals = skill_evaluations.get(s_id, [(0.0, 0.0, 0.5)])
            avg_score = round(sum(e[0] for e in evals) / len(evals), 4)
            avg_quality = round(sum(e[1] for e in evals) / len(evals), 4)

            # Proof Strength Formula
            proof_str = round(avg_quality * min(1.0, 0.5 + 0.5 * a_conf), 4)

            # Result Classification
            if a_mastery >= 0.70 and m_delta > 0.01 and proof_str >= 0.40:
                classification = "demonstrated"
                exp = f"Evidence indicates improvement after the learning activity. Mastery increased from {round(b_mastery*100)}% to {round(a_mastery*100)}% (+{round(m_delta*100)} pts)."
            elif m_delta > 0.01:
                classification = "improving"
                exp = f"Progress observed. Mastery increased from {round(b_mastery*100)}% to {round(a_mastery*100)}% (+{round(m_delta*100)} pts)."
            elif m_delta < -0.02:
                classification = "regression"
                exp = f"Assessment score was lower than current estimate. Mastery adjusted from {round(b_mastery*100)}% to {round(a_mastery*100)}% ({round(m_delta*100)} pts)."
            elif proof_str < 0.30:
                classification = "insufficient_evidence"
                exp = f"Current evidence is insufficient to demonstrate mastery improvement (Proof Strength: {proof_str})."
            else:
                classification = "no_improvement"
                exp = f"Mastery estimate remains unchanged at {round(a_mastery*100)}% after the activity."

            outcome = MasteryOutcome(
                learner_id=learner_id,
                activity_attempt_id=check.activity_attempt_id,
                mastery_check_id=check_id,
                skill_id=s_id,
                before_mastery=round(b_mastery, 4),
                after_mastery=round(a_mastery, 4),
                mastery_delta=m_delta,
                before_confidence=round(b_conf, 4),
                after_confidence=round(a_conf, 4),
                confidence_delta=c_delta,
                evidence_score=avg_score,
                evidence_quality=avg_quality,
                proof_strength=proof_str,
                classification=classification,
                explanation=exp,
            )
            self.session.add(outcome)
            outcome_records.append(outcome)

        # 7. Update MasteryCheckAttempt status
        check.status = "completed"
        check.completed_at = now
        await self.session.flush()
        await self.session.commit()

        # Reload outcomes with relationships
        reload_outcomes_stmt = select(MasteryOutcome).where(
            MasteryOutcome.mastery_check_id == check_id
        ).options(selectinload(MasteryOutcome.skill))
        loaded_outcomes = (await self.session.execute(reload_outcomes_stmt)).scalars().all()

        return self._to_outcome_response(check.activity_attempt_id, check_id, learner_id, now, loaded_outcomes)

    async def get_attempt_outcome(
        self,
        learner_id: UUID,
        activity_attempt_id: UUID,
    ) -> ProofOfMasteryOutcomeResponse:
        attempt_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.id == activity_attempt_id
        )
        attempt = (await self.session.execute(attempt_stmt)).scalar_one_or_none()
        if not attempt:
            raise ValueError(f"Activity attempt '{activity_attempt_id}' not found.")
        if attempt.learner_id != learner_id:
            raise ValueError("Learner does not own this activity attempt.")

        outcomes_stmt = select(MasteryOutcome).where(
            MasteryOutcome.activity_attempt_id == activity_attempt_id
        ).options(selectinload(MasteryOutcome.skill))
        outcomes = (await self.session.execute(outcomes_stmt)).scalars().all()

        if not outcomes:
            raise ValueError("No proof-of-mastery outcome generated for this activity attempt yet.")

        check_id = outcomes[0].mastery_check_id
        now = outcomes[0].created_at or datetime.now(timezone.utc)
        return self._to_outcome_response(activity_attempt_id, check_id, learner_id, now, outcomes)

    def _to_activity_response(self, attempt: LearningActivityAttempt) -> ActivityAttemptResponse:
        r_title = attempt.resource.title if attempt.resource else f"Activity Step {attempt.attempt_number}"
        return ActivityAttemptResponse(
            id=attempt.id,
            learner_id=attempt.learner_id,
            learning_path_id=attempt.learning_path_id,
            learning_path_node_id=attempt.learning_path_node_id,
            resource_id=attempt.resource_id,
            resource_title=r_title,
            status=attempt.status,
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            time_spent_minutes=attempt.time_spent_minutes,
            completion_percentage=attempt.completion_percentage,
            attempt_number=attempt.attempt_number,
            submission_data=attempt.metadata_json.get("submission_data") if attempt.metadata_json and isinstance(attempt.metadata_json, dict) else None,
        )


    def _to_question_items(
        self, questions: Sequence[AssessmentQuestion], skills_map: dict[UUID, str]
    ) -> list[MasteryCheckQuestionItem]:
        items: list[MasteryCheckQuestionItem] = []
        for q in questions:
            s_name = skills_map.get(q.skill_id, "Target Skill")
            opts = None
            if q.expected_answer and isinstance(q.expected_answer, dict):
                opts = q.expected_answer.get("options")
            items.append(
                MasteryCheckQuestionItem(
                    question_id=q.id,
                    skill_id=q.skill_id,
                    skill_name=s_name,
                    prompt=q.prompt,
                    question_type=q.question_type,
                    difficulty=q.difficulty,
                    options=opts,
                )
            )
        return items

    def _to_outcome_response(
        self,
        activity_attempt_id: UUID,
        mastery_check_id: UUID | None,
        learner_id: UUID,
        evaluated_at: datetime,
        outcomes: Sequence[MasteryOutcome],
    ) -> ProofOfMasteryOutcomeResponse:
        skill_items: list[SkillMasteryOutcomeItem] = []
        classifications = [o.classification for o in outcomes]

        if "demonstrated" in classifications:
            overall_class = "demonstrated"
            overall_exp = "Evidence indicates demonstrated mastery improvement following the learning activity."
        elif "improving" in classifications:
            overall_class = "improving"
            overall_exp = "Evidence indicates positive learning progress following the activity."
        elif "regression" in classifications:
            overall_class = "regression"
            overall_exp = "Evidence indicates mastery regression on post-learning evaluation."
        elif "insufficient_evidence" in classifications:
            overall_class = "insufficient_evidence"
            overall_exp = "Current evidence is insufficient to confirm mastery improvement."
        else:
            overall_class = "no_improvement"
            overall_exp = "Mastery estimate remains unchanged after activity completion."

        for o in outcomes:
            s_name = o.skill.name if o.skill else "Target Skill"
            skill_items.append(
                SkillMasteryOutcomeItem(
                    skill_id=o.skill_id,
                    skill_name=s_name,
                    before_mastery=o.before_mastery,
                    after_mastery=o.after_mastery,
                    mastery_delta=o.mastery_delta,
                    before_confidence=o.before_confidence,
                    after_confidence=o.after_confidence,
                    confidence_delta=o.confidence_delta,
                    evidence_score=o.evidence_score,
                    evidence_quality=o.evidence_quality,
                    proof_strength=o.proof_strength,
                    classification=o.classification,
                    explanation=o.explanation,
                )
            )

        return ProofOfMasteryOutcomeResponse(
            activity_attempt_id=activity_attempt_id,
            mastery_check_id=mastery_check_id,
            learner_id=learner_id,
            evaluated_at=evaluated_at,
            overall_classification=overall_class,
            overall_explanation=overall_exp,
            skill_outcomes=skill_items,
        )

from datetime import datetime, timezone
from uuid import UUID

from app.models.assessment_question import AssessmentQuestion
from app.models.skill_evidence import SkillEvidence
from app.models.skill_mastery import SkillMastery
from app.schemas.diagnostic import AnswerEvaluation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class MasteryEngine:
    """Deterministic, bounded incremental mastery and confidence estimation engine."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_evidence_and_update_mastery(
        self,
        learner_id: UUID,
        skill_id: UUID,
        question: AssessmentQuestion,
        evaluation: AnswerEvaluation,
        evidence_type: str = "diagnostic_assessment",
        source_id: str | None = None,
    ) -> tuple[SkillEvidence, SkillMastery]:
        now = datetime.now(timezone.utc)
        evidence_strength = max(0.1, min(1.0, evaluation.confidence))

        # 1. Create and persist SkillEvidence record
        evidence = SkillEvidence(
            learner_id=learner_id,
            skill_id=skill_id,
            evidence_type=evidence_type,
            source_id=source_id or str(question.id),
            score=evaluation.score,
            confidence=evaluation.confidence,
            observed_at=now,
            metadata_json={
                "question_id": str(question.id),
                "difficulty": question.difficulty,
                "question_type": question.question_type,
                "is_correct": evaluation.is_correct,
                "rubric_coverage": evaluation.rubric_coverage,
                "misconception_code": evaluation.misconception_code,
                "feedback": evaluation.feedback,
            },
        )
        self.session.add(evidence)

        # 2. Fetch existing SkillMastery record
        mastery_stmt = select(SkillMastery).where(
            SkillMastery.learner_id == learner_id,
            SkillMastery.skill_id == skill_id,
        )
        mastery_res = await self.session.execute(mastery_stmt)
        mastery = mastery_res.scalar_one_or_none()

        prev_mastery = mastery.mastery_score if mastery else 0.0
        prev_confidence = mastery.confidence if mastery else 0.0

        # 3. Calculate mastery score update
        norm_diff = max(0.0, min(1.0, (question.difficulty - 1.0) / 4.0))

        if evaluation.is_correct:
            # Correct answer: target signal scales with question difficulty
            signal = 0.70 + 0.30 * norm_diff
        else:
            # Incorrect answer: target signal drops lower on easy questions
            signal = 0.30 * norm_diff

        # Weight factor decreases as prior confidence grows
        weight = evidence_strength * (1.0 - prev_confidence * 0.5) * 0.40
        new_mastery_score = prev_mastery * (1.0 - weight) + signal * weight
        new_mastery_score = max(0.0, min(1.0, round(new_mastery_score, 4)))

        # 4. Calculate confidence update
        delta_conf = 0.20 * evidence_strength * (1.0 - prev_confidence)

        # Consistency bonus if result aligns with current mastery direction
        is_consistent = (evaluation.is_correct and prev_mastery >= 0.5) or (
            not evaluation.is_correct and prev_mastery < 0.5
        )
        if is_consistent and prev_confidence > 0.0:
            delta_conf += 0.05 * (1.0 - prev_confidence)

        new_confidence = prev_confidence + delta_conf
        new_confidence = max(0.0, min(1.0, round(new_confidence, 4)))

        # 5. Update or insert SkillMastery record
        if not mastery:
            mastery = SkillMastery(
                learner_id=learner_id,
                skill_id=skill_id,
                mastery_score=new_mastery_score,
                confidence=new_confidence,
                last_assessed_at=now,
            )
            self.session.add(mastery)
        else:
            mastery.mastery_score = new_mastery_score
            mastery.confidence = new_confidence
            mastery.last_assessed_at = now

        await self.session.flush()
        return evidence, mastery

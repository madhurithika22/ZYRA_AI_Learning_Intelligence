import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.learner import Learner
    from app.models.learning_activity_attempt import LearningActivityAttempt
    from app.models.mastery_check_attempt import MasteryCheckAttempt
    from app.models.skill import Skill


class MasteryOutcome(Base, TimestampMixin):
    """Model recording measured proof-of-mastery outcomes, before/after metrics, and classifications."""

    __tablename__ = "mastery_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    learner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    activity_attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_activity_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mastery_check_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("mastery_check_attempts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    before_mastery: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    after_mastery: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    mastery_delta: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    before_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    after_confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    confidence_delta: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    evidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    evidence_quality: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    proof_strength: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    classification: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        # demonstrated, improving, insufficient_evidence, no_improvement, regression
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Relationships
    learner: Mapped["Learner"] = relationship("Learner")
    activity_attempt: Mapped["LearningActivityAttempt"] = relationship("LearningActivityAttempt")
    mastery_check: Mapped["MasteryCheckAttempt | None"] = relationship("MasteryCheckAttempt")
    skill: Mapped["Skill"] = relationship("Skill")

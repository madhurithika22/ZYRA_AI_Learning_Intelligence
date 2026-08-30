from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.diagnostic_response import DiagnosticResponse
    from app.models.goal import Goal
    from app.models.learner import Learner
    from app.models.skill import Skill


class DiagnosticSession(TimestampMixin, Base):
    """Represents an adaptive diagnostic assessment session for a learner's goal."""

    __tablename__ = "diagnostic_sessions"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    learner_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("learners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    goal_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="not_started",
    )

    current_skill_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
    )

    question_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    max_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    session_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    learner: Mapped["Learner"] = relationship("Learner")
    goal: Mapped["Goal"] = relationship("Goal")
    current_skill: Mapped["Skill | None"] = relationship("Skill")
    responses: Mapped[list["DiagnosticResponse"]] = relationship(
        "DiagnosticResponse",
        back_populates="session",
        cascade="all, delete-orphan",
    )

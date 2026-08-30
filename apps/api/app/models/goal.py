from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.learner import Learner
    from app.models.learning_path import LearningPath
    from app.models.role import Role


class Goal(TimestampMixin, Base):
    """Represents a learner's target outcome."""

    __tablename__ = "goals"

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

    target_role_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    objective: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    timeline_weeks: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    daily_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relationships
    learner: Mapped["Learner"] = relationship(
        "Learner",
        back_populates="goals",
    )

    target_role: Mapped["Role"] = relationship(
        "Role",
        back_populates="goals",
    )

    learning_paths: Mapped[list["LearningPath"]] = relationship(
        "LearningPath",
        back_populates="goal",
        cascade="all, delete-orphan",
    )

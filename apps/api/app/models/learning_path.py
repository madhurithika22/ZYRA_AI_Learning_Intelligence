from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.goal import Goal
    from app.models.learner import Learner
    from app.models.learning_path_node import LearningPathNode


class LearningPath(TimestampMixin, Base):
    """Represents a customized learning path generated for a learner goal."""

    __tablename__ = "learning_paths"

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

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    strategy: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="active",
    )

    estimated_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    expected_readiness: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    parent_path_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    generation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    change_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    parent_path: Mapped["LearningPath | None"] = relationship(
        "LearningPath",
        remote_side=[id],
    )

    # Relationships
    learner: Mapped["Learner"] = relationship(
        "Learner",
        back_populates="learning_paths",
    )

    goal: Mapped["Goal"] = relationship(
        "Goal",
        back_populates="learning_paths",
    )

    nodes: Mapped[list["LearningPathNode"]] = relationship(
        "LearningPathNode",
        back_populates="learning_path",
        cascade="all, delete-orphan",
        order_by="LearningPathNode.sequence",
    )

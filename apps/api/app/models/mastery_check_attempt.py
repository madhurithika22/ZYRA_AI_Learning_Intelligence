import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.learner import Learner
    from app.models.learning_activity_attempt import LearningActivityAttempt
    from app.models.learning_path_node import LearningPathNode


class MasteryCheckAttempt(Base, TimestampMixin):
    """Model tracking a post-learning verification assessment event."""

    __tablename__ = "mastery_check_attempts"

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
    learning_path_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_path_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="started",  # started, completed, failed
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
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )

    # Relationships
    learner: Mapped["Learner"] = relationship("Learner")
    activity_attempt: Mapped["LearningActivityAttempt"] = relationship("LearningActivityAttempt")
    learning_path_node: Mapped["LearningPathNode"] = relationship("LearningPathNode")

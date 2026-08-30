import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.learner import Learner
    from app.models.learning_path import LearningPath
    from app.models.learning_path_node import LearningPathNode
    from app.models.learning_resource import LearningResource


class LearningActivityAttempt(Base, TimestampMixin):
    """Model tracking a learner's engagement attempt with a learning path node activity."""

    __tablename__ = "learning_activity_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    learner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learners.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    learning_path_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    learning_path_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_path_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_resources.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="started",  # started, completed, abandoned
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
    time_spent_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    completion_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
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
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )

    # Relationships
    learner: Mapped["Learner"] = relationship("Learner")
    learning_path: Mapped["LearningPath"] = relationship("LearningPath")
    learning_path_node: Mapped["LearningPathNode"] = relationship("LearningPathNode")
    resource: Mapped["LearningResource"] = relationship("LearningResource")

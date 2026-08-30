from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.learner import Learner


class LearnerProfile(TimestampMixin, Base):
    """Represents learner-stated experience, preferences, and background metadata."""

    __tablename__ = "learner_profiles"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    learner_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("learners.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    experience_level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    preferred_learning_mode: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    weekly_availability_hours: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    stated_background: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    avatar_gender: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    avatar_variant: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    profile_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    learner: Mapped["Learner"] = relationship(
        "Learner",
        back_populates="profile",
    )

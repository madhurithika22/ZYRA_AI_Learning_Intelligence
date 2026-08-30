from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.learning_path import LearningPath
    from app.models.learning_resource import LearningResource
    from app.models.skill import Skill


class LearningPathNode(TimestampMixin, Base):
    """Represents a discrete sequential step or milestone within a learning path."""

    __tablename__ = "learning_path_nodes"
    __table_args__ = (
        UniqueConstraint("learning_path_id", "sequence", name="uq_path_node_sequence"),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    learning_path_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    resource_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("learning_resources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    skill_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    milestone_label: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    estimated_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    rationale: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source_node_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("learning_path_nodes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="pending",
    )

    # Relationships
    learning_path: Mapped["LearningPath"] = relationship(
        "LearningPath",
        back_populates="nodes",
    )

    resource: Mapped["LearningResource | None"] = relationship(
        "LearningResource",
        back_populates="learning_path_nodes",
    )

    skill: Mapped["Skill | None"] = relationship(
        "Skill",
    )

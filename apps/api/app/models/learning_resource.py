from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.learning_path_node import LearningPathNode
    from app.models.skill_resource import SkillResource


class LearningResource(TimestampMixin, Base):
    """Represents a resource that can be used in a learning path."""

    __tablename__ = "learning_resources"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(240),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    resource_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    difficulty: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    estimated_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    covered_skills: Mapped[list["SkillResource"]] = relationship(
        "SkillResource",
        back_populates="resource",
        cascade="all, delete-orphan",
    )

    learning_path_nodes: Mapped[list["LearningPathNode"]] = relationship(
        "LearningPathNode",
        back_populates="resource",
    )

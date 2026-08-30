from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.learning_resource import LearningResource
    from app.models.skill import Skill


class SkillResource(Base):
    """Associates a learning resource with a skill it teaches."""

    __tablename__ = "skill_resources"

    skill_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )

    resource_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("learning_resources.id", ondelete="CASCADE"),
        primary_key=True,
    )

    relevance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    # Relationships
    skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="learning_resources",
    )

    resource: Mapped["LearningResource"] = relationship(
        "LearningResource",
        back_populates="covered_skills",
    )

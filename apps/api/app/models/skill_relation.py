from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.skill import Skill


class SkillRelation(TimestampMixin, Base):
    """Represents a directed relationship between two skills."""

    __tablename__ = "skill_relations"
    __table_args__ = (
        UniqueConstraint(
            "source_skill_id",
            "target_skill_id",
            "relation_type",
            name="uq_skill_relation",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    source_skill_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    target_skill_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    relation_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    strength: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    # Relationships
    source_skill: Mapped["Skill"] = relationship(
        "Skill",
        foreign_keys=[source_skill_id],
        back_populates="prerequisite_sources",
    )

    target_skill: Mapped["Skill"] = relationship(
        "Skill",
        foreign_keys=[target_skill_id],
        back_populates="prerequisite_targets",
    )

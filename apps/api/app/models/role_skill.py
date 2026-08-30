from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.skill import Skill


class RoleSkill(Base):
    """Associates a skill with a target role and its importance."""

    __tablename__ = "role_skills"

    role_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    skill_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )

    importance: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    required_level: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    # Relationships
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="required_skills",
    )

    skill: Mapped["Skill"] = relationship(
        "Skill",
        back_populates="role_requirements",
    )

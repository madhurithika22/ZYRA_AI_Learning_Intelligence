from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.goal import Goal
    from app.models.role_skill import RoleSkill


class Role(TimestampMixin, Base):
    """Represents a target career or learning role."""

    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    goals: Mapped[list["Goal"]] = relationship(
        "Goal",
        back_populates="target_role",
    )

    required_skills: Mapped[list["RoleSkill"]] = relationship(
        "RoleSkill",
        back_populates="role",
        cascade="all, delete-orphan",
    )

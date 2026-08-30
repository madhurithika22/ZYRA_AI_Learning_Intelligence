from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.conversation_session import ConversationSession
    from app.models.goal import Goal
    from app.models.learner_profile import LearnerProfile
    from app.models.learning_path import LearningPath
    from app.models.skill_evidence import SkillEvidence
    from app.models.skill_mastery import SkillMastery
    from app.models.user_account import UserAccount


class Learner(TimestampMixin, Base):
    """Represents a learner using the platform."""

    __tablename__ = "learners"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    display_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
        index=True,
    )

    # Relationships
    user_account: Mapped["UserAccount | None"] = relationship(
        "UserAccount",
        back_populates="learner",
        uselist=False,
        cascade="all, delete-orphan",
    )

    profile: Mapped["LearnerProfile | None"] = relationship(
        "LearnerProfile",
        back_populates="learner",
        uselist=False,
        cascade="all, delete-orphan",
    )

    goals: Mapped[list["Goal"]] = relationship(
        "Goal",
        back_populates="learner",
        cascade="all, delete-orphan",
    )

    learning_paths: Mapped[list["LearningPath"]] = relationship(
        "LearningPath",
        back_populates="learner",
        cascade="all, delete-orphan",
    )

    skill_evidence: Mapped[list["SkillEvidence"]] = relationship(
        "SkillEvidence",
        back_populates="learner",
        cascade="all, delete-orphan",
    )

    skill_mastery: Mapped[list["SkillMastery"]] = relationship(
        "SkillMastery",
        back_populates="learner",
        cascade="all, delete-orphan",
    )

    conversation_sessions: Mapped[list["ConversationSession"]] = relationship(
        "ConversationSession",
        back_populates="learner",
        cascade="all, delete-orphan",
    )

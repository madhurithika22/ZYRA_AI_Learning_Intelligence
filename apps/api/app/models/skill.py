from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.assessment import Assessment
    from app.models.assessment_question import AssessmentQuestion
    from app.models.role_skill import RoleSkill
    from app.models.skill_evidence import SkillEvidence
    from app.models.skill_mastery import SkillMastery
    from app.models.skill_relation import SkillRelation
    from app.models.skill_resource import SkillResource


class Skill(TimestampMixin, Base):
    """Represents a canonical learner skill."""

    __tablename__ = "skills"

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

    difficulty: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    parent_skill_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    parent_skill: Mapped["Skill | None"] = relationship(
        "Skill",
        remote_side=[id],
        back_populates="child_skills",
    )

    child_skills: Mapped[list["Skill"]] = relationship(
        "Skill",
        back_populates="parent_skill",
    )

    role_requirements: Mapped[list["RoleSkill"]] = relationship(
        "RoleSkill",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    prerequisite_sources: Mapped[list["SkillRelation"]] = relationship(
        "SkillRelation",
        foreign_keys="[SkillRelation.source_skill_id]",
        back_populates="source_skill",
        cascade="all, delete-orphan",
    )

    prerequisite_targets: Mapped[list["SkillRelation"]] = relationship(
        "SkillRelation",
        foreign_keys="[SkillRelation.target_skill_id]",
        back_populates="target_skill",
        cascade="all, delete-orphan",
    )

    learning_resources: Mapped[list["SkillResource"]] = relationship(
        "SkillResource",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    assessments: Mapped[list["Assessment"]] = relationship(
        "Assessment",
        back_populates="skill",
    )

    assessment_questions: Mapped[list["AssessmentQuestion"]] = relationship(
        "AssessmentQuestion",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    skill_evidence: Mapped[list["SkillEvidence"]] = relationship(
        "SkillEvidence",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

    mastery_records: Mapped[list["SkillMastery"]] = relationship(
        "SkillMastery",
        back_populates="skill",
        cascade="all, delete-orphan",
    )

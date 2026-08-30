from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class GoalInterpretationRequest(BaseModel):
    """Request payload for natural language goal interpretation."""

    natural_language_goal: str = Field(
        ...,
        min_length=3,
        description="Free-form natural language goal statement from the learner.",
    )
    learner_id: UUID | None = Field(
        default=None,
        description="Optional learner ID if persisting or associating profile.",
    )


class GoalInterpretation(BaseModel):
    """Structured representation extracted from a natural language goal."""

    target_role: str = Field(
        ...,
        description="Extracted target career role or skill objective.",
    )
    objective: str = Field(
        ...,
        description="Normalized high-level learning objective.",
    )
    timeline_weeks: int | None = Field(
        default=None,
        description="Extracted target timeline in weeks.",
    )
    daily_minutes: int | None = Field(
        default=None,
        description="Extracted daily study time commitment in minutes.",
    )
    desired_outcome: str | None = Field(
        default=None,
        description="Extracted outcome focus (e.g. job_readiness, mastery, project).",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="List of identified learner constraints.",
    )
    stated_existing_skills: list[str] = Field(
        default_factory=list,
        description="Skills stated as known by the learner.",
    )
    ambiguities: list[str] = Field(
        default_factory=list,
        description="Unclear or ambiguous details flagged during extraction.",
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score of interpretation (0.0 to 1.0).",
    )

    @field_validator("timeline_weeks")
    @classmethod
    def validate_timeline_weeks(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("timeline_weeks must be a positive integer")
        return v

    @field_validator("daily_minutes")
    @classmethod
    def validate_daily_minutes(cls, v: int | None) -> int | None:
        if v is not None:
            if v <= 0:
                raise ValueError("daily_minutes must be greater than zero")
            if v > 1440:
                raise ValueError("daily_minutes cannot exceed 1440 minutes (24 hours)")
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class ResolvedRoleInfo(BaseModel):
    """Information regarding canonical database role resolution."""

    canonical_role_id: UUID | None = None
    canonical_role_name: str | None = None
    confidence: float = 1.0
    is_resolved: bool = False
    ambiguity_reason: str | None = None


class ResolvedSkillItem(BaseModel):
    """Canonical database skill item matched from learner statement."""

    skill_id: UUID
    name: str


class ResolvedSkillInfo(BaseModel):
    """Categorized resolution of learner-stated existing skills."""

    resolved_skills: list[ResolvedSkillItem] = Field(default_factory=list)
    unresolved_skills: list[str] = Field(default_factory=list)


class GoalIntelligenceResult(BaseModel):
    """Complete goal interpretation and database resolution result."""

    interpretation: GoalInterpretation
    resolved_role: ResolvedRoleInfo
    resolved_skills: ResolvedSkillInfo
    validation_status: str = Field(
        ...,
        description="'valid', 'invalid', or 'ambiguous'",
    )
    is_valid: bool = True
    validation_errors: list[str] = Field(default_factory=list)


class GoalCreationResponse(BaseModel):
    """Response returned upon successful transactional goal persistence."""

    goal_id: UUID
    learner_id: UUID
    target_role_id: UUID
    objective: str
    timeline_weeks: int | None = None
    daily_minutes: int | None = None
    intelligence_result: GoalIntelligenceResult

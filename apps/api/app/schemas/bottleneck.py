from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BottleneckExplanation(BaseModel):
    """Structured explanation detailing why a skill is identified as a learning bottleneck."""

    primary_reason: str
    evidence: list[str] = Field(default_factory=list)
    downstream_skills: list[str] = Field(default_factory=list)


class SkillGapItem(BaseModel):
    """Analyzed skill gap and bottleneck metrics for a single target role skill."""

    skill_id: UUID
    skill_name: str
    required_level: float
    mastery: float
    confidence: float
    gap: float
    role_importance: float
    dependency_impact: float
    uncertainty_factor: float
    bottleneck_score: float
    rank: int
    classification: str
    explanation: BottleneckExplanation


class BottleneckAnalysisResponse(BaseModel):
    """Complete ranked bottleneck analysis for a learner and target role goal."""

    learner_id: UUID
    goal_id: UUID
    target_role: str
    analyzed_at: datetime
    primary_bottleneck: SkillGapItem | None = None
    secondary_bottlenecks: list[SkillGapItem] = Field(default_factory=list)
    all_gaps: list[SkillGapItem] = Field(default_factory=list)

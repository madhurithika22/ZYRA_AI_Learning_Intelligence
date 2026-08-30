from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PathNodeResponse(BaseModel):
    """Represents a discrete step within an optimized learning path sequence."""

    id: UUID | None = None
    sequence: int
    resource_id: UUID | None = None
    resource_title: str
    resource_type: str
    resource_url: str | None = None
    skill_id: UUID | None = None
    skill_name: str
    estimated_minutes: int
    rationale: str


class PathStrategyOption(BaseModel):
    """Represents a single strategy-optimized learning path option."""

    path_id: UUID
    strategy: str
    name: str
    status: str
    feasible: bool
    estimated_minutes: int
    estimated_weeks: float
    total_resources: int
    target_skill_coverage: float
    bottleneck_coverage: float
    practical_value: float
    redundancy_score: float
    risk_score: float
    path_score: float
    explanation: str
    warning_message: str | None = None
    nodes: list[PathNodeResponse] = Field(default_factory=list)


class PathComparisonResponse(BaseModel):
    """Structured response presenting the 4 strategy-optimized learning path options."""

    learner_id: UUID
    goal_id: UUID
    target_role: str
    generated_at: datetime
    options: dict[str, PathStrategyOption] = Field(default_factory=dict)


class ActivatePathResponse(BaseModel):
    """Response returned when a learner activates a learning path strategy."""

    path_id: UUID
    learner_id: UUID
    goal_id: UUID
    strategy: str
    status: str
    activated_at: datetime
    message: str

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class ActionType(str, Enum):
    """Supported candidate action types."""

    LEARN = "LEARN"
    CONTINUE = "CONTINUE"
    MASTERY_CHECK = "MASTERY_CHECK"
    REASSESS = "REASSESS"
    PREREQUISITE_REVIEW = "PREREQUISITE_REVIEW"
    PROJECT = "PROJECT"
    SKIP = "SKIP"


class ActionMetrics(BaseModel):
    """Normalized metrics [0.0, 1.0] used for deterministic action scoring."""

    model_config = ConfigDict(from_attributes=True)

    gap_reduction: float = Field(ge=0.0, le=1.0, default=0.0)
    bottleneck_relevance: float = Field(ge=0.0, le=1.0, default=0.0)
    information_value: float = Field(ge=0.0, le=1.0, default=0.0)
    prerequisite_value: float = Field(ge=0.0, le=1.0, default=0.0)
    path_progress_value: float = Field(ge=0.0, le=1.0, default=0.0)
    evidence_value: float = Field(ge=0.0, le=1.0, default=0.0)
    practical_value: float = Field(ge=0.0, le=1.0, default=0.0)
    time_cost: float = Field(ge=0.0, le=1.0, default=0.0)
    redundancy: float = Field(ge=0.0, le=1.0, default=0.0)
    repetition_penalty: float = Field(ge=0.0, le=1.0, default=0.0)


class NextActionItem(BaseModel):
    """Candidate next action with score, rank, feasibility, and explanation."""

    model_config = ConfigDict(from_attributes=True)

    action_id: UUID = Field(default_factory=uuid4)
    rank: int = Field(ge=1, default=1)
    action_type: ActionType
    title: str
    target_skill_id: UUID | None = None
    target_skill_name: str
    resource_id: UUID | None = None
    path_node_id: UUID | None = None
    attempt_id: UUID | None = None
    check_id: UUID | None = None
    score: float = Field(ge=0.0)
    feasible: bool = True
    estimated_minutes: int = Field(ge=0, default=30)
    primary_reason: str
    supporting_reasons: list[str] = Field(default_factory=list)
    metrics_used: ActionMetrics
    constraints_considered: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)


class NextActionResponse(BaseModel):
    """Complete Next-Best-Action recommendation with confidence and top alternatives."""

    model_config = ConfigDict(from_attributes=True)

    learner_id: UUID
    goal_id: UUID | None = None
    selected_action: NextActionItem
    action_confidence: float = Field(ge=0.0, le=1.0)
    confidence_label: str  # HIGH, MEDIUM, LOW
    alternatives: list[NextActionItem] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NextActionCandidatesResponse(BaseModel):
    """Ranked list of all feasible candidate actions."""

    model_config = ConfigDict(from_attributes=True)

    learner_id: UUID
    goal_id: UUID | None = None
    candidates: list[NextActionItem] = Field(default_factory=list)

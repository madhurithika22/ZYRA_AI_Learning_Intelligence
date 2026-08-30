from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TwinFreshnessStatus(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    INCOMPLETE = "incomplete"


class TwinConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TwinFreshness(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: TwinFreshnessStatus
    generated_at: datetime
    latest_mastery_update_at: datetime | None = None
    latest_path_change_at: datetime | None = None


class TwinStateConfidence(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    level: TwinConfidenceLevel
    score: float = Field(..., ge=0.0, le=1.0)
    reason: str
    missing_dimensions: list[str] = Field(default_factory=list)


class TwinGoalSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    goal_id: UUID | None = None
    objective: str
    target_role_id: UUID | None = None
    target_role_name: str
    goal_skill_progress: float = Field(..., ge=0.0, le=1.0)
    target_skill_count: int
    skills_at_required: int
    skills_near_target: int
    skills_needing_work: int
    skills_uncertain: int
    evidence_count: int


class TwinSkillItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: UUID
    skill_name: str
    mastery: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    required: float = Field(..., ge=0.0, le=1.0)
    gap: float = Field(..., ge=0.0, le=1.0)
    progress_to_required: float = Field(..., ge=0.0, le=1.0)
    evidence_count: int
    status: str  # STRONG, ON_TRACK, GAP, UNCERTAIN


class TwinBottleneckSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill_id: UUID | None = None
    skill_name: str
    mastery_score: float = Field(..., ge=0.0, le=1.0)
    required_level: float = Field(..., ge=0.0, le=1.0)
    gap: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    dependency_impact: float = Field(..., ge=0.0)
    bottleneck_score: float = Field(..., ge=0.0)
    reason: str
    affected_skills: list[str] = Field(default_factory=list)


class TwinNextActionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action_type: str
    title: str
    target_skill_id: UUID | None = None
    target_skill_name: str
    resource_id: UUID | None = None
    node_id: UUID | None = None
    estimated_minutes: int
    action_confidence: float = Field(..., ge=0.0, le=1.0)
    score: float = Field(..., ge=0.0, le=1.0)
    primary_reason: str
    reasons: list[str] = Field(default_factory=list)


class TwinPathSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    path_id: UUID | None = None
    version: int
    name: str
    status: str
    completion_percentage: float = Field(..., ge=0.0, le=1.0)
    completed_nodes: int
    total_nodes: int
    remaining_minutes: int
    is_stale: bool
    replan_available: bool


class TwinReplanSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    should_replan: bool
    staleness_score: float = Field(..., ge=0.0, le=1.0)
    trigger_type: str | None = None
    rationale: str
    draft_path_id: UUID | None = None


class TwinRecentChangeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    change_type: str
    description: str
    timestamp: datetime
    impact_delta: str | None = None


class TwinEvidenceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_evidence_count: int
    recent_evidence_count: int
    last_assessed_at: datetime | None = None
    demonstrated_skills_count: int
    improving_skills_count: int
    insufficient_evidence_count: int
    recently_verified_skills: list[str] = Field(default_factory=list)


class DecisionTrace(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    learner_state_summary: dict[str, Any]
    skill_state_trace: list[dict[str, Any]]
    bottleneck_trace: dict[str, Any]
    next_action_trace: dict[str, Any]
    path_state_trace: dict[str, Any]
    replan_trace: dict[str, Any]


class LearningTwinResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    learner_id: UUID
    display_name: str
    goal: TwinGoalSummary
    path: TwinPathSummary | None = None
    skills: list[TwinSkillItem] = Field(default_factory=list)
    bottleneck: TwinBottleneckSummary | None = None
    next_action: TwinNextActionSummary | None = None
    replan: TwinReplanSummary | None = None
    recent_changes: list[TwinRecentChangeItem] = Field(default_factory=list)
    evidence_summary: TwinEvidenceSummary
    state_confidence: TwinStateConfidence
    state_completeness: float = Field(..., ge=0.0, le=1.0)
    freshness: TwinFreshness
    decision_trace: DecisionTrace | None = None

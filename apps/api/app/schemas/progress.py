from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PathProgressResponse(BaseModel):
    """Aggregate progress metrics for a learning path."""

    model_config = ConfigDict(from_attributes=True)

    path_id: UUID
    path_name: str
    total_nodes: int = Field(ge=0)
    completed_nodes: int = Field(ge=0)
    in_progress_nodes: int = Field(ge=0)
    remaining_nodes: int = Field(ge=0)
    completion_percentage: float = Field(ge=0.0, le=1.0)
    total_estimated_minutes: int = Field(ge=0)
    completed_minutes: int = Field(ge=0)
    remaining_minutes: int = Field(ge=0)
    time_completion_percentage: float = Field(ge=0.0, le=1.0)


class NodeProgressItem(BaseModel):
    """Detailed progress status for an individual node on a learning path."""

    model_config = ConfigDict(from_attributes=True)

    sequence: int
    path_node_id: UUID
    resource_id: UUID | None
    resource_title: str
    target_skill_id: UUID | None
    target_skill_name: str
    estimated_minutes: int
    status: str  # completed, in_progress, pending
    attempt_id: UUID | None = None
    completion_percentage: float = Field(ge=0.0, le=1.0, default=0.0)
    time_spent_minutes: int | None = None
    proof_status: str  # proven, attempted, unproven
    before_mastery: float | None = None
    after_mastery: float | None = None
    mastery_delta: float | None = None


class SkillProgressItem(BaseModel):
    """Progress metrics for a single target-role skill."""

    model_config = ConfigDict(from_attributes=True)

    skill_id: UUID
    skill_name: str
    required_level: float = Field(ge=0.0, le=1.0)
    role_importance: float = Field(ge=0.0)
    current_mastery: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    initial_mastery: float = Field(ge=0.0, le=1.0)
    mastery_delta: float
    progress_to_required: float = Field(ge=0.0, le=1.0)
    evidence_count: int = Field(ge=0)
    last_evidence_at: datetime | None = None


class RecentChangeItem(BaseModel):
    """Deterministic summary of a recent mastery change for a skill."""

    model_config = ConfigDict(from_attributes=True)

    skill_id: UUID
    skill_name: str
    before_mastery: float
    after_mastery: float
    mastery_delta: float
    classification: str  # improving, stable, regression, insufficient_evidence
    explanation: str
    evaluated_at: datetime


class TimelineProgressResponse(BaseModel):
    """Learning pace and time budget progress metrics."""

    model_config = ConfigDict(from_attributes=True)

    timeline_weeks: int | None = None
    daily_minutes: int | None = None
    total_available_minutes: int | None = None
    actual_time_spent_minutes: int = Field(ge=0)
    path_estimated_remaining_minutes: int = Field(ge=0)
    descriptive_pace: float = Field(ge=0.0)
    pace_description: str


class GoalSkillProgressResponse(BaseModel):
    """Aggregated goal skill progress proxy and bottleneck state."""

    model_config = ConfigDict(from_attributes=True)

    goal_id: UUID
    target_role_id: UUID
    target_role_name: str
    total_target_skills: int
    skills_at_required: int
    skills_near_required: int
    skills_low_confidence: int
    goal_skill_progress: float = Field(ge=0.0, le=1.0)
    path_completion_percentage: float = Field(ge=0.0, le=1.0)
    total_evidence_count: int = Field(ge=0)


class SkillHistoryItem(BaseModel):
    """Chronological event entry in a skill's mastery history."""

    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    event_type: str  # diagnostic, mastery_check, activity_attempt
    title: str
    before_mastery: float
    after_mastery: float
    mastery_delta: float
    confidence: float
    evidence_type: str | None = None
    evidence_quality: float | None = None
    proof_strength: float | None = None


class LearnerProgressSummary(BaseModel):
    """Complete aggregated progress summary for a learner."""

    model_config = ConfigDict(from_attributes=True)

    learner_id: UUID
    active_goal_id: UUID | None = None
    target_role_name: str = "Unspecified Goal"
    goal_skill_progress: float = Field(ge=0.0, le=1.0, default=0.0)
    path_progress: PathProgressResponse | None = None
    nodes_progress: list[NodeProgressItem] = Field(default_factory=list)
    skills_progress: list[SkillProgressItem] = Field(default_factory=list)
    recent_changes: list[RecentChangeItem] = Field(default_factory=list)
    timeline_progress: TimelineProgressResponse
    primary_bottleneck: dict[str, Any] | None = None

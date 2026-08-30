from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReplanTriggerType(str, Enum):
    BOTTLENECK_RESOLVED = "BOTTLENECK_RESOLVED"
    BOTTLENECK_SHIFTED = "BOTTLENECK_SHIFTED"
    SKILL_GAP_CHANGED = "SKILL_GAP_CHANGED"
    PREREQUISITE_STATE_CHANGED = "PREREQUISITE_STATE_CHANGED"
    PATH_NODE_OBSOLETE = "PATH_NODE_OBSOLETE"
    NEW_INTERVENTION_REQUIRED = "NEW_INTERVENTION_REQUIRED"
    MANUAL_REPLAN = "MANUAL_REPLAN"


class NodeDeltaAction(str, Enum):
    KEEP = "KEEP"
    REMOVE = "REMOVE"
    INSERT = "INSERT"
    REORDER = "REORDER"
    COMPLETE = "COMPLETE"
    SKIP = "SKIP"


class NodeDeltaItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action: NodeDeltaAction
    resource_id: UUID | None = None
    resource_title: str
    skill_id: UUID | None = None
    skill_name: str
    old_sequence: int | None = None
    new_sequence: int | None = None
    reason: str


class PathDeltaSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    added_nodes: list[NodeDeltaItem] = Field(default_factory=list)
    removed_nodes: list[NodeDeltaItem] = Field(default_factory=list)
    kept_nodes: list[NodeDeltaItem] = Field(default_factory=list)
    reordered_nodes: list[NodeDeltaItem] = Field(default_factory=list)
    skipped_nodes: list[NodeDeltaItem] = Field(default_factory=list)
    summary_text: str


class ReplanDecision(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    should_replan: bool
    staleness_score: float = Field(ge=0.0, le=1.0)
    trigger_type: ReplanTriggerType | None = None
    trigger_skill_id: UUID | None = None
    trigger_skill_name: str | None = None
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    current_path_version: int
    draft_path_id: UUID | None = None
    path_delta: PathDeltaSummary | None = None


class ReplanStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    learner_id: UUID
    goal_id: UUID
    current_path_id: UUID
    current_path_version: int
    should_replan: bool
    staleness_score: float
    trigger_type: ReplanTriggerType | None = None
    primary_bottleneck_skill_name: str | None = None
    summary: str
    decision: ReplanDecision


class PathVersionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    path_id: UUID
    version: int
    parent_path_id: UUID | None = None
    status: str
    generation_reason: str | None = None
    created_at: datetime
    nodes_count: int
    estimated_minutes: int | None = None


class PathDiffResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_path_id: UUID
    from_version: int
    to_path_id: UUID
    to_version: int
    delta: PathDeltaSummary

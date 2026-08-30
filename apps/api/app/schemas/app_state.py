from uuid import UUID

from pydantic import BaseModel


class LearnerAppStateResponse(BaseModel):
    learner_id: UUID
    stage: str
    next_action_label: str
    next_action_route: str
    goal_id: UUID | None = None
    target_role: str | None = None
    active_path_id: UUID | None = None
    primary_bottleneck_skill: str | None = None
    progress_pct: float = 0.0
    state_confidence: str = "LOW"
    diagnostic_session_id: UUID | None = None

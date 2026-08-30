from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from app.core.constants import DIFFICULTY_MAX, DIFFICULTY_MIN
from pydantic import BaseModel, Field, field_validator


class DiagnosticState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    EVALUATING = "EVALUATING"
    NEXT_QUESTION = "NEXT_QUESTION"
    COMPLETE = "COMPLETE"


class StartDiagnosticRequest(BaseModel):
    """Payload to start a diagnostic assessment session."""

    goal_id: UUID
    max_questions: int = Field(default=10, ge=1, le=50)
    force_new: bool = False


class SelfAssessmentRequest(BaseModel):
    """Payload for pre-diagnostic self-assessment ratings."""

    ratings: dict[str, str] = Field(
        ..., description="Map of skill_id or skill_name to rating ('New to it', 'Familiar', 'Comfortable', 'Advanced')"
    )


class DiagnosticSessionResponse(BaseModel):
    """Response containing diagnostic session state."""

    session_id: UUID
    learner_id: UUID
    goal_id: UUID
    status: str
    question_count: int
    max_questions: int
    started_at: datetime
    completed_at: datetime | None = None
    session_metadata: dict[str, Any] | None = None


class DiagnosticQuestionResponse(BaseModel):
    """Question presentation structure for the learner."""

    session_id: UUID
    question_id: UUID
    skill_id: UUID
    skill_name: str
    question_type: str
    difficulty: float
    prompt: str
    options: list[str] | None = None
    question_number: int
    total_questions: int

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty_range(cls, v: float) -> float:
        if v < DIFFICULTY_MIN or v > DIFFICULTY_MAX:
            raise ValueError(f"difficulty must be between {DIFFICULTY_MIN} and {DIFFICULTY_MAX}")
        return v


class SubmitResponseRequest(BaseModel):
    """Payload when submitting an answer for a diagnostic question."""

    idempotency_key: str = Field(..., min_length=5, max_length=100)
    question_id: UUID
    learner_answer: str = Field(..., min_length=1)


class AnswerEvaluation(BaseModel):
    """Structured evaluation output returned by AnswerEvaluator implementations."""

    is_correct: bool
    score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    rubric_coverage: float = Field(default=1.0, ge=0.0, le=1.0)
    misconception_code: str | None = None
    feedback: str = Field(default="Response evaluated.")


class SubmitResponseResult(BaseModel):
    """Result returned after evaluating and persisting a question response."""

    session_id: UUID
    question_id: UUID
    is_correct: bool
    score: float
    evaluation_summary: str
    is_session_completed: bool
    termination_reason: str | None = None
    mastery_updates: list[dict[str, Any]] = Field(default_factory=list)


class LearnerSkillStateItem(BaseModel):
    """Mastery and confidence representation for a single role-relevant skill."""

    skill_id: UUID
    skill_name: str
    required_level: float
    role_importance: float
    mastery_score: float
    confidence: float
    evidence_count: int
    last_assessed_at: datetime | None = None


class LearnerSkillStateResponse(BaseModel):
    """Complete Learning Twin skill state for a learner and target role goal."""

    learner_id: UUID
    goal_id: UUID
    target_role: str
    skills: list[LearnerSkillStateItem]


class DiagnosticHistoryItem(BaseModel):
    """Historical diagnostic session summary."""

    session_id: UUID
    started_at: datetime
    completed_at: datetime | None = None
    status: str
    question_count: int
    skills_count: int
    termination_reason: str | None = None


class DiagnosticHistoryResponse(BaseModel):
    """List of historical diagnostic sessions for a learner."""

    learner_id: UUID
    goal_id: UUID
    history: list[DiagnosticHistoryItem]

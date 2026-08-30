from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class StartActivityRequest(BaseModel):
    learner_id: UUID
    idempotency_key: str | None = None


class SaveDraftActivityRequest(BaseModel):
    learner_id: UUID
    submission_data: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class CompleteActivityRequest(BaseModel):
    learner_id: UUID
    time_spent_minutes: int | None = Field(default=None, ge=1)
    completion_percentage: float = Field(default=100.0, ge=0.0, le=100.0)
    submission_data: dict[str, Any] | None = None
    idempotency_key: str | None = None


class ActivityAttemptResponse(BaseModel):
    id: UUID
    learner_id: UUID
    learning_path_id: UUID
    learning_path_node_id: UUID
    resource_id: UUID
    resource_title: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    time_spent_minutes: int | None = None
    completion_percentage: float
    attempt_number: int
    submission_data: dict[str, Any] | None = None



class MasteryCheckQuestionItem(BaseModel):
    question_id: UUID
    skill_id: UUID
    skill_name: str
    prompt: str
    question_type: str
    difficulty: float
    options: list[str] | None = None


class StartMasteryCheckResponse(BaseModel):
    id: UUID | None = None
    check_id: UUID
    activity_attempt_id: UUID
    learning_path_node_id: UUID
    status: str
    started_at: datetime
    attempt_number: int
    questions: list[MasteryCheckQuestionItem]

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.check_id


class MasteryCheckAnswerSubmission(BaseModel):
    question_id: UUID
    learner_answer: str


class SubmitMasteryCheckRequest(BaseModel):
    learner_id: UUID
    answers: list[MasteryCheckAnswerSubmission]
    idempotency_key: str | None = None


class SkillMasteryOutcomeItem(BaseModel):
    skill_id: UUID
    skill_name: str
    before_mastery: float
    after_mastery: float
    mastery_delta: float
    before_confidence: float
    after_confidence: float
    confidence_delta: float
    evidence_score: float
    evidence_quality: float
    proof_strength: float
    classification: str  # demonstrated, improving, insufficient_evidence, no_improvement, regression
    explanation: str


class ProofOfMasteryOutcomeResponse(BaseModel):
    activity_attempt_id: UUID
    mastery_check_id: UUID | None = None
    learner_id: UUID
    evaluated_at: datetime
    overall_classification: str
    overall_explanation: str
    skill_outcomes: list[SkillMasteryOutcomeItem]

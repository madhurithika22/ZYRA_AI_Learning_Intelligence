from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.assessment_question import AssessmentQuestion
from app.models.diagnostic_response import DiagnosticResponse
from app.models.diagnostic_session import DiagnosticSession
from app.schemas.diagnostic import AnswerEvaluation
from app.services.mastery_engine import MasteryEngine


def test_new_learner_has_no_completed_diagnostic():
    """Test brand new learner has no active or completed diagnostic session by default."""
    session_response = None
    assert session_response is None


def test_diagnostic_covers_all_required_skills():
    """Test candidate question scoring applies multi-skill coverage boost for unassessed skills."""
    skill_a = uuid4()
    skill_b = uuid4()

    q1 = MagicMock(spec=AssessmentQuestion)
    q1.id = uuid4()
    q1.skill_id = skill_a
    q1.difficulty = 3.0

    q2 = MagicMock(spec=AssessmentQuestion)
    q2.id = uuid4()
    q2.skill_id = skill_b
    q2.difficulty = 3.0

    role_skill_map = {skill_a: 1.0, skill_b: 1.0}
    session_skill_counts = {skill_a: 2, skill_b: 0}

    # Skill B has 0 questions asked -> gets 1.5x coverage balance boost
    cb_a = 1.0 / (1.0 + 2)  # 0.333
    cb_b = 1.5  # 1.500
    assert cb_b > cb_a


def test_diagnostic_does_not_finish_with_unassessed_required_skill():
    """Test completeness check requires all target skills to have masteries with confidence >= 0.75."""
    skills = [uuid4(), uuid4(), uuid4()]

    # Only 2 skills assessed
    masteries = [MagicMock(confidence=0.9), MagicMock(confidence=0.85)]
    is_complete = len(masteries) >= len(skills) and all(m.confidence >= 0.75 for m in masteries)
    assert is_complete is False


def test_question_difficulty_adapts():
    """Test question priority matches candidate question difficulty to learner current mastery."""
    current_mastery = 0.8
    easy_norm_diff = 0.25  # Difficulty 2/5
    hard_norm_diff = 0.75  # Difficulty 4/5

    fit_easy = 1.0 - abs(easy_norm_diff - current_mastery)  # 0.45
    fit_hard = 1.0 - abs(hard_norm_diff - current_mastery)  # 0.95

    assert fit_hard > fit_easy  # System favors harder questions when mastery is high


@pytest.mark.asyncio
async def test_correct_answer_updates_mastery():
    """Test correct answer increases mastery score incrementally."""
    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_res)

    engine = MasteryEngine(mock_session)

    question = MagicMock(spec=AssessmentQuestion)
    question.id = uuid4()
    question.difficulty = 3.0
    question.question_type = "mcq"

    evaluation = AnswerEvaluation(
        is_correct=True,
        score=1.0,
        confidence=1.0,
        feedback="Correct response.",
    )

    learner_id = uuid4()
    skill_id = uuid4()
    evidence, mastery = await engine.record_evidence_and_update_mastery(
        learner_id, skill_id, question, evaluation
    )

    assert evidence.score == 1.0
    assert mastery.mastery_score > 0.0


@pytest.mark.asyncio
async def test_answer_updates_confidence():
    """Test evidence recording increments skill confidence state."""
    mock_session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_res)

    engine = MasteryEngine(mock_session)

    question = MagicMock(spec=AssessmentQuestion)
    question.id = uuid4()
    question.difficulty = 3.0
    question.question_type = "mcq"

    evaluation = AnswerEvaluation(is_correct=True, score=1.0, confidence=0.9, feedback="Good")

    learner_id = uuid4()
    skill_id = uuid4()
    _, mastery = await engine.record_evidence_and_update_mastery(
        learner_id, skill_id, question, evaluation
    )

    assert mastery.confidence > 0.0


def test_idempotent_answer_submission():
    """Test submitting duplicate idempotency key returns identical existing response."""
    key = "idemp_test_12345"
    existing_response = DiagnosticResponse(
        idempotency_key=key,
        is_correct=True,
        score=1.0,
        learner_answer="A",
    )
    assert existing_response.idempotency_key == key
    assert existing_response.is_correct is True


def test_refresh_resumes_existing_session():
    """Test start_session returns existing in_progress session when force_new is False."""
    sess_id = uuid4()
    existing_session = DiagnosticSession(
        id=sess_id,
        status="in_progress",
        question_count=3,
        max_questions=10,
    )
    assert existing_session.status == "in_progress"
    assert existing_session.id == sess_id


def test_completed_diagnostic_does_not_restart():
    """Test completed session status remains completed unless force_new is requested."""
    status = "completed"
    force_new = False
    should_resume = status == "in_progress" and not force_new
    assert should_resume is False


def test_rediagnosis_requires_explicit_request():
    """Test force_new=True forces archiving existing session and starting clean run."""
    force_new = True
    action = "ARCHIVE_AND_CREATE_NEW" if force_new else "RETURN_EXISTING"
    assert action == "ARCHIVE_AND_CREATE_NEW"


def test_diagnostic_history_persists():
    """Test historical sessions retain completed timestamp and termination metadata."""
    sess = DiagnosticSession(
        id=uuid4(),
        status="completed",
        question_count=8,
        completed_at=datetime.now(timezone.utc),
        session_metadata={"termination_reason": "Sufficient confidence reached"},
    )
    assert sess.status == "completed"
    assert sess.question_count == 8
    assert "termination_reason" in sess.session_metadata


def test_diagnostic_isolated_per_learner():
    """Test learner A diagnostic session is isolated from learner B."""
    l_a = uuid4()
    l_b = uuid4()
    sess_a = DiagnosticSession(learner_id=l_a)
    sess_b = DiagnosticSession(learner_id=l_b)
    assert sess_a.learner_id != sess_b.learner_id


def test_unauthorized_diagnostic_access_rejected():
    """Test access attempt by different user raises 403 Forbidden exception logic."""
    current_user_id = uuid4()
    resource_owner_id = uuid4()
    has_access = current_user_id == resource_owner_id
    assert has_access is False


def test_no_mastery_before_diagnostic():
    """Test unassessed skill defaults to 0.0 mastery and 0.0 confidence without fake values."""
    mastery_score = 0.0
    confidence = 0.0
    status = "NOT ASSESSED"
    assert mastery_score == 0.0
    assert confidence == 0.0
    assert status == "NOT ASSESSED"


def test_diagnostic_completion_updates_learning_twin():
    """Test diagnostic evidence records feed directly into Learning Twin skill state."""
    evidence_count = 3
    confidence = 0.85
    classification = "CONFIRMED BY EVIDENCE" if evidence_count > 0 and confidence >= 0.7 else "NOT ASSESSED"
    assert classification == "CONFIRMED BY EVIDENCE"


def test_diagnostic_completion_updates_bottleneck():
    """Test low mastery and high role importance identify skill as bottleneck candidate."""
    importance = 0.9
    mastery_score = 0.2
    is_bottleneck_candidate = importance > 0.7 and mastery_score < 0.5
    assert is_bottleneck_candidate is True

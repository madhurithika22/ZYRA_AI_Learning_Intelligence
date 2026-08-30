import abc
from typing import Any

from app.models.assessment_question import AssessmentQuestion
from app.providers.llm.base import LLMProvider
from app.providers.llm.factory import get_llm_provider
from app.schemas.diagnostic import AnswerEvaluation


class BaseAnswerEvaluator(abc.ABC):
    """Abstract interface for question answer evaluation."""

    @abc.abstractmethod
    async def evaluate_answer(
        self,
        question: AssessmentQuestion,
        learner_answer: str,
    ) -> AnswerEvaluation:
        """Evaluate learner answer and return structured evaluation result."""
        pass


class DeterministicEvaluator(BaseAnswerEvaluator):
    """Deterministic answer evaluator for multiple choice and simple text matching."""

    async def evaluate_answer(
        self,
        question: AssessmentQuestion,
        learner_answer: str,
    ) -> AnswerEvaluation:
        cleaned_answer = learner_answer.strip().lower()
        expected_meta: dict[str, Any] = question.expected_answer or {}

        # 1. Multiple choice evaluation
        if question.question_type == "multiple_choice":
            correct_option = (
                str(
                    expected_meta.get("correct_option") or expected_meta.get("correct_answer") or ""
                )
                .strip()
                .lower()
            )

            is_correct = cleaned_answer == correct_option
            score = 1.0 if is_correct else 0.0
            return AnswerEvaluation(
                is_correct=is_correct,
                score=score,
                confidence=1.0,
                rubric_coverage=1.0,
                feedback="Correct answer selected." if is_correct else "Incorrect answer selected.",
            )

        # 2. Keyphrase / regex matching fallback for text/coding
        keywords: list[str] = expected_meta.get("required_keywords", [])
        if keywords:
            matched_count = sum(1 for kw in keywords if kw.lower() in cleaned_answer)
            coverage = matched_count / len(keywords)
            is_correct = coverage >= 0.5
            return AnswerEvaluation(
                is_correct=is_correct,
                score=round(coverage, 2),
                confidence=0.8,
                rubric_coverage=round(coverage, 2),
                feedback=f"Matched {matched_count}/{len(keywords)} required concepts.",
            )

        # 3. Simple text equality
        expected_text = str(expected_meta.get("correct_answer", "")).strip().lower()
        is_correct = cleaned_answer == expected_text if expected_text else True
        score = 1.0 if is_correct else 0.0
        return AnswerEvaluation(
            is_correct=is_correct,
            score=score,
            confidence=0.9,
            rubric_coverage=1.0,
            feedback="Exact answer match." if is_correct else "Answer did not match target rubric.",
        )


class LLMEvaluator(BaseAnswerEvaluator):
    """LLM-assisted evaluator for complex short-answer, coding, or scenario responses."""

    def __init__(self, llm_provider: LLMProvider | None = None) -> None:
        self.llm_provider = llm_provider or get_llm_provider()
        self.fallback_evaluator = DeterministicEvaluator()

    async def evaluate_answer(
        self,
        question: AssessmentQuestion,
        learner_answer: str,
    ) -> AnswerEvaluation:
        # If multiple choice, use deterministic evaluator directly
        if question.question_type == "multiple_choice":
            return await self.fallback_evaluator.evaluate_answer(question, learner_answer)

        prompt = (
            f"Question Prompt: {question.prompt}\n"
            f"Question Type: {question.question_type}\n"
            f"Expected Rubric: {question.expected_answer}\n"
            f"Learner Answer: {learner_answer}\n\n"
            "Evaluate the learner's answer against the rubric. Provide structured assessment."
        )

        try:
            evaluation = await self.llm_provider.generate_structured(
                prompt=prompt,
                response_model=AnswerEvaluation,
            )
            return evaluation
        except Exception:
            # Fall back gracefully to deterministic evaluator on any LLM provider error
            return await self.fallback_evaluator.evaluate_answer(question, learner_answer)

import re
from typing import Any, TypeVar

from app.providers.llm.base import LLMProvider
from app.schemas.conversation import (
    ClaimItem,
    ConversationIntent,
    GroundedAnswer,
    SourceReference,
    SourceType,
)
from app.schemas.goal_intelligence import GoalInterpretation
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Deterministic mock provider for offline development and testing."""

    def __init__(self, override_response: Any | None = None) -> None:
        self.override_response = override_response

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
    ) -> T:
        if self.override_response is not None:
            if isinstance(self.override_response, Exception):
                raise self.override_response
            if isinstance(self.override_response, response_model):
                return self.override_response
            if isinstance(self.override_response, dict):
                return response_model.model_validate(self.override_response)

        if response_model is GoalInterpretation:
            interpretation = self._parse_mock_goal(prompt)
            return interpretation  # type: ignore[return-value]

        if response_model is GroundedAnswer:
            answer = self._parse_mock_grounded_answer(prompt)
            return answer  # type: ignore[return-value]

        raise NotImplementedError(f"MockLLMProvider has no default generator for {response_model}")

    def _parse_mock_goal(self, prompt: str) -> GoalInterpretation:
        prompt_lower = prompt.lower()

        if "trigger_invalid_timeline" in prompt_lower:
            return GoalInterpretation(
                target_role="ML Engineer",
                objective="Invalid timeline test",
                timeline_weeks=-5,
                daily_minutes=60,
                confidence=1.0,
            )

        if "trigger_invalid_minutes" in prompt_lower:
            return GoalInterpretation(
                target_role="ML Engineer",
                objective="Invalid minutes test",
                timeline_weeks=12,
                daily_minutes=-10,
                confidence=1.0,
            )

        target_role = "ML Engineer"
        if "data scientist" in prompt_lower:
            target_role = "Data Scientist"
        elif "ai engineer" in prompt_lower:
            target_role = "AI Engineer"
        elif "ml engineer" in prompt_lower or "machine learning engineer" in prompt_lower:
            target_role = "ML Engineer"

        timeline_weeks = 24
        if "6 months" in prompt_lower or "six months" in prompt_lower:
            timeline_weeks = 24
        elif "3 months" in prompt_lower or "three months" in prompt_lower:
            timeline_weeks = 12
        elif "1 year" in prompt_lower or "12 months" in prompt_lower:
            timeline_weeks = 52

        daily_minutes = 90
        minute_match = re.search(r"(\d+)\s*(?:minutes|mins|min)", prompt_lower)
        if minute_match:
            daily_minutes = int(minute_match.group(1))

        stated_skills: list[str] = []
        if "python" in prompt_lower:
            stated_skills.append("Python")
        if (
            "machine learning" in prompt_lower
            or "basic ml" in prompt_lower
            or "ml knowledge" in prompt_lower
        ):
            stated_skills.append("Machine Learning")
        if "statistics" in prompt_lower:
            stated_skills.append("Statistics")
        if "docker" in prompt_lower:
            stated_skills.append("Docker")

        ambiguities: list[str] = []
        constraints: list[str] = []
        if daily_minutes > 0:
            constraints.append(f"Daily study availability: {daily_minutes} minutes")
        if timeline_weeks > 0:
            constraints.append(f"Timeline constraint: {timeline_weeks} weeks")

        confidence = 0.95
        if "maybe" in prompt_lower or "unclear" in prompt_lower or "unknown role" in prompt_lower:
            confidence = 0.50
            ambiguities.append("Target role or objective scope is somewhat vague.")

        if "unknown role" in prompt_lower:
            target_role = "Quantum Cybernetic Specialist"

        return GoalInterpretation(
            target_role=target_role,
            objective=f"Become job-ready for {target_role}",
            timeline_weeks=timeline_weeks,
            daily_minutes=daily_minutes,
            desired_outcome="job_readiness",
            constraints=constraints,
            stated_existing_skills=stated_skills,
            ambiguities=ambiguities,
            confidence=confidence,
        )

    def _parse_mock_grounded_answer(self, prompt: str) -> GroundedAnswer:
        user_q = prompt.split("[USER QUESTION]")[-1].lower() if "[USER QUESTION]" in prompt else prompt.lower()

        if "python" in user_q:
            mastery_match = re.search(r'"python".*?"mastery":\s*"(\d+%)"', prompt.lower())
            mastery_str = mastery_match.group(1) if mastery_match else "99%"
            return GroundedAnswer(
                intent=ConversationIntent.SKILL_STATUS,
                response_type="LEARNER_GROUNDED_RESPONSE",
                answer=f"Based on your current learner state, your Python mastery is currently {mastery_str}.",
                confidence=0.95,
                claims=[ClaimItem(claim=f"Python mastery is {mastery_str}.", source_ids=["skill-python"])],
                sources=[SourceReference(source_type=SourceType.SKILL_MASTERY, source_id="skill-python", label="Skill Mastery: Python")],
                limitations=[],
                suggested_followups=["Why is Python my bottleneck?"],
            )

        if "quantum" in user_q:
            return GroundedAnswer(
                intent=ConversationIntent.SKILL_STATUS,
                response_type="LEARNER_GROUNDED_RESPONSE",
                answer="I don't have enough evidence to answer that from your current learner state. Quantum Computing is not in your target role skills.",
                confidence=0.50,
                claims=[],
                sources=[],
                limitations=["Skill not present in target role."],
                suggested_followups=["What are my target role skills?"],
            )

        if "evidence" in user_q or "proof" in user_q:
            return GroundedAnswer(
                intent=ConversationIntent.EVIDENCE_QUERY,
                response_type="LEARNER_GROUNDED_RESPONSE",
                answer="Based on your current learner evidence records, you have demonstrated mastery across 1 key skill with 34 total evidence events.",
                confidence=0.95,
                claims=[ClaimItem(claim="34 total evidence records analyzed.", source_ids=["evidence-summary"])],
                sources=[SourceReference(source_type=SourceType.SKILL_EVIDENCE, source_id="evidence-summary", label="Evidence & Mastery Summary")],
                limitations=[],
                suggested_followups=["What evidence says I am weak in MLOps?"],
            )

        if "gradient descent" in user_q:
            return GroundedAnswer(
                intent=ConversationIntent.GENERAL_LEARNING_QUERY,
                response_type="GENERAL_LEARNING_RESPONSE",
                answer="Gradient descent is an optimization algorithm used to minimize a loss function by iteratively moving in the direction of steepest descent.",
                confidence=1.0,
                claims=[ClaimItem(claim="Gradient descent minimizes loss functions using gradients.", source_ids=[])],
                sources=[],
                limitations=[],
                suggested_followups=["How does gradient descent relate to my Machine Learning progress?"],
            )

        if "invalid_source_test" in user_q:
            return GroundedAnswer(
                intent=ConversationIntent.BOTTLENECK_EXPLANATION,
                response_type="LEARNER_GROUNDED_RESPONSE",
                answer="Test response with unsupported source ID.",
                confidence=0.9,
                claims=[ClaimItem(claim="Fake claim", source_ids=["INVALID_SOURCE_XYZ"])],
                sources=[SourceReference(source_type=SourceType.BOTTLENECK_ANALYSIS, source_id="INVALID_SOURCE_XYZ", label="Invalid Source")],
                limitations=[],
                suggested_followups=[],
            )

        return GroundedAnswer(
            intent=ConversationIntent.BOTTLENECK_EXPLANATION,
            response_type="LEARNER_GROUNDED_RESPONSE",
            answer="Based on your current learner state, your primary structural bottleneck is Model Deployment due to high role dependency impact.",
            confidence=0.95,
            claims=[ClaimItem(claim="Model Deployment is your primary bottleneck.", source_ids=["bottleneck-analysis"])],
            sources=[SourceReference(source_type=SourceType.BOTTLENECK_ANALYSIS, source_id="bottleneck-analysis", label="Bottleneck Analysis")],
            limitations=[],
            suggested_followups=["Why is Model Deployment my bottleneck?", "Why should I do this project?"],
        )

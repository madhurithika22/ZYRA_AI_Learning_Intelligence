import re
from typing import Any

from app.schemas.conversation import ConversationIntent


class IntentClassifier:
    """Classifies user queries into structured conversation intent categories and identifies target entities."""

    def classify_intent(self, message: str) -> tuple[ConversationIntent, dict[str, Any]]:
        """Classify message intent and return identified entities (e.g., skill_name, topic)."""
        msg_lower = message.lower().strip()
        entities: dict[str, Any] = {}

        # 1. Prompt Injection / Out-of-Scope Checks
        if any(kw in msg_lower for kw in ["weather", "movie", "recipe", "ignore your system", "reveal api key", "tell me a joke"]):
            if "ignore your system" in msg_lower or "reveal api key" in msg_lower:
                entities["injection_attempt"] = True
            return ConversationIntent.UNSUPPORTED, entities

        # 2. General Educational / Learning Concept Questions
        if re.search(r"\b(what is|explain|define|how does|what are)\b", msg_lower) and not any(
            kw in msg_lower for kw in ["my ", "mine", "i ", "me ", "path", "bottleneck", "next action", "progress", "evidence"]
        ):
            entities["concept_topic"] = message
            return ConversationIntent.GENERAL_LEARNING_QUERY, entities

        # 3. Goal & Role Questions
        if any(kw in msg_lower for kw in ["trying to become", "my goal", "target role", "my objective"]):
            return ConversationIntent.GOAL_STATUS, entities

        # 4. Bottleneck & Blocked Questions
        if any(kw in msg_lower for kw in ["bottleneck", "blocking me", "blocked by", "why is", "why am i stuck"]):
            if "bottleneck" in msg_lower or "blocking" in msg_lower or "stuck" in msg_lower:
                return ConversationIntent.BOTTLENECK_EXPLANATION, entities

        # 5. Next Best Action Questions
        if any(kw in msg_lower for kw in ["this project", "this action", "next action", "asking me to do", "why should i do"]):
            return ConversationIntent.NEXT_ACTION_EXPLANATION, entities

        # 6. Path & Replanning Questions
        if any(kw in msg_lower for kw in ["path change", "path changed", "why path", "path update"]):
            return ConversationIntent.PATH_EXPLANATION, entities

        # 7. Evidence & Assessment Questions
        if any(kw in msg_lower for kw in ["evidence", "proof", "what shows", "assessment history"]):
            return ConversationIntent.EVIDENCE_QUERY, entities

        # 8. Uncertainty & Confidence Questions
        if any(kw in msg_lower for kw in ["least certain", "uncertain", "how sure", "confidence"]):
            return ConversationIntent.UNCERTAINTY_QUERY, entities

        # 9. Overall Progress Questions
        if any(kw in msg_lower for kw in ["how much have i improved", "progress", "improvement", "mastered so far"]):
            return ConversationIntent.PROGRESS_SUMMARY, entities

        # 10. Skill History Questions
        if any(kw in msg_lower for kw in ["skill history", "mastery history", "history of"]):
            return ConversationIntent.SKILL_HISTORY, entities

        # 11. Comparison Questions
        if any(kw in msg_lower for kw in ["why this and not", "compare", "instead of"]):
            return ConversationIntent.COMPARISON, entities

        # 12. Skill Status Query (default for skill-specific queries)
        if any(kw in msg_lower for kw in ["mastery", "strong", "weak", "level in", "know about"]):
            return ConversationIntent.SKILL_STATUS, entities

        # Fallback for general questions vs skill status
        if not any(kw in msg_lower for kw in ["my", "mine", "i", "me"]):
            return ConversationIntent.GENERAL_LEARNING_QUERY, entities

        return ConversationIntent.SKILL_STATUS, entities

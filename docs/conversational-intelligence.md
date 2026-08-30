# Phase 12 — Grounded Conversational Learning Intelligence Documentation

> **DISCLAIMER**:
> "PostgreSQL + deterministic services = SOURCE OF TRUTH. LLM = LANGUAGE / REASONING INTERFACE."
> The LLM is strictly prohibited from inferring missing facts, inventing mastery percentages, or mutating database state.

---

## 1. Architectural Overview
The **Grounded Conversational Learning Intelligence Assistant** enables learners to interact naturally with their goal status, skill masteries, primary bottlenecks, recommended next-best actions, path changes, dynamic replanning history, and proof-of-mastery evidence.

```
[User Question] ──► [IntentClassifier] ──► [Intent & Entities]
                          │
                          ▼
                  [ContextBuilder] ◄── [LearningTwinService / Domain Services]
                          │
                          ▼
            [Minimal Grounded Context + Valid Source Map]
                          │
                          ▼
                 [OpenAIProvider / LLM] ◄── [System Prompt: Injection Defense & Grounding Rules]
                          │
                          ▼
               [GroundedAnswer Validation & Source Filtering]
                          │
                          ▼
            [ConversationSession & Message DB Persistence] ──► [Typed API Response]
```

---

## 2. Intent Categorization & Entity Resolution
The `IntentClassifier` maps queries to structured intent categories:
- `GOAL_STATUS`: Goal objective and target role inquiry.
- `SKILL_STATUS`: Specific skill mastery, confidence, and gap inquiry.
- `BOTTLENECK_EXPLANATION`: Structural bottleneck reasoning (Phase 5).
- `NEXT_ACTION_EXPLANATION`: Recommendation rationale (Phase 9).
- `PATH_EXPLANATION` / `REPLAN_EXPLANATION`: Learning path versioning and diffs (Phase 10).
- `PROGRESS_SUMMARY`: Overall progress metrics (Phase 8/7).
- `EVIDENCE_QUERY`: Proof-of-mastery evidence and outcomes (Phase 7).
- `UNCERTAINTY_QUERY`: Low-confidence skills and completeness metrics.
- `GENERAL_LEARNING_QUERY`: Educational concepts (e.g., "What is gradient descent?").
- `UNSUPPORTED`: Out-of-scope queries (e.g., weather, prompt injection).

---

## 3. Minimal Grounded Context & Source Validation
- **Targeted Retrieval**: The `ContextBuilder` fetches ONLY context relevant to the classified query intent.
- **Source Map**: Every claim in the LLM output is mapped to an authoritative `source_id` (e.g., `skill-c0f2d863...`, `bottleneck-analysis`, `next-action`).
- **Backend Source Validation**: The `ConversationalService` verifies that any `source_id` returned in the LLM response actually exists in the provided context. Unsupported or hallucinated source IDs are filtered out automatically.

---

## 4. Security, Prompt Injection & Cost Control
- **Prompt Injection Defense**: Learner input is treated as untrusted data. System prompts explicitly instruct the model that system instructions and grounded state override user prompts. Secrets (e.g., `OPENAI_API_KEY`) are never exposed in model context.
- **Learner Data Isolation**: Ownership checks enforce that Learner A cannot create, view, or message Learner B's conversation session (HTTP 403/404).
- **Cost Control**: Purely deterministic queries and out-of-scope questions are formatted directly by backend services with `used_llm = False`.

---

## 5. API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/learners/{learner_id}/conversation/sessions` | `POST` | Create a new conversation session |
| `/api/v1/conversation/sessions/{session_id}/messages` | `POST` | Send user message and get grounded assistant answer |
| `/api/v1/conversation/sessions/{session_id}` | `GET` | Retrieve session details and message history |
| `/api/v1/conversation/sessions/{session_id}/messages` | `GET` | Retrieve message history list |

# Adaptive Diagnostic Engine Specification

The Adaptive Diagnostic Engine determines a learner's baseline skill competency for a target career outcome goal through information-gain driven question selection.

## 1. Question Selection Algorithm

For candidate questions targeting the goal's required skills, selection priority is computed deterministically:

$$\text{question\_priority} = \text{uncertainty} \times \text{skill\_importance} \times \text{difficulty\_fit} \times \text{novelty}$$

### Components

1. **Uncertainty**: $\text{uncertainty} = \max(0.05, 1.0 - \text{confidence}_{\text{current}})$. Prioritizes skills where the system lacks evidence.
2. **Skill Importance**: $\text{skill\_importance} = \text{RoleSkill.importance} \in [0.0, 1.0]$. Prioritizes core required skills for the target role.
3. **Difficulty Fit**: $\text{difficulty\_fit} = 1.0 - |\text{normalized\_difficulty} - \text{mastery}_{\text{current}}|$. Prefers questions near the learner's estimated mastery boundary.
4. **Novelty**:
   - $0.0$ if answered in current session (avoids duplicate questions).
   - $0.5$ if answered in previous session.
   - $1.0$ if never answered.

---

## 2. Answer Evaluation Architecture

- **Multiple-Choice Questions**: Evaluated deterministically (`DeterministicEvaluator`) by matching option selection.
- **Short-Answer / Coding / Scenario Questions**: Evaluated via structured rubric evaluation abstraction (`LLMEvaluator`), returning structured `AnswerEvaluation` (score, confidence, rubric coverage, feedback).
- **Graceful Fallback**: If LLM provider is unconfigured or fails, evaluation falls back automatically to keyword/regex matching (`DeterministicEvaluator`).

---

## 3. Diagnostic Termination Rules

A session terminates when any of the following conditions are met:
1. `question_count >= max_questions` (default: 10 questions).
2. All target role skills reach high confidence ($\ge 0.75$).
3. No further un-answered questions remain in the item bank.
4. Explicit learner session abandonment.

---

## 4. Transactional Integrity & Idempotency

- **Idempotent Response Submission**: Each response submission requires a unique `idempotency_key`. Repeated requests with the same key return cached results without re-evaluating or updating mastery twice.
- **Atomic Operations**: Evaluation, evidence recording (`SkillEvidence`), mastery update (`SkillMastery`), and session state advancement execute inside a nested database transaction. Any failure triggers a complete rollback.

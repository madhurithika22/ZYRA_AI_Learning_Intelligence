# Phase 7 — Proof-of-Mastery & Evidence Loop Documentation

## 1. Executive Summary & Core Principle
The **Proof-of-Mastery & Evidence Loop** converts learning completions into rigorous, evaluated evidence of skill improvement.

> **CRITICAL PRODUCT RULE**: **Completion Is Not Mastery.**
> Completing a learning activity records attempt progress (`status="completed"`, `completion_percentage=1.0`), but **`SkillMastery` remains strictly unchanged**. `SkillMastery` is updated **ONLY** after evaluated evidence from a post-learning assessment (mastery check) passes to `MasteryEngine`.

---

## 2. System Architecture & Lifecycle

```
[ Learning Activity ]
        │
        ├──> Learner Starts Activity ──> LearningActivityAttempt (status="started")
        │
        ├──> Learner Completes Activity ──> LearningActivityAttempt (status="completed")
        │                                   (SkillMastery UNCHANGED)
        │
        └──> Post-Learning Assessment ──> MasteryCheckAttempt (status="started")
                │
                ├──> Evaluated via LLMEvaluator / DeterministicEvaluator
                │
                ├──> Evidence Quality Computed
                │     ev_quality = score × (0.5 + 0.5 × (difficulty - 1.0)/4.0) × rubric_coverage
                │
                ├──> Evaluated Evidence Recorded in MasteryEngine
                │     MasteryEngine.record_evidence_and_update_mastery(...)
                │
                ├──> Before vs After Mastery/Confidence Deltas & Proof Strength
                │     proof_strength = avg_quality × min(1.0, 0.5 + 0.5 × after_confidence)
                │
                └──> Persisted in DB as MasteryOutcome (Single DB Transaction)
```

---

## 3. Data Models & Database Schema

### `LearningActivityAttempt` (`learning_activity_attempts`)
- `id`: UUID (Primary Key)
- `learner_id`: FK -> `learners.id`
- `learning_path_id`: FK -> `learning_paths.id`
- `learning_path_node_id`: FK -> `learning_path_nodes.id`
- `resource_id`: FK -> `learning_resources.id`
- `status`: String (`started`, `completed`, `abandoned`)
- `started_at`: DateTime (TZ)
- `completed_at`: DateTime (TZ, Nullable)
- `time_spent_minutes`: Integer (Nullable)
- `completion_percentage`: Float (Default: 0.0)
- `attempt_number`: Integer (Default: 1)
- `idempotency_key`: String (Nullable, Indexed)

### `MasteryCheckAttempt` (`mastery_check_attempts`)
- `id`: UUID (Primary Key)
- `learner_id`: FK -> `learners.id`
- `activity_attempt_id`: FK -> `learning_activity_attempts.id`
- `learning_path_node_id`: FK -> `learning_path_nodes.id`
- `status`: String (`started`, `completed`, `failed`)
- `started_at`: DateTime (TZ)
- `completed_at`: DateTime (TZ, Nullable)
- `attempt_number`: Integer (Default: 1)
- `idempotency_key`: String (Nullable, Indexed)

### `MasteryOutcome` (`mastery_outcomes`)
- `id`: UUID (Primary Key)
- `activity_attempt_id`: FK -> `learning_activity_attempts.id`
- `mastery_check_id`: FK -> `mastery_check_attempts.id` (Nullable)
- `learner_id`: FK -> `learners.id`
- `skill_id`: FK -> `skills.id`
- `before_mastery`: Float
- `after_mastery`: Float
- `mastery_delta`: Float
- `before_confidence`: Float
- `after_confidence`: Float
- `confidence_delta`: Float
- `evidence_score`: Float
- `evidence_quality`: Float
- `proof_strength`: Float
- `classification`: String (`demonstrated`, `improving`, `insufficient_evidence`, `no_improvement`, `regression`)
- `explanation`: Text

---

## 4. Evidence Quality & Proof Strength Formulas

### Evidence Quality
$$\text{ev\_quality} = \text{score} \times \left(0.5 + 0.5 \times \frac{\text{difficulty} - 1.0}{4.0}\right) \times \text{rubric\_coverage}$$

### Proof Strength
$$\text{proof\_strength} = \text{avg\_quality} \times \min\left(1.0, 0.5 + 0.5 \times \text{after\_confidence}\right)$$

---

## 5. API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/learning-activities/{path_node_id}/start` | `POST` | Start learning activity attempt |
| `/api/v1/learning-activities/{attempt_id}/complete` | `POST` | Complete activity (SkillMastery UNCHANGED) |
| `/api/v1/learning-activities/{attempt_id}` | `GET` | Fetch activity attempt details |
| `/api/v1/learning-activities/{attempt_id}/outcome` | `GET` | Fetch proof-of-mastery outcome |
| `/api/v1/mastery-checks/{activity_attempt_id}/start` | `POST` | Start post-learning assessment |
| `/api/v1/mastery-checks/{check_id}/submit` | `POST` | Submit answers, record evidence, return outcome |

---

## 6. Verification & Synthetic Audit Matrix

| Case | Scenario | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Case A** | Activity Completed, No Assessment | `Mastery Before == Mastery After` | **PASS** |
| **Case B** | Strong Post-Learning Assessment | `Mastery Delta > 0`, `Classification = improving` | **PASS** |
| **Case C** | Weak Post-Learning Assessment | Low score evaluated, regression or no growth | **PASS** |
| **Case D** | Repeated Consistent Evidence | `Confidence After > Confidence Before` | **PASS** |
| **Case E** | Conflicting Evidence | Moderated confidence growth | **PASS** |
| **Case F** | Idempotency Key Reuse | Same attempt returned, zero duplicate updates | **PASS** |
| **Case G** | Transaction Failure | Atomic rollback of all evidence & outcome records | **PASS** |
| **Case H** | Skill-Specific Differentiation | Unique outcome per target skill | **PASS** |

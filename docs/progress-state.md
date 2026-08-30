# Phase 8 — Learning Progress & Adaptive State Documentation

## 1. Executive Summary & Core Principle
Phase 8 introduces a deterministic, longitudinal **Learning Progress & Adaptive State Layer** to the Adaptive Learning Intelligence Engine.

> **CORE PRINCIPLE**:
> Progress state is a **deterministic aggregation of authoritative database state** (`SkillMastery`, `SkillEvidence`, `MasteryOutcome`, `LearningActivityAttempt`, `LearningPathNode`, `RoleSkill`). Zero LLM calls are used to aggregate, calculate, or summarize learner progress.

---

## 2. Key Formulas & Distinctions

### Goal Skill Progress Proxy
$$\text{Goal Skill Progress} = \frac{\sum \left( \min\left(1.0, \frac{\text{Current Mastery}}{\text{Required Level}}\right) \times \text{Importance} \right)}{\sum \text{Importance}}$$

- `required_level`: Role-specific competency target defined in `RoleSkill.required_level`.
- `importance`: Relative skill weight defined in `RoleSkill.importance`.
- **Distinction**: This metric represents **Goal Skill Progress**, NOT overall "career readiness" or job-matching guarantees.

### Path Progress vs Mastery Proof
| Metric | Basis | Description |
| :--- | :--- | :--- |
| **Path Completion %** | Node Activity Progress | $\frac{\text{Completed Nodes}}{\text{Total Path Nodes}}$ (e.g. 50% completed) |
| **Time Completion %** | Estimated Duration | $\frac{\text{Completed Node Estimated Mins}}{\text{Total Path Estimated Mins}}$ |
| **Proven Proof Status** | Evaluated Evidence | Node proof status is `proven` ONLY after post-learning assessment (`MasteryOutcome`). |

Completing 60% of path activities does **NOT** imply 60% skill mastery. Path completion measures activity progress; skill progress measures demonstrated mastery.

---

## 3. Time & Pace Semantics
- `total_available_minutes = daily_minutes * 7 * timeline_weeks`
- `actual_time_spent_minutes`: Sum of actual recorded activity duration (`LearningActivityAttempt.time_spent_minutes`).
- `path_estimated_remaining_minutes`: Total estimated duration of uncompleted path nodes.
- `descriptive_pace`: Ratio of completed estimated activity minutes to actual elapsed minutes spent (`completed_minutes / max(1, actual_time_spent)`). No predictive completion forecasting is performed.

---

## 4. API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/learners/{learner_id}/progress` | `GET` | Fetch complete longitudinal progress summary for active goal & path |
| `/api/v1/learners/{learner_id}/goals/{goal_id}/progress` | `GET` | Fetch goal skill progress proxy & target skill status breakdown |
| `/api/v1/learning-paths/{path_id}/progress` | `GET` | Fetch node completion and duration metrics for a learning path |
| `/api/v1/learners/{learner_id}/skills/{skill_id}/history` | `GET` | Fetch chronological mastery and evidence event history for a skill |

---

## 5. Synthetic Audit Matrix

| Case | Scenario | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| **Case A** | Activity Completed | Path completion increases, mastery unchanged | **PASS** |
| **Case B** | Mastery Check Succeeds | Mastery & confidence reflected in progress summary | **PASS** |
| **Case C** | Skill Improves | Recent changes updated with evidence-backed language | **PASS** |
| **Case D** | Skill Regresses | Regression classification displayed cleanly | **PASS** |
| **Case E** | No Evidence | Explicit "No demonstrated evidence yet" state | **PASS** |
| **Case F** | Multiple Mastery Outcomes | Chronological skill history preserved | **PASS** |
| **Case G** | Node Completion | Completed nodes tracked independently of estimated time | **PASS** |
| **Case H** | Time vs Estimate | Actual time spent and estimated duration tracked separately | **PASS** |
| **Case I** | Importance Weighting | Goal Skill Progress weighted by `RoleSkill.importance` | **PASS** |
| **Case J** | Query Determinism | Identical state summary across repeated queries | **PASS** |
| **Math Audit** | Weighted Skill Proxy | $\frac{1.0(1.0) + 0.5(0.5) + 0.2(0.5)}{1.0 + 0.5 + 0.2} = \frac{1.35}{1.70} = 79.41\%$ | **PASS** |

# Phase 11 — Learning Twin & Decision Center Documentation

> **DISCLAIMER**:
> "The Learning Twin is a unified deterministic learner-state representation. It does not independently infer mastery, bottlenecks, or recommendations." Zero LLM calls are invoked during state composition, confidence scoring, completeness evaluation, or decision trace generation.

---

## 1. Overview & Architectural Philosophy
The **Learning Twin & Decision Center** provides a single, unified computational representation of the learner's current state. Rather than introducing independent heuristics or duplicate calculations, it orchestrates authoritative domain engines across the platform:

```
[Goal & Profile] (Phase 3) ────────┐
[Skill Mastery & Evidence] (Phase 4) ──┼──► [LearningTwinService] ──► [LearningTwinResponse]
[Bottleneck Analysis] (Phase 5) ────┤                                     ├── Goal Summary
[Path Optimizer] (Phase 6) ─────────┤                                     ├── Bottleneck Card
[Proof of Mastery] (Phase 7) ───────┤                                     ├── Next Best Action
[Progress Service] (Phase 8) ───────┤                                     ├── Skill Matrix
[Next-Best-Action Engine] (Phase 9) ┤                                     ├── Path Health
[Dynamic Replanning Engine] (Phase 10) ┘                                  └── Decision Trace
```

---

## 2. Authoritative Data Source Mapping

| Field / Section | Authoritative Data Source | Engine / Model |
| :--- | :--- | :--- |
| `goal` | Goal, Role, RoleSkill | Phase 3 Domain Models & `ProgressService` |
| `skills` | SkillMastery, SkillEvidence | Phase 4 & Phase 8 `ProgressService` |
| `bottleneck` | BottleneckAnalysisService | Phase 5 Bottleneck Engine |
| `path` | LearningPath, LearningPathNode | Phase 6 Optimizer & Phase 8 `ProgressService` |
| `evidence_summary` | SkillEvidence, MasteryOutcome | Phase 7 Proof-of-Mastery Service |
| `next_action` | NextActionService | Phase 9 Next-Best-Action Engine |
| `replan` | ReplanningService, ChangeDetectionService | Phase 10 Dynamic Replanning Engine |

---

## 3. Multi-Layer Confidence Framework
The Learning Twin maintains three distinct, non-conflated confidence dimensions:

1. **Skill Confidence**: Standard error of mastery estimation for a specific skill ($\text{confidence} \in [0.0, 1.0]$).
2. **Action Confidence**: Expected outcome utility for recommended next action ($\text{action\_confidence} \in [0.0, 1.0]$).
3. **Twin State Confidence**: Evaluates whether the unified learner computational state is sufficiently complete across 7 key dimensions:
   - Goal set
   - Target role assigned
   - Target skills present
   - Mastery evidence records available
   - Active learning path present
   - Primary bottleneck verified
   - Next best action available

$$\text{StateCompleteness} = \frac{\text{Observed Dimensions}}{7.0}$$
- **`HIGH`**: Completeness $\ge 85\%$
- **`MEDIUM`**: Completeness $50\% - 84\%$
- **`LOW`**: Completeness $< 50\%$

---

## 4. State Freshness & Determinism
- **derived Freshness**: Automatically derived from `latest_mastery_update_at` and active path update timestamps.
- **Determinism**: Identical database state yields 100% identical Learning Twin snapshots and decision traces.

---

## 5. API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/learners/{learner_id}/learning-twin` | `GET` | Returns unified Learning Twin snapshot and decision trace |
| `/api/v1/learners/{learner_id}/learning-twin/trace` | `GET` | Returns structured decision execution trace |

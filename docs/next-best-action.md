# Phase 9 — Adaptive Next-Best-Action Engine Documentation

> **DISCLAIMER**:
> This is a deterministic decision heuristic, not a validated behavioral recommendation model. Zero LLM calls are invoked during action scoring, candidate ranking, or explanation generation.

---

## 1. Candidate Action Types
The engine evaluates current learner state and generates candidate actions across seven distinct action types:

| Action Type | Description | Trigger Condition |
| :--- | :--- | :--- |
| `LEARN` | Start a recommended learning resource | Target skill gap > 0 with uncompleted path activity |
| `CONTINUE` | Resume an in-progress activity | Active `LearningActivityAttempt` in `started` state |
| `MASTERY_CHECK` | Complete post-learning assessment check | `LearningActivityAttempt` completed but unproven |
| `REASSESS` | Targeted diagnostic assessment | Skill confidence < 0.50 with significant skill gap |
| `PREREQUISITE_REVIEW` | Learn prerequisite skill | Unmastered prerequisite blocking primary bottleneck |
| `PROJECT` | Hands-on applied project / lab | Practical learning value is high for target skill |
| `SKIP` | Explicitly skip redundant content | Demonstrated mastery >= target requirement & confidence >= 80% |

---

## 2. Action Scoring & Normalization Formula
$$\text{ActionScore} = w_{\text{gap}} \cdot \text{gap\_reduction} + w_{\text{bottleneck}} \cdot \text{bottleneck\_relevance} + w_{\text{uncertainty}} \cdot \text{information\_value} + w_{\text{prerequisite}} \cdot \text{prerequisite\_value} + w_{\text{progress}} \cdot \text{path\_progress\_value} + w_{\text{evidence}} \cdot \text{evidence\_value} + w_{\text{practical}} \cdot \text{practical\_value} - w_{\text{time}} \cdot \text{time\_cost} - w_{\text{redundancy}} \cdot \text{redundancy} - w_{\text{repeat}} \cdot \text{repetition\_penalty}$$

### Configured Scoring Weights
- $w_{\text{gap}} = 0.25$
- $w_{\text{bottleneck}} = 0.25$
- $w_{\text{uncertainty}} = 0.15$
- $w_{\text{prerequisite}} = 0.15$
- $w_{\text{progress}} = 0.10$
- $w_{\text{evidence}} = 0.10$
- $w_{\text{practical}} = 0.05$
- $w_{\text{time}} = 0.10$
- $w_{\text{redundancy}} = 0.15$
- $w_{\text{repeat}} = 0.20$

All metric components are normalized to $[0.0, 1.0]$. The resulting ActionScore is clamped to $\ge 0.0$.

---

## 3. Deterministic Tie-Breakers & Action Stability
When candidate action scores are identical or near-identical, tie-breaking is enforced strictly in order:
1. `score` (descending)
2. `bottleneck_relevance` (descending)
3. `gap_reduction` (descending)
4. `estimated_minutes` (ascending)
5. Action Type Priority: `CONTINUE` > `MASTERY_CHECK` > `SKIP` > `PREREQUISITE_REVIEW` > `LEARN` > `PROJECT` > `REASSESS`
6. Candidate Title (alphabetical ascending)

---

## 4. Action Confidence vs Mastery Confidence
- **Mastery Confidence**: Statistical uncertainty in a learner's mastery estimate for a skill (`SkillMastery.confidence`).
- **Action Confidence**: The engine's system confidence that the selected action is currently optimal ($[0.40, 0.99]$), computed from the score gap to rank #2 alternative:
  $$\text{Action Confidence} = \min\left(0.99, \max\left(0.40, 0.50 + 1.5 \times (\text{Score}_1 - \text{Score}_2)\right)\right)$$
- **Labels**: `HIGH` ($\ge 80\%$), `MEDIUM` ($\ge 60\%$), `LOW` ($< 60\%$).

---

## 5. API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/learners/{learner_id}/next-action` | `GET` | Returns top selected action, action confidence, and top 2 alternatives |
| `/api/v1/learners/{learner_id}/goals/{goal_id}/next-action` | `GET` | Goal-specific Next-Best-Action recommendation |
| `/api/v1/learners/{learner_id}/goals/{goal_id}/next-actions` | `GET` | Full ranked candidate action list for a goal |

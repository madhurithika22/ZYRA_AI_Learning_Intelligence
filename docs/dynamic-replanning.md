# Phase 10 — Dynamic Replanning Engine Documentation

> **DISCLAIMER**:
> This is a deterministic dynamic replanning heuristic, not a formally optimal stochastic planner. Zero LLM calls are invoked during change detection, staleness calculation, path diff generation, or versioning.

---

## 1. Overview & Core Philosophy
The **Dynamic Replanning Engine** evaluates whether an active learning path has become stale because the learner's actual state (mastery, confidence, bottleneck structure, activity completions) has materially changed.

### Core Principle
- **Path Generation**: "What is an optimal path from scratch?"
- **Dynamic Replanning**: "How should the CURRENT active path change because the learner's state changed?"

Replanning preserves path continuity and completed learner effort while applying minimal-change deltas to address structural changes.

---

## 2. Material Change Thresholds & Triggers
A replan is triggered when material state changes cross defined thresholds:

| Trigger Category | Trigger Condition | Material Threshold |
| :--- | :--- | :--- |
| `PATH_NODE_OBSOLETE` | Future node skill already mastered | Mastery $\ge$ Required & Confidence $\ge 0.80$ |
| `BOTTLENECK_RESOLVED` | Primary bottleneck skill reached requirement | Mastery $\ge$ Required level |
| `BOTTLENECK_SHIFTED` | Structural bottleneck shifted to a new skill | Primary bottleneck skill changed |
| `SKILL_GAP_CHANGED` | Major overall mastery progression | $\Delta\text{mastery} \ge 0.40$ across target skills |
| `PREREQUISITE_STATE_CHANGED` | Prerequisite satisfied or newly required | Prerequisite state change |
| `MANUAL_REPLAN` | Learner explicitly requests replan | Explicit user trigger |

Immaterial numerical fluctuations ($\Delta\text{mastery} < 0.10$) do NOT trigger replanning.

---

## 3. Path Staleness Metric
$$\text{StalenessScore} = \min\left(1.0, w_{\text{bottleneck}} + w_{\text{obsolete}} + w_{\text{gap}} + w_{\text{prereq}}\right)$$
- **Threshold**: `STALENESS_REPLAN_THRESHOLD = 0.35`
- Paths with Staleness Score $\ge 35\%$ or explicit trigger conditions recommend a path update.

---

## 4. Path Versioning & Node Lineage
- **Immutability**: Active paths are never overwritten. Re-planning creates a new draft version $V_{k+1}$ pointing to parent $V_k$ via `parent_path_id`.
- **Node Lineage**: Surviving nodes preserve identity and lineage via `source_node_id`.

---

## 5. Approval & Lifecycle Workflow
1. **Draft Generation**: Replan engine creates draft path version $V_{k+1}$ (`status = "draft"`).
2. **Learner Review**: UI displays "PATH UPDATE RECOMMENDED" with side-by-side diff.
3. **Acceptance**:
   - `POST /learning-paths/{draft_path_id}/accept`
   - $V_{k+1}$ becomes `"active"`.
   - $V_k$ becomes `"superseded"`.
4. **Rejection**:
   - `POST /learning-paths/{draft_path_id}/reject`
   - $V_{k+1}$ becomes `"rejected"`.
   - $V_k$ remains `"active"`.

---

## 6. Minimal-Change Heuristic
To avoid disruptive full-path rebuilds, path deltas minimize total modification cost:
$$\text{ReplanCost} = N_{\text{removed}} + N_{\text{inserted}} + 0.5 \cdot N_{\text{reordered}} + 2.0 \cdot N_{\text{lost\_proof}}$$

---

## 7. API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/learners/{learner_id}/goals/{goal_id}/replan-status` | `GET` | Returns path staleness score and replan recommendation |
| `/api/v1/learners/{learner_id}/goals/{goal_id}/replan` | `POST` | Generates draft path version $V_{k+1}$ with path delta |
| `/api/v1/learning-paths/{path_id}/versions` | `GET` | Returns version lineage history |
| `/api/v1/learning-paths/{from_id}/diff/{to_id}` | `GET` | Returns structured path delta diff |
| `/api/v1/learning-paths/{draft_id}/accept` | `POST` | Accepts draft replan ($V_{k+1} \rightarrow \text{active}$) |
| `/api/v1/learning-paths/{draft_id}/reject` | `POST` | Rejects draft replan ($V_{k+1} \rightarrow \text{rejected}$) |

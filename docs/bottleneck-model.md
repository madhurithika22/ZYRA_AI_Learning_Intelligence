# Bottleneck Detection & Skill Gap Intelligence Model

## Overview

The Bottleneck Detection Engine provides the first deterministic intelligence layer of the Adaptive Learning Intelligence Engine. It analyzes target role requirements, demonstrated learner competencies, directed skill dependency graphs, and diagnostic uncertainty to identify, rank, and explain critical learning bottlenecks.

A core principle of this model is that **LOWEST MASTERY != BOTTLENECK**. A skill with low demonstrated mastery but minimal role importance and zero downstream dependencies should NOT block progress ahead of a high-priority prerequisite skill whose weakness restricts progress across multiple downstream target competencies.

---

## Mathematical Formulations

### 1. Normalized Skill Gap
For each skill $s$ required by target role $R$, the competency gap is calculated as:

$$\text{gap}(s) = \max\left(0.0, \text{normalized\_required\_level}(s, R) - \text{demonstrated\_mastery}(s)\right)$$

Where:
- $\text{normalized\_required\_level}(s, R) \in [0.0, 1.0]$ normalizes standard $1.0-5.0$ role difficulty requirements via $\frac{\text{level} - 1.0}{4.0}$.
- $\text{demonstrated\_mastery}(s) \in [0.0, 1.0]$ is derived from Phase 4 `SkillMastery`.

---

### 2. Weighted Downstream Dependency Impact
Using the directed `SkillRelation` graph, each prerequisite and supporting relationship is traversed recursively:

$$\text{dependency\_impact}(A) = 1.0 + \sum_{B \in \text{Downstream}(A)} \text{relation\_weight}(A \to B) \times \text{role\_importance}(B) \times 0.75^{\text{depth} - 1}$$

Where relation weights are defined as:
- `prerequisite`: $1.0$
- `supports`: $0.5$
- `related`: $0.0$ (ignored for prerequisite impact)

Cycles are prevented via strict `visited` set tracking during graph traversal.

---

### 3. Uncertainty Factor & Bottleneck Score
To prevent zero-evidence unknown skills from dominating solely due to high uncertainty while appropriately weighting diagnostic confidence, the uncertainty factor is defined as:

$$\text{uncertainty\_factor}(s) = 1.0 - \left(\text{confidence}(s) \times 0.5\right)$$

The overall deterministic **Bottleneck Score** is:

$$\text{bottleneck\_score}(s) = \text{gap}(s) \times \text{role\_importance}(s) \times \text{dependency\_impact}(s) \times \text{uncertainty\_factor}(s)$$

---

## Classification & Ranking

### Classification Thresholds
- **`critical`**: $\text{bottleneck\_score} \ge 1.5$ AND $\text{confidence} \ge 0.40$
- **`high`**: $\text{bottleneck\_score} \ge 1.0$ AND $\text{confidence} \ge 0.30$
- **`moderate`**: $\text{bottleneck\_score} \ge 0.50$
- **`low`**: $\text{bottleneck\_score} < 0.50$
- **`insufficient_evidence`**: $\text{evidence\_count} == 0$ OR $\text{confidence} < 0.25$

### Deterministic Tie-Breaking Order
1. `bottleneck_score` descending
2. `role_importance` descending
3. `gap` descending
4. `skill_name` ascending

---

## Known Limitations & Scope
- **Deterministic Prototype**: This model is a deterministic prototype scoring engine, not a statistically validated causal network.
- **Scope Boundary**: Bottleneck detection identifies and ranks learning bottlenecks with structured explanations. It does NOT generate learning path optimizations or course recommendations (which belong to Phase 7).

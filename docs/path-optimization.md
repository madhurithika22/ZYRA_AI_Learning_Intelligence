# Learning Path Optimization Engine

## Overview

The Learning Path Optimization Engine provides the Phase 6 intelligence layer of the Adaptive Learning Intelligence Engine. It converts learner goals, target role requirements, demonstrated competencies (`SkillMastery`), diagnostic confidence, Phase 5 skill gaps and bottlenecks, directed skill dependencies (`SkillRelation`), learning resources, and time constraints into 4 strategy-optimized learning path candidates:

1. **`FASTEST`**: Minimal time completion, strict zero redundancy, high bottleneck focus.
2. **`BALANCED`**: Balanced trade-off between time, target role skill coverage, and practical value.
3. **`DEEP_MASTERY`**: Greater conceptual depth, foundational prerequisite coverage, and reinforcement.
4. **`PROJECT_FIRST`**: Prioritizes hands-on projects, labs, and interactive coding exercises early in sequence.

---

## Core Product Principle
The optimizer does NOT produce a generic list of "courses sorted by relevance". It constructs **an optimized sequence of minimum necessary learning actions that closes the learner's highest-impact gaps while respecting prerequisites, evidence, and time constraints**.

Learners who demonstrate mastery ($\text{mastery} \ge \text{required}$) in a skill (e.g. Python at $84\%$) are NOT assigned redundant introductory content.

---

## Multi-Objective Path Scoring Model

$$\text{PathScore} = w_{\text{mastery}} \cdot \text{MasteryGain} + w_{\text{relevance}} \cdot \text{RoleCoverage} + w_{\text{bottleneck}} \cdot \text{BottleneckCoverage} + w_{\text{practical}} \cdot \text{PracticalValue} - w_{\text{time}} \cdot \text{TimeCost} - w_{\text{redundancy}} \cdot \text{Redundancy} - w_{\text{risk}} \cdot \text{DifficultyRisk}$$

### Strategy Objective Weights

| Objective Weight | `FASTEST` | `BALANCED` | `DEEP_MASTERY` | `PROJECT_FIRST` |
|---|---|---|---|---|
| $w_{\text{mastery}}$ | 1.5 | 1.5 | 2.5 | 1.2 |
| $w_{\text{relevance}}$ | 1.0 | 1.5 | 1.5 | 1.2 |
| $w_{\text{bottleneck}}$ | 2.0 | 1.5 | 1.5 | 1.5 |
| $w_{\text{practical}}$ | 0.5 | 1.0 | 1.0 | 3.0 |
| $w_{\text{time}}$ | 2.5 | 1.0 | 0.4 | 1.0 |
| $w_{\text{redundancy}}$ | 3.0 | 2.0 | 1.0 | 2.0 |
| $w_{\text{risk}}$ | 0.5 | 1.0 | 1.5 | 0.5 |

---

## Prerequisite-Aware Sequencing
Using directed `SkillRelation` records:
- If candidate Resource $R$ targets Skill $S$, and Skill $S$ has unfulfilled prerequisite Skill $P$ ($\text{mastery}(P) < \text{required}(P)$), any candidate resource targeting $P$ MUST be scheduled BEFORE $R$.
- Multi-hop prerequisites are resolved via topological graph sorting.

---

## Path Lifecycle & Persistence
1. `POST /api/v1/learners/{id}/goals/{id}/paths/generate`: Generates 4 strategy candidates stored as `draft` paths in `learning_paths` and `learning_path_nodes`.
2. `POST /api/v1/learning-paths/{id}/activate`: Marks the selected path as `active` and sets other draft candidates for that goal to `archived`.

---

## Zero LLM Dependency
The path optimization engine operates with 100% deterministic algorithms (graph traversal, candidate filtering, greedy multi-objective optimization, structured explanation generation) without making any LLM calls.

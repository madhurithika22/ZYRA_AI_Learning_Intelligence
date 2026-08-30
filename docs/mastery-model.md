# Mastery Engine Technical Specification

The Mastery Engine provides a deterministic, interpretable, and bounded model for updating a learner's estimated skill mastery and evidence confidence based on observed performance evidence.

## Core Principles

1. **Deterministic & Non-LLM Computation**: Numerical mastery scores and confidence estimates are calculated exclusively by explicit algorithm code (`MasteryEngine`), never by an LLM.
2. **Separation of Mastery and Confidence**:
   - **Mastery Score ($M \in [0.0, 1.0]$)**: Represents estimated skill level (0.0 = novice, 1.0 = expert).
   - **Confidence ($C \in [0.0, 1.0]$)**: Represents statistical certainty based on volume, recency, and consistency of observed evidence.
3. **No Mastery from Self-Reports**: Learner-stated existing skills are recorded purely as background metadata in `LearnerProfile` and never create `SkillMastery` or `SkillEvidence` records.

---

## Mastery Update Formula

When a learner answers an assessment question with difficulty $D \in [1.0, 5.0]$, score $S \in [0.0, 1.0]$, and evidence strength $W_{\text{ev}} \in [0.0, 1.0]$:

### 1. Difficulty Normalization & Signal Weighting
$$\text{norm\_diff} = \frac{D - 1.0}{4.0} \in [0.0, 1.0]$$

$$\text{signal} = \begin{cases} 0.70 + 0.30 \times \text{norm\_diff} & \text{if answer is correct } (S = 1.0) \\ 0.30 \times \text{norm\_diff} & \text{if answer is incorrect } (S = 0.0) \end{cases}$$

$$\text{weight} = W_{\text{ev}} \times (1.0 - C_{\text{prev}} \times 0.5) \times 0.40$$

### 2. Incremental Bounded Update
$$M_{\text{new}} = \max\left(0.0, \min\left(1.0, M_{\text{prev}} \times (1.0 - \text{weight}) + \text{signal} \times \text{weight}\right)\right)$$

---

## Confidence Update Formula

$$\Delta C = 0.20 \times W_{\text{ev}} \times (1.0 - C_{\text{prev}})$$

If the observation is consistent with the current mastery direction (correct when $M_{\text{prev}} \ge 0.5$ or incorrect when $M_{\text{prev}} < 0.5$), a consistency bonus is added:

$$\Delta C_{\text{bonus}} = 0.05 \times (1.0 - C_{\text{prev}})$$

$$C_{\text{new}} = \max\left(0.0, \min\left(1.0, C_{\text{prev}} + \Delta C + \Delta C_{\text{bonus}}\right)\right)$$

---

## Known Limitations & Model Scope

- **Prototype Estimator**: This model is a bounded incremental weighted update estimator designed for scalable prototype evaluation. It is not a scientifically validated Bayesian Knowledge Tracing (BKT) or Item Response Theory (IRT) model.
- **Future Enhancements**: Memory decay and spaced repetition forgetting functions belong to future phase retention modules.

# Controlled Evaluation Scenarios (Scenarios A – M)

The evaluation suite consists of 13 controlled scenarios with explicit ground truth expectations:

| Scenario | Title | Description | Expected Ground Truth Behavior |
| :--- | :--- | :--- | :--- |
| **SCENARIO A** | Mastered Skill Skip | Learner has Python mastery = 0.90 (Required = 0.75). | Python fundamentals skipped; estimated minutes saved. |
| **SCENARIO B** | Severe Skill Gap | Learner has Deep Learning gap (mastery = 0.10, required = 0.80). | Deep Learning identified as primary bottleneck. |
| **SCENARIO C** | Low Confidence | Skill mastery = 0.80 but confidence = 0.30. | Scheduled for diagnostic/proof before assuming mastery. |
| **SCENARIO D** | Prerequisite Order | Python is prerequisite for Deep Learning. | Sequence(Python) < Sequence(Deep Learning). |
| **SCENARIO E** | Unproven Attempt | Quiz attempt score = 1.0, proof outcome = None. | Mastery unchanged; action = MASTERY_CHECK. |
| **SCENARIO F** | Bottleneck Shift | Learner passes proof for Deep Learning. | Bottleneck shifts to Model Deployment; Next Action updates. |
| **SCENARIO G** | Obsolete Content | Learner proves external mastery in PyTorch. | Future PyTorch nodes removed/skipped in V2 plan. |
| **SCENARIO H** | Time Constraints | Available time budget = 60 mins out of 300 min catalog. | Highest impact bottleneck resource selected fitting 60m budget. |
| **SCENARIO I** | State Replan Trigger | Mastery delta exceeds threshold (> 0.15). | `replan_required = True` and path delta generated. |
| **SCENARIO J** | Trivial State Update | Mastery delta is 0.02 (< threshold 0.15). | `replan_required = False` (prevents plan churn). |
| **SCENARIO K** | Role Weighting | MLOps role_skill weight = 2.5 vs Stats = 1.0. | MLOps prioritized over Statistics as bottleneck. |
| **SCENARIO L** | Evidence Conflict | Quiz score = 1.0 vs Diagnostic score = 0.2. | Mastery engine calculates conservative confidence-weighted score. |
| **SCENARIO M** | Grounded Query | Learner asks "Why is Model Deployment my bottleneck?". | Answer grounded in backend state with explicit source links. |

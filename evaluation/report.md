# Phase 13 — Evaluation & Baseline Comparison Report

**Run ID**: `eval-run-0d9dd845`  
**Timestamp**: `2026-08-30 12:19:22` GMT  
**Dataset Version**: `v1.0-controlled-scenarios`  

## 1. Summary Metrics

| Evaluation Metric | Value |
| :--- | :--- |
| Unnecessary Resources Avoided | **1** |
| Unnecessary Estimated Minutes Avoided | **120 mins** |
| Prerequisite Ordering Accuracy | **100.0%** |
| Bottleneck Controlled-Case Accuracy | **100.0%** |
| Next-Action Adaptive Decision Rate | **100.0%** |
| Replan Minimal-Change Preservation Rate | **92.0%** |
| Grounded Claim Rate | **100.0%** |
| Source Attribution Accuracy | **100.0%** |
| Cross-Service Consistency Mismatches | **0** |
| Security Attack Cases Passed | **6 / 6** |
| LLM Cost Control Bypass Rate | **40.0%** |

## 2. Baseline Comparison Table

| Capability / Metric | Conventional Baseline | Adaptive Learning Intelligence Engine |
| :--- | :--- | :--- |
| **Mastery-Aware Filtering** | No (Recommends mastered content) | **Yes (Filters mastered skills)** |
| **Prerequisite Sequencing** | Static catalog order | **Topological dependency graph** |
| **Bottleneck Identification** | None (Uses static popularity) | **Role-weighted bottleneck analysis** |
| **Proof-of-Mastery Gating** | No (Assumes completion = mastery) | **Yes (Gated by evidence & diagnostic)** |
| **Dynamic Replanning** | No (Static course list) | **Yes (Delta-triggered re-optimization)** |
| **Grounded Conversational AI** | No (N/A) | **Yes (Source-attributed Gemini AI)** |
| **LLM Cost Control** | N/A | **Yes (Deterministic status query bypass)** |

## 3. Detailed Controlled Scenario Results

### SCENARIO_A: Learner Has Already Mastered Python [PASS]
- **Description**: Learner has Python mastery=0.90 (Required=0.75).
- **Expected**: Python fundamentals should be skipped by our engine.
- **Baseline Output**: `{'recommended_count': 4, 'contains_python': True}`
- **Our System Output**: `{'recommended_count': 3, 'contains_python': False}`
- **Explanation**: Baseline recommended Python because it has high static relevance score (0.95). Our system filtered Python based on mastery state.

### SCENARIO_B: Severe Deep Learning Gap [PASS]
- **Description**: Learner has Deep Learning mastery=0.10 (Required=0.80).
- **Expected**: Deep Learning identified as primary bottleneck.
- **Baseline Output**: `{'top_recommendation': 'Python Fundamentals Basics'}`
- **Our System Output**: `{'primary_bottleneck': 'Deep Learning', 'next_action': 'LEARN_NODE'}`
- **Explanation**: Our system prioritized the severe skill gap as primary bottleneck, while baseline recommended top-relevance resource regardless of gap.

### SCENARIO_C: High Mastery / Low Confidence Skill [PASS]
- **Description**: PyTorch has score=0.80 but confidence=0.30.
- **Expected**: System schedules diagnostic/proof of mastery for PyTorch before assuming true mastery.
- **Baseline Output**: `{'action': 'RECOMMEND_GENERAL_COURSE'}`
- **Our System Output**: `{'action': 'MASTERY_CHECK', 'target_skill': 'PyTorch'}`
- **Explanation**: Our system triggers diagnostic check for low confidence skills to ground mastery evidence.

### SCENARIO_D: Prerequisite Sequencing Constraint [PASS]
- **Description**: Python is prerequisite for Deep Learning.
- **Expected**: Python sequence index < Deep Learning sequence index.
- **Baseline Output**: `{'prerequisite_enforced': False}`
- **Our System Output**: `{'sequence_order': ['Python', 'Deep Learning'], 'prerequisite_valid': True}`
- **Explanation**: Prerequisite sequencer guarantees valid topological ordering.

### SCENARIO_E: Completed Activity Without Proof [PASS]
- **Description**: Activity attempt completed with score=1.0 but proof outcome is None.
- **Expected**: Mastery score remains unchanged until proof of mastery passed.
- **Baseline Output**: `{'assumes_mastery': True}`
- **Our System Output**: `{'mastery_changed': False, 'requires_proof': True}`
- **Explanation**: Proof-aware mastery engine prevents unproven mastery jumps.

### SCENARIO_F: Bottleneck Shift Upon Proof Resolution [PASS]
- **Description**: Learner passes proof of mastery for Deep Learning.
- **Expected**: Primary bottleneck shifts to Model Deployment; Next Action updates.
- **Baseline Output**: `{'relevance_shift': False}`
- **Our System Output**: `{'previous_bottleneck': 'Deep Learning', 'new_bottleneck': 'Model Deployment', 'decision_changed': True}`
- **Explanation**: Next Action engine recalculates optimal action upon state update.

### SCENARIO_G: Future Path Content Becomes Obsolete [PASS]
- **Description**: Learner proves external mastery in PyTorch.
- **Expected**: PyTorch path nodes marked obsolete/skipped in V2 plan.
- **Baseline Output**: `{'path_updated': False}`
- **Our System Output**: `{'obsolete_nodes_skipped': 1, 'path_version': 'v2'}`
- **Explanation**: Dynamic replanning engine removes redundant nodes when mastery is achieved externally.

### SCENARIO_H: Constrained Time Budget [PASS]
- **Description**: Learner has 60 minutes available out of 300 minute catalog.
- **Expected**: Highest impact bottleneck resource selected fitting 60 min budget.
- **Baseline Output**: `{'total_minutes': 120}`
- **Our System Output**: `{'selected_resource': 'PyTorch Tensor Operations', 'total_minutes': 60}`
- **Explanation**: Path optimizer enforces strict max_minutes constraint.

### SCENARIO_I: State Change Triggers Dynamic Replan [PASS]
- **Description**: Mastery delta exceeds threshold (>0.15).
- **Expected**: replan_required becomes True and path delta generated.
- **Baseline Output**: `{'replan_supported': False}`
- **Our System Output**: `{'replan_required': True, 'trigger': 'BOTTLENECK_RESOLVED'}`
- **Explanation**: Change detection service triggers replan on significant state changes.

### SCENARIO_J: Minor State Change Does Not Replan [PASS]
- **Description**: Mastery delta is 0.02 (< threshold 0.15).
- **Expected**: replan_required remains False to prevent path churn.
- **Baseline Output**: `{'replan_supported': False}`
- **Our System Output**: `{'replan_required': False}`
- **Explanation**: Replanning engine avoids unnecessary plan churn on trivial state updates.

### SCENARIO_K: Differentiated Role Skill Importance [PASS]
- **Description**: MLOps has role_skill weight=2.5 vs Stats weight=1.0.
- **Expected**: MLOps prioritized over Statistics as bottleneck.
- **Baseline Output**: `{'top_pick': 'Python'}`
- **Our System Output**: `{'primary_bottleneck': 'Model Deployment'}`
- **Explanation**: Bottleneck analysis weighs skill importance for the specific target role.

### SCENARIO_L: Conflicting Evidence Reconciliation [PASS]
- **Description**: Learner scored 1.0 on quiz but 0.2 on diagnostic.
- **Expected**: Mastery engine computes conservative confidence-weighted score.
- **Baseline Output**: `{'score': 1.0}`
- **Our System Output**: `{'reconciled_score': 0.45, 'confidence': 0.5}`
- **Explanation**: Mastery engine uses variance and source weight to reconcile conflicting evidence.

### SCENARIO_M: Grounded Conversational Explanation [PASS]
- **Description**: Learner asks 'Why is Model Deployment my bottleneck?'.
- **Expected**: Response is grounded in backend state with explicit source references.
- **Baseline Output**: `{'grounding_supported': False}`
- **Our System Output**: `{'response_type': 'LEARNER_GROUNDED_RESPONSE', 'sources_count': 2, 'grounded_claims': True}`
- **Explanation**: Conversational intelligence uses grounded context and source validation.


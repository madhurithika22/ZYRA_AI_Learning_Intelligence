# Phase 13 Evaluation Metrics Definitions

## 1. Unnecessary Learning Avoided
- **UnnecessaryLearningAvoided**: Count of resources recommended by conventional baseline that target already-sufficient skills ($>0.75$) and are filtered out by our system.
- **UnnecessaryEstimatedMinutesAvoided**: Total estimated content duration (minutes) avoided by filtering mastered skills.

## 2. Prerequisite Accuracy
$$\text{PrerequisiteAccuracy} = \frac{\text{Valid Prerequisite Ordering Pairs}}{\text{All Tested Prerequisite Relationships}}$$

## 3. Bottleneck Identification Accuracy
Controlled-case accuracy measuring whether the identified primary bottleneck matches expected ground truth for synthetic test cases.

## 4. Next-Action Adaptivity
$$\text{AdaptiveDecisionRate} = \frac{\text{Cases where decision changed upon state modification}}{\text{Total state modification test cases}}$$

## 5. Replan Minimality & Preservation
$$\text{PreservationRate} = \frac{\text{Unchanged useful nodes preserved in V2 plan}}{\text{Total useful nodes in V1 plan}}$$

## 6. Grounding Quality & Source Attribution
- **GroundedClaimRate**: Proportion of learner-state assertions backed by authoritative domain state. Target: 100%.
- **SourceAttributionAccuracy**: Proportion of claims correctly mapped to validated backend source IDs.

## 7. LLM Cost Control Bypass Rate
$$\text{LLMBypassRate} = \frac{\text{Factual status queries answered directly without LLM}}{\text{Total conversational queries}}$$
Target: >40% cost reduction on common factual queries.

# Evaluation Architecture & Conventional Baseline Definition

## 1. Baseline Definition (`BaselineRecommendationEngine`)
The conventional baseline represents a standard course recommender used in non-adaptive learning management systems. It ranks learning resources based solely on static metadata (such as resource-to-skill relevance scores and duration) without taking into account:
- Learner skill mastery scores
- Learner confidence
- Structural bottleneck analysis
- Prerequisite graph dependencies
- Proof-of-mastery evidence
- Dynamic replanning history
- Next-best-action priorities

## 2. Fair Comparison Methodology
Both the conventional baseline and our Adaptive Learning Intelligence Engine are evaluated under strict parity constraints:
- **Same Learner Profile**: Identical goal, target role, and initial assessment data.
- **Same Resource Catalog**: Identical candidate resources and estimated duration values.
- **Same Role Skill Weights**: Identical role requirements.
- **Same Time Constraints**: Identical max minutes budget allocations.

## 3. Explicit Baseline Limitations
1. **No Mastery Awareness**: Baseline continues recommending resources for skills the learner has already mastered ($>0.75$).
2. **No Dependency Enforcement**: Baseline ranks items purely by relevance score, potentially ordering advanced topics before fundamental prerequisites.
3. **No Bottleneck Prioritization**: Baseline ranks by static resource relevance rather than focusing time on the learner's specific structural bottleneck.
4. **No Evidence Gating**: Baseline assumes resource completion implies mastery without proof validation.

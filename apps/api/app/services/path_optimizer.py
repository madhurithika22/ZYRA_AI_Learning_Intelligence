from typing import NamedTuple
from uuid import UUID

from app.core.constants import (
    STRATEGY_BALANCED,
    STRATEGY_DEEP_MASTERY,
    STRATEGY_FASTEST,
    STRATEGY_PROJECT_FIRST,
)
from app.schemas.bottleneck import BottleneckAnalysisResponse
from app.services.resource_candidate_filter import CandidateResource


class StrategyWeights(NamedTuple):
    w_mastery: float
    w_relevance: float
    w_bottleneck: float
    w_practical: float
    w_time: float
    w_redundancy: float
    w_risk: float


STRATEGY_WEIGHTS: dict[str, StrategyWeights] = {
    STRATEGY_FASTEST: StrategyWeights(
        w_mastery=1.5,
        w_relevance=1.0,
        w_bottleneck=2.0,
        w_practical=0.5,
        w_time=2.5,
        w_redundancy=3.0,
        w_risk=0.5,
    ),
    STRATEGY_BALANCED: StrategyWeights(
        w_mastery=1.5,
        w_relevance=1.5,
        w_bottleneck=1.5,
        w_practical=1.0,
        w_time=1.0,
        w_redundancy=2.0,
        w_risk=1.0,
    ),
    STRATEGY_DEEP_MASTERY: StrategyWeights(
        w_mastery=2.5,
        w_relevance=1.5,
        w_bottleneck=1.5,
        w_practical=1.0,
        w_time=0.4,
        w_redundancy=1.0,
        w_risk=1.5,
    ),
    STRATEGY_PROJECT_FIRST: StrategyWeights(
        w_mastery=1.2,
        w_relevance=1.2,
        w_bottleneck=1.5,
        w_practical=3.0,
        w_time=1.0,
        w_redundancy=2.0,
        w_risk=0.5,
    ),
}


class OptimizationMetrics(NamedTuple):
    total_minutes: int
    estimated_weeks: float
    mastery_gain: float
    role_coverage: float
    bottleneck_coverage: float
    practical_value: float
    redundancy_score: float
    risk_score: float
    path_score: float
    feasible: bool
    warning_message: str | None


class PathOptimizer:
    """Deterministic multi-objective optimizer for learning path sequence generation."""

    def optimize_path(
        self,
        strategy: str,
        candidates: list[CandidateResource],
        bottleneck_analysis: BottleneckAnalysisResponse,
        prereq_map: dict[UUID, set[UUID]],
        daily_minutes: int = 60,
        timeline_weeks: int = 12,
    ) -> tuple[list[CandidateResource], OptimizationMetrics, str]:
        bottleneck_id = (
            bottleneck_analysis.primary_bottleneck.skill_id
            if bottleneck_analysis.primary_bottleneck
            else None
        )
        target_skills_with_gaps = {
            g.skill_id: g.gap for g in bottleneck_analysis.all_gaps if g.gap > 0.0
        }

        # 1. Select subset of resources tailored to strategy
        selected = self._select_resource_subset(
            strategy=strategy,
            candidates=candidates,
            target_gaps=target_skills_with_gaps,
            bottleneck_id=bottleneck_id,
        )

        # 2. Sequence selected resources respecting prerequisites
        from app.services.prerequisite_sequencer import PrerequisiteSequencer

        sequencer = PrerequisiteSequencer(session=None)  # Pure sequence method
        mastered_skill_ids = {g.skill_id for g in bottleneck_analysis.all_gaps if g.gap == 0.0}
        sequenced = sequencer.sequence_resources(
            candidate_resources=selected,
            prereq_map=prereq_map,
            mastered_skill_ids=mastered_skill_ids,
        )

        # 3. Compute optimization metrics and multi-objective score
        metrics = self.calculate_metrics(
            strategy=strategy,
            sequence=sequenced,
            bottleneck_analysis=bottleneck_analysis,
            daily_minutes=daily_minutes,
            timeline_weeks=timeline_weeks,
        )

        # 4. Build structured explanation
        explanation = self._build_explanation(
            strategy=strategy,
            sequence=sequenced,
            metrics=metrics,
            bottleneck_analysis=bottleneck_analysis,
        )

        return sequenced, metrics, explanation

    def _select_resource_subset(
        self,
        strategy: str,
        candidates: list[CandidateResource],
        target_gaps: dict[UUID, float],
        bottleneck_id: UUID | None,
    ) -> list[CandidateResource]:
        if not candidates:
            return []

        # Sort candidate pool based on strategy focus
        if strategy == STRATEGY_FASTEST:
            # Maximizes incremental gap closing per minute
            sorted_cand = sorted(
                candidates,
                key=lambda r: (
                    -(r.incremental_gap_value / max(1, r.estimated_minutes)),
                    -r.incremental_gap_value,
                ),
            )
        elif strategy == STRATEGY_PROJECT_FIRST:
            # Prioritizes practical / applied resources
            sorted_cand = sorted(
                candidates,
                key=lambda r: (
                    -r.practical_value,
                    -r.incremental_gap_value,
                ),
            )
        elif strategy == STRATEGY_DEEP_MASTERY:
            # Prefers comprehensive coverage and foundational resources
            sorted_cand = sorted(
                candidates,
                key=lambda r: (
                    -r.incremental_gap_value,
                    -r.practical_value,
                ),
            )
        else:  # BALANCED
            sorted_cand = sorted(
                candidates,
                key=lambda r: (
                    -(r.incremental_gap_value * r.practical_value),
                    -r.incremental_gap_value,
                ),
            )

        # Greedy selection with redundancy control
        selected: list[CandidateResource] = []
        covered_skill_ids: set[UUID] = set()

        for r in sorted_cand:
            # Check if resource provides new gap-closing coverage
            new_coverage = any(
                cov.skill_id in target_gaps and cov.skill_id not in covered_skill_ids
                for cov in r.covered_skills
            )

            if strategy == STRATEGY_FASTEST:
                # Fastest picks only 1 best resource per gap, strict non-redundancy
                if new_coverage:
                    selected.append(r)
                    for cov in r.covered_skills:
                        covered_skill_ids.add(cov.skill_id)
            elif strategy == STRATEGY_PROJECT_FIRST:
                # Project first includes project resources and supporting candidates
                if new_coverage or (r.practical_value >= 0.8 and len(selected) < 4):
                    selected.append(r)
                    for cov in r.covered_skills:
                        covered_skill_ids.add(cov.skill_id)
            elif strategy == STRATEGY_DEEP_MASTERY:
                # Deep mastery allows up to 2 resources per skill for depth
                if new_coverage or len(selected) < len(target_gaps) + 2:
                    selected.append(r)
                    for cov in r.covered_skills:
                        covered_skill_ids.add(cov.skill_id)
            else:  # BALANCED
                if new_coverage or len(selected) < len(target_gaps) + 1:
                    selected.append(r)
                    for cov in r.covered_skills:
                        covered_skill_ids.add(cov.skill_id)

        return selected

    def calculate_metrics(
        self,
        strategy: str,
        sequence: list[CandidateResource],
        bottleneck_analysis: BottleneckAnalysisResponse,
        daily_minutes: int,
        timeline_weeks: int,
    ) -> OptimizationMetrics:
        weights = STRATEGY_WEIGHTS.get(strategy, STRATEGY_WEIGHTS[STRATEGY_BALANCED])
        total_minutes = sum(r.estimated_minutes for r in sequence)
        hours = total_minutes / 60.0

        # Time budget check
        max_total_minutes = daily_minutes * 7 * timeline_weeks
        feasible = total_minutes <= max_total_minutes
        warning_msg = None
        if not feasible:
            warning_msg = f"Path estimated duration ({round(hours, 1)} hrs) exceeds time budget of {round(max_total_minutes / 60.0, 1)} hrs ({timeline_weeks} wks @ {daily_minutes} mins/day)."

        estimated_weeks = round(total_minutes / max(1, daily_minutes * 7), 1)

        # Target role skill coverage
        target_skills = {g.skill_id for g in bottleneck_analysis.all_gaps if g.gap > 0.0}
        covered_targets = set()
        for r in sequence:
            for cov in r.covered_skills:
                if cov.skill_id in target_skills:
                    covered_targets.add(cov.skill_id)

        role_coverage = len(covered_targets) / max(1, len(target_skills))

        # Bottleneck coverage
        b_id = (
            bottleneck_analysis.primary_bottleneck.skill_id
            if bottleneck_analysis.primary_bottleneck
            else None
        )
        b_covered = False
        if b_id:
            for r in sequence:
                if any(cov.skill_id == b_id for cov in r.covered_skills):
                    b_covered = True
                    break

        bottleneck_coverage = 1.0 if b_covered else 0.0
        mastery_gain = min(
            1.0, sum(r.incremental_gap_value for r in sequence) / max(1.0, len(target_skills))
        )
        practical_val = (
            (sum(r.practical_value for r in sequence) / max(1, len(sequence))) if sequence else 0.0
        )

        # Redundancy penalty: proportion of overlapping skills covered > 1 time
        skill_counts: dict[UUID, int] = {}
        for r in sequence:
            for cov in r.covered_skills:
                skill_counts[cov.skill_id] = skill_counts.get(cov.skill_id, 0) + 1

        redundant_cnt = sum(cnt - 1 for cnt in skill_counts.values() if cnt > 1)
        redundancy_score = round(redundant_cnt / max(1, len(sequence)), 2)

        # Risk score: proportion of high difficulty resources (> 3.5)
        high_diff_cnt = sum(1 for r in sequence if r.difficulty > 3.5)
        risk_score = round(high_diff_cnt / max(1, len(sequence)), 2)

        # Time cost normalized [0, 1] relative to budget
        time_cost = min(1.0, total_minutes / max(1, max_total_minutes))

        # PathScore formula
        score = (
            weights.w_mastery * mastery_gain
            + weights.w_relevance * role_coverage
            + weights.w_bottleneck * bottleneck_coverage
            + weights.w_practical * practical_val
            - weights.w_time * time_cost
            - weights.w_redundancy * redundancy_score
            - weights.w_risk * risk_score
        )

        return OptimizationMetrics(
            total_minutes=total_minutes,
            estimated_weeks=estimated_weeks,
            mastery_gain=round(mastery_gain, 4),
            role_coverage=round(role_coverage, 4),
            bottleneck_coverage=round(bottleneck_coverage, 4),
            practical_value=round(practical_val, 4),
            redundancy_score=redundancy_score,
            risk_score=risk_score,
            path_score=round(score, 4),
            feasible=feasible,
            warning_message=warning_msg,
        )

    def _build_explanation(
        self,
        strategy: str,
        sequence: list[CandidateResource],
        metrics: OptimizationMetrics,
        bottleneck_analysis: BottleneckAnalysisResponse,
    ) -> str:
        b_name = (
            bottleneck_analysis.primary_bottleneck.skill_name
            if bottleneck_analysis.primary_bottleneck
            else "primary bottleneck"
        )

        if strategy == STRATEGY_FASTEST:
            return f"FASTEST path optimized for rapid goal completion in {metrics.estimated_weeks} weeks ({round(metrics.total_minutes / 60, 1)} hrs). Directly addresses critical bottleneck '{b_name}' with minimal redundant content."
        elif strategy == STRATEGY_DEEP_MASTERY:
            return f"DEEP MASTERY path builds comprehensive conceptual depth over {metrics.estimated_weeks} weeks. Incorporates foundational prerequisites before advanced topics in '{b_name}'."
        elif strategy == STRATEGY_PROJECT_FIRST:
            return f"PROJECT FIRST path prioritizes applied labs and coding projects ({round(metrics.practical_value * 100)}% practical focus). Schedules hands-on activities early in sequence."
        else:
            return f"BALANCED path balances time efficiency, target role coverage ({round(metrics.role_coverage * 100)}%), and practical exercises. Recommended for optimal learning outcome."

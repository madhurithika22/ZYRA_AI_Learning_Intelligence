from datetime import datetime, timezone
from uuid import UUID

from app.core.constants import (
    PATH_STATUS_ACTIVE,
    PATH_STATUS_ARCHIVED,
    PATH_STATUS_DRAFT,
    STRATEGY_BALANCED,
    STRATEGY_DEEP_MASTERY,
    STRATEGY_FASTEST,
    STRATEGY_PROJECT_FIRST,
)
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learner_profile import LearnerProfile
from app.models.learning_path import LearningPath
from app.models.learning_path_node import LearningPathNode
from app.schemas.learning_path import (
    ActivatePathResponse,
    PathComparisonResponse,
    PathNodeResponse,
    PathStrategyOption,
)
from app.services.bottleneck_analysis import BottleneckAnalysisService
from app.services.path_optimizer import OptimizationMetrics, PathOptimizer
from app.services.prerequisite_sequencer import PrerequisiteSequencer
from app.services.resource_candidate_filter import CandidateResource, ResourceCandidateFilter
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class LearningPathService:
    """Application service for generating, persisting, comparing, and activating learning paths."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.bottleneck_service = BottleneckAnalysisService(session)
        self.candidate_filter = ResourceCandidateFilter(session)
        self.sequencer = PrerequisiteSequencer(session)
        self.optimizer = PathOptimizer()

    async def generate_candidate_paths(
        self,
        learner_id: UUID,
        goal_id: UUID,
    ) -> PathComparisonResponse:
        now = datetime.now(timezone.utc)

        # 1. Validate learner & goal
        learner = await self.session.get(Learner, learner_id)
        if not learner:
            raise ValueError(f"Learner with ID '{learner_id}' not found.")

        goal = await self.session.get(Goal, goal_id)
        if not goal:
            raise ValueError(f"Goal with ID '{goal_id}' not found.")

        # Load profile and goal time preferences
        prof_stmt = select(LearnerProfile).where(LearnerProfile.learner_id == learner_id)
        prof_res = await self.session.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()

        daily_mins = 60
        if goal.daily_minutes and goal.daily_minutes > 0:
            daily_mins = goal.daily_minutes
        elif profile and profile.weekly_availability_hours:
            daily_mins = max(15, int((profile.weekly_availability_hours * 60) / 7))

        timeline_wks = (
            goal.timeline_weeks if goal.timeline_weeks and goal.timeline_weeks > 0 else 12
        )

        # 2. Get Phase 5 Bottleneck Analysis
        b_analysis = await self.bottleneck_service.analyze_bottlenecks(learner_id, goal_id)

        target_skill_gaps = {g.skill_id: g.gap for g in b_analysis.all_gaps}
        role_importance_map = {g.skill_id: g.role_importance for g in b_analysis.all_gaps}
        mastered_ids = {g.skill_id for g in b_analysis.all_gaps if g.gap == 0.0}

        # 3. Load catalog candidates & prerequisite map
        candidates = await self.candidate_filter.get_candidate_resources(
            target_skill_gaps=target_skill_gaps,
            role_importance_map=role_importance_map,
            mastered_skill_ids=mastered_ids,
        )
        prereq_map = await self.sequencer.get_prerequisite_map()

        # 4. Generate 4 strategy-optimized candidate paths
        strategies = [
            STRATEGY_FASTEST,
            STRATEGY_BALANCED,
            STRATEGY_DEEP_MASTERY,
            STRATEGY_PROJECT_FIRST,
        ]
        options: dict[str, PathStrategyOption] = {}

        for strat in strategies:
            sequence, metrics, explanation = self.optimizer.optimize_path(
                strategy=strat,
                candidates=candidates,
                bottleneck_analysis=b_analysis,
                prereq_map=prereq_map,
                daily_minutes=daily_mins,
                timeline_weeks=timeline_wks,
            )

            # Persist draft path or reuse existing draft if identical
            path_obj = await self._persist_draft_path(
                learner_id=learner_id,
                goal_id=goal_id,
                strategy=strat,
                sequence=sequence,
                metrics=metrics,
                explanation=explanation,
            )

            nodes_resp = [
                PathNodeResponse(
                    id=n.id,
                    sequence=n.sequence,
                    resource_id=n.resource_id,
                    resource_title=n.resource.title
                    if n.resource
                    else f"Resource Step {n.sequence}",
                    resource_type=n.resource.resource_type if n.resource else "learning_activity",
                    resource_url=n.resource.source_url if n.resource else None,
                    skill_id=n.skill_id,
                    skill_name=n.skill.name if n.skill else "Target Skill",
                    estimated_minutes=n.estimated_minutes or 60,
                    rationale=n.rationale or explanation,
                )
                for n in path_obj.nodes
            ]

            options[strat] = PathStrategyOption(
                path_id=path_obj.id,
                strategy=strat,
                name=path_obj.name,
                status=path_obj.status,
                feasible=metrics.feasible,
                estimated_minutes=metrics.total_minutes,
                estimated_weeks=metrics.estimated_weeks,
                total_resources=len(sequence),
                target_skill_coverage=metrics.role_coverage,
                bottleneck_coverage=metrics.bottleneck_coverage,
                practical_value=metrics.practical_value,
                redundancy_score=metrics.redundancy_score,
                risk_score=metrics.risk_score,
                path_score=metrics.path_score,
                explanation=explanation,
                warning_message=metrics.warning_message,
                nodes=nodes_resp,
            )

        await self.session.commit()
        return PathComparisonResponse(
            learner_id=learner_id,
            goal_id=goal_id,
            target_role=b_analysis.target_role,
            generated_at=now,
            options=options,
        )

    async def _persist_draft_path(
        self,
        learner_id: UUID,
        goal_id: UUID,
        strategy: str,
        sequence: list[CandidateResource],
        metrics: OptimizationMetrics,
        explanation: str,
    ) -> LearningPath:

        # Check if draft path for this strategy already exists
        existing_stmt = (
            select(LearningPath)
            .where(
                LearningPath.learner_id == learner_id,
                LearningPath.goal_id == goal_id,
                LearningPath.strategy == strategy,
                LearningPath.status == PATH_STATUS_DRAFT,
            )
            .options(
                selectinload(LearningPath.nodes).selectinload(LearningPathNode.resource),
                selectinload(LearningPath.nodes).selectinload(LearningPathNode.skill),
            )
        )
        res = await self.session.execute(existing_stmt)
        existing_path = res.scalars().first()

        if existing_path:
            # Update metrics and return existing path cleanly
            existing_path.estimated_minutes = metrics.total_minutes
            existing_path.expected_readiness = metrics.path_score
            await self.session.flush()
            return existing_path

        # Create new LearningPath object
        strat_display = strategy.replace("_", " ").title()
        path = LearningPath(
            learner_id=learner_id,
            goal_id=goal_id,
            name=f"{strat_display} Learning Path",
            strategy=strategy,
            status=PATH_STATUS_DRAFT,
            estimated_minutes=metrics.total_minutes,
            expected_readiness=metrics.path_score,
        )

        self.session.add(path)
        await self.session.flush()

        # Add sequence nodes
        for idx, r in enumerate(sequence, start=1):
            primary_skill_id = r.covered_skills[0].skill_id if r.covered_skills else None
            node = LearningPathNode(
                learning_path_id=path.id,
                sequence=idx,
                resource_id=r.resource_id,
                skill_id=primary_skill_id,
                milestone_label=f"Step {idx}: {r.title}",
                estimated_minutes=r.estimated_minutes,
                rationale=f"Step {idx} in {strategy} sequence targeting {r.title}.",
            )
            self.session.add(node)

        await self.session.flush()

        # Reload with relationships
        reload_stmt = (
            select(LearningPath)
            .where(LearningPath.id == path.id)
            .options(
                selectinload(LearningPath.nodes).selectinload(LearningPathNode.resource),
                selectinload(LearningPath.nodes).selectinload(LearningPathNode.skill),
            )
        )
        return (await self.session.execute(reload_stmt)).scalar_one()

    async def activate_path(
        self,
        path_id: UUID,
        learner_id: UUID,
    ) -> ActivatePathResponse:
        now = datetime.now(timezone.utc)
        path = await self.session.get(LearningPath, path_id)
        if not path:
            raise ValueError(f"Learning path with ID '{path_id}' not found.")
        if path.learner_id != learner_id:
            raise ValueError("Learner does not own this learning path.")

        # Archive other draft/active paths for this goal
        archive_stmt = (
            update(LearningPath)
            .where(
                LearningPath.goal_id == path.goal_id,
                LearningPath.id != path_id,
                LearningPath.status.in_([PATH_STATUS_DRAFT, PATH_STATUS_ACTIVE]),
            )
            .values(status=PATH_STATUS_ARCHIVED)
        )
        await self.session.execute(archive_stmt)

        # Mark target path active
        path.status = PATH_STATUS_ACTIVE
        await self.session.commit()

        return ActivatePathResponse(
            path_id=path.id,
            learner_id=learner_id,
            goal_id=path.goal_id,
            strategy=path.strategy,
            status=PATH_STATUS_ACTIVE,
            activated_at=now,
            message=f"Learning path '{path.name}' successfully activated.",
        )

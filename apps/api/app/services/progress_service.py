from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learner_profile import LearnerProfile
from app.models.learning_activity_attempt import LearningActivityAttempt
from app.models.learning_path import LearningPath
from app.models.learning_path_node import LearningPathNode
from app.models.mastery_outcome import MasteryOutcome
from app.models.role import Role
from app.models.role_skill import RoleSkill
from app.models.skill import Skill
from app.models.skill_evidence import SkillEvidence
from app.models.skill_mastery import SkillMastery
from app.schemas.progress import (
    GoalSkillProgressResponse,
    LearnerProgressSummary,
    NodeProgressItem,
    PathProgressResponse,
    RecentChangeItem,
    SkillHistoryItem,
    SkillProgressItem,
    TimelineProgressResponse,
)
from app.services.bottleneck_analysis import BottleneckAnalysisService
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ProgressService:
    """Service aggregating longitudinal learning progress and learner state deterministically."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_learner_progress_summary(
        self, learner_id: UUID
    ) -> LearnerProgressSummary:
        """Fetch full progress summary for a learner across their active goal and learning path."""
        # 1. Verify Learner exists
        learner = (
            await self.db.execute(select(Learner).where(Learner.id == learner_id))
        ).scalar_one_or_none()
        if not learner:
            raise ValueError(f"Learner with ID {learner_id} not found.")

        # 2. Get active goal
        goal_stmt = (
            select(Goal)
            .where(Goal.learner_id == learner_id)
            .order_by(Goal.created_at.desc())
        )
        goal = (await self.db.execute(goal_stmt)).scalars().first()

        if not goal:
            # Return baseline summary if learner has no goal yet
            return LearnerProgressSummary(
                learner_id=learner_id,
                target_role_name="No Active Goal",
                timeline_progress=TimelineProgressResponse(
                    actual_time_spent_minutes=0,
                    path_estimated_remaining_minutes=0,
                    descriptive_pace=0.0,
                    pace_description="No active learning path or time budget configured.",
                ),
            )

        # 3. Get target role name
        role_stmt = select(Role).where(Role.id == goal.target_role_id)
        role = (await self.db.execute(role_stmt)).scalar_one_or_none()
        target_role_name = role.name if role else "Target Role"

        # 4. Get active path
        path_stmt = (
            select(LearningPath)
            .where(
                LearningPath.learner_id == learner_id,
                LearningPath.goal_id == goal.id,
                LearningPath.status == "active",
            )
            .order_by(LearningPath.created_at.desc())
        )
        active_path = (await self.db.execute(path_stmt)).scalars().first()

        path_progress: PathProgressResponse | None = None
        nodes_progress: list[NodeProgressItem] = []
        if active_path:
            path_progress = await self.get_path_progress(learner_id, active_path.id)
            nodes_progress = await self._get_nodes_progress(learner_id, active_path.id)

        # 5. Get skill progress and goal skill progress proxy
        skills_progress, goal_skill_progress = await self._get_skills_progress(
            learner_id, goal
        )

        # 6. Get recent changes
        recent_changes = await self._get_recent_changes(learner_id)

        # 7. Get timeline progress
        timeline_progress = await self._get_timeline_progress(
            learner_id, goal, path_progress
        )

        # 8. Get Phase 5 bottleneck summary without duplicating logic
        bottleneck_summary: dict[str, Any] | None = None
        try:
            bottleneck_service = BottleneckAnalysisService(self.db)
            b_data = await bottleneck_service.analyze_bottlenecks(learner_id, goal.id)
            if b_data.primary_bottleneck:
                bottleneck_summary = b_data.primary_bottleneck.model_dump()
        except Exception:
            bottleneck_summary = None

        return LearnerProgressSummary(
            learner_id=learner_id,
            active_goal_id=goal.id,
            target_role_name=target_role_name,
            goal_skill_progress=goal_skill_progress.goal_skill_progress,
            path_progress=path_progress,
            nodes_progress=nodes_progress,
            skills_progress=skills_progress,
            recent_changes=recent_changes,
            timeline_progress=timeline_progress,
            primary_bottleneck=bottleneck_summary,
        )

    async def get_goal_progress(
        self, learner_id: UUID, goal_id: UUID
    ) -> GoalSkillProgressResponse:
        """Fetch goal skill progress proxy and status breakdown for a goal."""
        goal = (
            await self.db.execute(
                select(Goal).where(Goal.id == goal_id, Goal.learner_id == learner_id)
            )
        ).scalar_one_or_none()
        if not goal:
            raise ValueError(f"Goal {goal_id} not found for learner {learner_id}.")

        _, goal_progress = await self._get_skills_progress(learner_id, goal)
        return goal_progress

    async def get_path_progress(
        self, learner_id: UUID, path_id: UUID
    ) -> PathProgressResponse:
        """Calculate node completion and time progress for a specific LearningPath."""
        path = (
            await self.db.execute(
                select(LearningPath).where(
                    LearningPath.id == path_id, LearningPath.learner_id == learner_id
                )
            )
        ).scalar_one_or_none()
        if not path:
            raise ValueError(f"LearningPath {path_id} not found for learner {learner_id}.")

        nodes_stmt = (
            select(LearningPathNode)
            .where(LearningPathNode.learning_path_id == path_id)
            .order_by(LearningPathNode.sequence)
        )
        nodes = (await self.db.execute(nodes_stmt)).scalars().all()

        total_nodes = len(nodes)
        if total_nodes == 0:
            return PathProgressResponse(
                path_id=path_id,
                path_name=path.name,
                total_nodes=0,
                completed_nodes=0,
                in_progress_nodes=0,
                remaining_nodes=0,
                completion_percentage=0.0,
                total_estimated_minutes=0,
                completed_minutes=0,
                remaining_minutes=0,
                time_completion_percentage=0.0,
            )

        node_ids = [n.id for n in nodes]
        attempts_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.learner_id == learner_id,
            LearningActivityAttempt.learning_path_node_id.in_(node_ids),
        )
        attempts = (await self.db.execute(attempts_stmt)).scalars().all()
        attempts_by_node: dict[UUID, LearningActivityAttempt] = {
            a.learning_path_node_id: a for a in attempts
        }

        completed_nodes = 0
        in_progress_nodes = 0
        completed_minutes = 0
        total_estimated_minutes = sum(n.estimated_minutes or 0 for n in nodes)

        for n in nodes:
            att = attempts_by_node.get(n.id)
            if att and att.status == "completed":
                completed_nodes += 1
                completed_minutes += n.estimated_minutes or 0
            elif att and att.status == "started":
                in_progress_nodes += 1

        remaining_nodes = total_nodes - completed_nodes
        remaining_minutes = max(0, total_estimated_minutes - completed_minutes)

        completion_pct = round(completed_nodes / total_nodes, 4)
        time_completion_pct = (
            round(completed_minutes / total_estimated_minutes, 4)
            if total_estimated_minutes > 0
            else 0.0
        )

        return PathProgressResponse(
            path_id=path_id,
            path_name=path.name,
            total_nodes=total_nodes,
            completed_nodes=completed_nodes,
            in_progress_nodes=in_progress_nodes,
            remaining_nodes=remaining_nodes,
            completion_percentage=completion_pct,
            total_estimated_minutes=total_estimated_minutes,
            completed_minutes=completed_minutes,
            remaining_minutes=remaining_minutes,
            time_completion_percentage=time_completion_pct,
        )

    async def get_skill_history(
        self, learner_id: UUID, skill_id: UUID
    ) -> list[SkillHistoryItem]:
        """Fetch chronological mastery and evidence history for a specific skill."""
        skill = (
            await self.db.execute(select(Skill).where(Skill.id == skill_id))
        ).scalar_one_or_none()
        if not skill:
            raise ValueError(f"Skill {skill_id} not found.")

        history_items: list[SkillHistoryItem] = []

        # 1. Fetch MasteryOutcomes
        outcomes_stmt = (
            select(MasteryOutcome)
            .options(selectinload(MasteryOutcome.activity_attempt))
            .where(
                MasteryOutcome.learner_id == learner_id,
                MasteryOutcome.skill_id == skill_id,
            )
            .order_by(MasteryOutcome.created_at.asc())
        )
        outcomes = (await self.db.execute(outcomes_stmt)).scalars().all()

        for o in outcomes:
            evt_title = f"Post-Learning Assessment ({skill.name})"
            history_items.append(
                SkillHistoryItem(
                    timestamp=o.created_at,
                    event_type="mastery_check",
                    title=evt_title,
                    before_mastery=o.before_mastery,
                    after_mastery=o.after_mastery,
                    mastery_delta=o.mastery_delta,
                    confidence=o.after_confidence,
                    evidence_type="proof_of_mastery",
                    evidence_quality=o.evidence_quality,
                    proof_strength=o.proof_strength,
                )
            )

        # 2. If no outcomes, check baseline diagnostic / SkillMastery
        if not history_items:
            sm = (
                await self.db.execute(
                    select(SkillMastery).where(
                        SkillMastery.learner_id == learner_id,
                        SkillMastery.skill_id == skill_id,
                    )
                )
            ).scalar_one_or_none()
            if sm:
                history_items.append(
                    SkillHistoryItem(
                        timestamp=sm.updated_at or datetime.now(timezone.utc),
                        event_type="diagnostic",
                        title=f"Adaptive Diagnostic Evaluation ({skill.name})",
                        before_mastery=sm.mastery_score,
                        after_mastery=sm.mastery_score,
                        mastery_delta=0.0,
                        confidence=sm.confidence,
                        evidence_type="diagnostic_response",
                        evidence_quality=sm.confidence,
                        proof_strength=sm.confidence,
                    )
                )

        return sorted(history_items, key=lambda x: x.timestamp)

    # ----------------------------------------------------
    # Private Helper Methods
    # ----------------------------------------------------

    async def _get_nodes_progress(
        self, learner_id: UUID, path_id: UUID
    ) -> list[NodeProgressItem]:
        nodes_stmt = (
            select(LearningPathNode)
            .options(
                selectinload(LearningPathNode.resource),
                selectinload(LearningPathNode.skill),
            )
            .where(LearningPathNode.learning_path_id == path_id)
            .order_by(LearningPathNode.sequence)
        )
        nodes = (await self.db.execute(nodes_stmt)).scalars().all()

        node_ids = [n.id for n in nodes]
        attempts_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.learner_id == learner_id,
            LearningActivityAttempt.learning_path_node_id.in_(node_ids),
        )
        attempts = (await self.db.execute(attempts_stmt)).scalars().all()
        attempts_by_node = {a.learning_path_node_id: a for a in attempts}

        attempt_ids = [a.id for a in attempts]
        outcomes_by_attempt: dict[UUID, MasteryOutcome] = {}
        if attempt_ids:
            outcomes_stmt = select(MasteryOutcome).where(
                MasteryOutcome.learner_id == learner_id,
                MasteryOutcome.activity_attempt_id.in_(attempt_ids),
            )
            outcomes = (await self.db.execute(outcomes_stmt)).scalars().all()
            outcomes_by_attempt = {o.activity_attempt_id: o for o in outcomes}

        node_items: list[NodeProgressItem] = []
        for n in nodes:
            att = attempts_by_node.get(n.id)
            res_title = n.resource.title if n.resource else f"Activity #{n.sequence}"
            sk_id = n.skill_id
            sk_name = n.skill.name if n.skill else "General Skill"

            status = "pending"
            att_id = None
            comp_pct = 0.0
            time_spent = None
            proof_status = "unproven"
            b_mast = None
            a_mast = None
            m_delta = None

            if att:
                att_id = att.id
                status = att.status
                comp_pct = min(
                    1.0,
                    att.completion_percentage / 100.0
                    if att.completion_percentage > 1.0
                    else att.completion_percentage,
                )
                time_spent = att.time_spent_minutes

                out = outcomes_by_attempt.get(att.id)
                if out:
                    proof_status = "proven"
                    b_mast = out.before_mastery
                    a_mast = out.after_mastery
                    m_delta = out.mastery_delta
                elif status == "completed":
                    proof_status = "unproven"
                elif status == "started":
                    proof_status = "attempted"

            node_items.append(
                NodeProgressItem(
                    sequence=n.sequence,
                    path_node_id=n.id,
                    resource_id=n.resource_id,
                    resource_title=res_title,
                    target_skill_id=sk_id,
                    target_skill_name=sk_name,
                    estimated_minutes=n.estimated_minutes or 0,
                    status=status,
                    attempt_id=att_id,
                    completion_percentage=comp_pct,
                    time_spent_minutes=time_spent,
                    proof_status=proof_status,
                    before_mastery=b_mast,
                    after_mastery=a_mast,
                    mastery_delta=m_delta,
                )
            )

        return node_items

    async def _get_skills_progress(
        self, learner_id: UUID, goal: Goal
    ) -> tuple[list[SkillProgressItem], GoalSkillProgressResponse]:
        # Fetch RoleSkills for goal's target role
        role_skills_stmt = (
            select(RoleSkill)
            .options(selectinload(RoleSkill.skill))
            .where(RoleSkill.role_id == goal.target_role_id)
        )
        role_skills = (await self.db.execute(role_skills_stmt)).scalars().all()
        skill_ids = [rs.skill_id for rs in role_skills]

        # Fetch SkillMastery records
        sm_stmt = select(SkillMastery).where(
            SkillMastery.learner_id == learner_id,
            SkillMastery.skill_id.in_(skill_ids),
        )
        sm_records = (await self.db.execute(sm_stmt)).scalars().all()
        sm_by_skill = {sm.skill_id: sm for sm in sm_records}

        # Fetch evidence counts & last observed dates
        ev_stmt = (
            select(
                SkillEvidence.skill_id,
                func.count(SkillEvidence.id).label("cnt"),
                func.max(SkillEvidence.observed_at).label("last_at"),
            )
            .where(
                SkillEvidence.learner_id == learner_id,
                SkillEvidence.skill_id.in_(skill_ids),
            )
            .group_by(SkillEvidence.skill_id)
        )
        ev_rows = (await self.db.execute(ev_stmt)).all()
        ev_meta = {row[0]: (row[1], row[2]) for row in ev_rows}

        skill_items: list[SkillProgressItem] = []
        total_importance = 0.0
        weighted_progress_sum = 0.0

        at_required_cnt = 0
        near_required_cnt = 0
        low_conf_cnt = 0
        total_ev_cnt = 0

        for rs in role_skills:
            sk_id = rs.skill_id
            sk_name = rs.skill.name if rs.skill else "Skill"
            req_level = max(0.01, min(1.0, rs.required_level))
            importance = max(0.1, rs.importance)

            sm = sm_by_skill.get(sk_id)
            cur_mastery = sm.mastery_score if sm else 0.0
            cur_conf = sm.confidence if sm else 0.0

            # Initial mastery baseline
            initial_mastery = cur_mastery
            ev_count, last_at = ev_meta.get(sk_id, (0, None))
            total_ev_cnt += ev_count

            # Progress to required: min(1.0, current_mastery / required_level)
            prog_to_req = min(1.0, cur_mastery / req_level)

            if cur_mastery >= req_level:
                at_required_cnt += 1
            elif cur_mastery >= 0.8 * req_level:
                near_required_cnt += 1

            if cur_conf < 0.6:
                low_conf_cnt += 1

            weighted_progress_sum += prog_to_req * importance
            total_importance += importance

            skill_items.append(
                SkillProgressItem(
                    skill_id=sk_id,
                    skill_name=sk_name,
                    required_level=req_level,
                    role_importance=importance,
                    current_mastery=cur_mastery,
                    confidence=cur_conf,
                    initial_mastery=initial_mastery,
                    mastery_delta=round(cur_mastery - initial_mastery, 4),
                    progress_to_required=round(prog_to_req, 4),
                    evidence_count=ev_count,
                    last_evidence_at=last_at,
                )
            )

        goal_skill_progress = (
            round(weighted_progress_sum / total_importance, 4)
            if total_importance > 0
            else 0.0
        )

        role_stmt = select(Role).where(Role.id == goal.target_role_id)
        role = (await self.db.execute(role_stmt)).scalar_one_or_none()
        role_name = role.name if role else "Target Role"

        goal_response = GoalSkillProgressResponse(
            goal_id=goal.id,
            target_role_id=goal.target_role_id,
            target_role_name=role_name,
            total_target_skills=len(role_skills),
            skills_at_required=at_required_cnt,
            skills_near_required=near_required_cnt,
            skills_low_confidence=low_conf_cnt,
            goal_skill_progress=goal_skill_progress,
            path_completion_percentage=0.0,  # Updated in summary
            total_evidence_count=total_ev_cnt,
        )

        return skill_items, goal_response

    async def _get_recent_changes(
        self, learner_id: UUID
    ) -> list[RecentChangeItem]:
        outcomes_stmt = (
            select(MasteryOutcome)
            .options(selectinload(MasteryOutcome.skill))
            .where(MasteryOutcome.learner_id == learner_id)
            .order_by(MasteryOutcome.created_at.desc())
            .limit(5)
        )
        outcomes = (await self.db.execute(outcomes_stmt)).scalars().all()

        recent_items: list[RecentChangeItem] = []
        for o in outcomes:
            sk_name = o.skill.name if o.skill else "Target Skill"

            if o.evidence_quality < 0.4:
                cls = "insufficient_evidence"
                exp = f"Evidence quality was limited ({o.evidence_quality*100:.0f}%). Mastery unconfirmed."
            elif o.mastery_delta > 0.02:
                cls = "improving"
                exp = f"Estimated mastery increased by {o.mastery_delta*100:.0f} points based on new assessment evidence."
            elif o.mastery_delta < -0.02:
                cls = "regression"
                exp = f"Assessment score was lower than prior estimate. Mastery adjusted by {o.mastery_delta*100:.0f} points."
            else:
                cls = "stable"
                exp = "Assessment verified current mastery level with stable confidence."

            recent_items.append(
                RecentChangeItem(
                    skill_id=o.skill_id,
                    skill_name=sk_name,
                    before_mastery=o.before_mastery,
                    after_mastery=o.after_mastery,
                    mastery_delta=o.mastery_delta,
                    classification=cls,
                    explanation=exp,
                    evaluated_at=o.created_at,
                )
            )

        return recent_items

    async def _get_timeline_progress(
        self,
        learner_id: UUID,
        goal: Goal,
        path_progress: PathProgressResponse | None,
    ) -> TimelineProgressResponse:
        # Fetch profile constraints
        prof_stmt = select(LearnerProfile).where(LearnerProfile.learner_id == learner_id)
        profile = (await self.db.execute(prof_stmt)).scalar_one_or_none()

        t_weeks = goal.timeline_weeks or 12
        d_mins = (
            goal.daily_minutes
            or (
                int((profile.weekly_availability_hours * 60) / 7)
                if (profile and profile.weekly_availability_hours)
                else 60
            )
            or 60
        )

        total_avail = d_mins * 7 * t_weeks

        # Actual time spent from activity attempts
        att_stmt = select(
            func.sum(LearningActivityAttempt.time_spent_minutes)
        ).where(
            LearningActivityAttempt.learner_id == learner_id,
            LearningActivityAttempt.status == "completed",
        )
        actual_spent = (await self.db.execute(att_stmt)).scalar() or 0

        rem_mins = path_progress.remaining_minutes if path_progress else 0
        comp_mins = path_progress.completed_minutes if path_progress else 0

        # Descriptive pace: completed_minutes / max(1, actual_spent)
        descriptive_pace = (
            round(comp_mins / actual_spent, 2) if actual_spent > 0 else 1.0
        )

        pace_desc = (
            f"Observed pace: {comp_mins} estimated minutes completed across {actual_spent} actual minutes spent."
            if actual_spent > 0
            else "No completed activity time recorded yet."
        )

        return TimelineProgressResponse(
            timeline_weeks=t_weeks,
            daily_minutes=d_mins,
            total_available_minutes=total_avail,
            actual_time_spent_minutes=actual_spent,
            path_estimated_remaining_minutes=rem_mins,
            descriptive_pace=descriptive_pace,
            pace_description=pace_desc,
        )

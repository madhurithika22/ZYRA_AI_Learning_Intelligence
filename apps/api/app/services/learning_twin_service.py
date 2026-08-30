from datetime import datetime, timezone
from uuid import UUID

from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learning_path import LearningPath
from app.models.skill_evidence import SkillEvidence
from app.models.skill_mastery import SkillMastery
from app.schemas.learning_twin import (
    DecisionTrace,
    LearningTwinResponse,
    TwinBottleneckSummary,
    TwinConfidenceLevel,
    TwinEvidenceSummary,
    TwinFreshness,
    TwinFreshnessStatus,
    TwinGoalSummary,
    TwinNextActionSummary,
    TwinPathSummary,
    TwinRecentChangeItem,
    TwinReplanSummary,
    TwinSkillItem,
    TwinStateConfidence,
)
from app.services.bottleneck_analysis import BottleneckAnalysisService
from app.services.next_action_service import NextActionService
from app.services.progress_service import ProgressService
from app.services.replanning_service import ReplanningService
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class LearningTwinService:
    """Orchestration service composing the unified Learning Twin snapshot and decision trace.

    "The Learning Twin is a unified deterministic learner-state representation.
    It does not independently infer mastery, bottlenecks, or recommendations."
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.progress_service = ProgressService(db)
        self.bottleneck_service = BottleneckAnalysisService(db)
        self.next_action_service = NextActionService(db)
        self.replan_service = ReplanningService(db)

    async def get_learning_twin(
        self,
        learner_id: UUID,
        include_trace: bool = True,
    ) -> LearningTwinResponse:
        """Fetch the unified Learning Twin snapshot for a learner."""
        now = datetime.now(timezone.utc)

        # 1. Verify Learner exists
        learner_stmt = select(Learner).where(Learner.id == learner_id)
        learner = (await self.db.execute(learner_stmt)).scalar_one_or_none()
        if not learner:
            raise ValueError(f"Learner with ID {learner_id} not found.")

        display_name = learner.display_name or learner.email

        # 2. Get active goal
        goal_stmt = (
            select(Goal)
            .options(selectinload(Goal.target_role))
            .where(Goal.learner_id == learner_id)
            .order_by(Goal.created_at.desc())
        )
        goal = (await self.db.execute(goal_stmt)).scalars().first()

        # Handle No Active Goal Case
        if not goal:
            evidence_summary = await self._build_evidence_summary(learner_id)
            freshness = TwinFreshness(
                status=TwinFreshnessStatus.INCOMPLETE,
                generated_at=now,
            )
            state_confidence = TwinStateConfidence(
                level=TwinConfidenceLevel.LOW,
                score=0.20,
                reason="No active goal set for learner.",
                missing_dimensions=["goal", "target_role", "active_path", "bottleneck", "next_action"],
            )
            goal_summary = TwinGoalSummary(
                goal_id=None,
                objective="No Goal Set",
                target_role_id=None,
                target_role_name="Unassigned",
                goal_skill_progress=0.0,
                target_skill_count=0,
                skills_at_required=0,
                skills_near_target=0,
                skills_needing_work=0,
                skills_uncertain=0,
                evidence_count=evidence_summary.total_evidence_count,
            )

            return LearningTwinResponse(
                learner_id=learner_id,
                display_name=display_name,
                goal=goal_summary,
                path=None,
                skills=[],
                bottleneck=None,
                next_action=None,
                replan=None,
                recent_changes=[],
                evidence_summary=evidence_summary,
                state_confidence=state_confidence,
                state_completeness=0.20,
                freshness=freshness,
                decision_trace=None,
            )

        # 3. Invoke Authoritative Services for Goal State
        progress_summary = await self.progress_service.get_learner_progress_summary(learner_id)
        evidence_summary = await self._build_evidence_summary(learner_id)

        try:
            b_analysis = await self.bottleneck_service.analyze_bottlenecks(learner_id, goal.id)
        except Exception:
            b_analysis = None

        try:
            next_action_resp = await self.next_action_service.get_next_action(learner_id, goal.id)
        except Exception:
            next_action_resp = None

        try:
            replan_resp = await self.replan_service.get_replan_status(learner_id, goal.id)
        except Exception:
            replan_resp = None

        # 4. Map Goal Summary from ProgressService
        role_name = goal.target_role.name if goal.target_role else progress_summary.target_role_name

        skills_at_req = sum(1 for sk in progress_summary.skills_progress if sk.current_mastery >= sk.required_level and sk.confidence >= 0.80)
        skills_near = sum(1 for sk in progress_summary.skills_progress if (sk.required_level * 0.70) <= sk.current_mastery < sk.required_level)
        skills_needs_work = sum(1 for sk in progress_summary.skills_progress if sk.current_mastery < (sk.required_level * 0.70))
        skills_uncert = sum(1 for sk in progress_summary.skills_progress if sk.confidence < 0.60)

        goal_summary = TwinGoalSummary(
            goal_id=goal.id,
            objective=goal.objective,
            target_role_id=goal.target_role_id,
            target_role_name=role_name,
            goal_skill_progress=progress_summary.goal_skill_progress,
            target_skill_count=len(progress_summary.skills_progress),
            skills_at_required=skills_at_req,
            skills_near_target=skills_near,
            skills_needing_work=skills_needs_work,
            skills_uncertain=skills_uncert,
            evidence_count=evidence_summary.total_evidence_count,
        )

        # 5. Map Skills Matrix from ProgressService
        twin_skills: list[TwinSkillItem] = []
        for sk in progress_summary.skills_progress:
            if sk.current_mastery >= sk.required_level and sk.confidence >= 0.80:
                status_label = "STRONG"
            elif sk.current_mastery >= (sk.required_level * 0.70):
                status_label = "ON_TRACK"
            elif sk.confidence < 0.60:
                status_label = "UNCERTAIN"
            else:
                status_label = "GAP"

            sk_gap = max(0.0, round(sk.required_level - sk.current_mastery, 4))
            twin_skills.append(
                TwinSkillItem(
                    skill_id=sk.skill_id,
                    skill_name=sk.skill_name,
                    mastery=sk.current_mastery,
                    confidence=sk.confidence,
                    required=sk.required_level,
                    gap=sk_gap,
                    progress_to_required=sk.progress_to_required,
                    evidence_count=sk.evidence_count,
                    status=status_label,
                )
            )

        # 6. Map Path Summary from ProgressService & ReplanningService
        p_prog = progress_summary.path_progress
        twin_path: TwinPathSummary | None = None
        if p_prog:
            # Query version from LearningPath model
            path_obj = (await self.db.execute(select(LearningPath).where(LearningPath.id == p_prog.path_id))).scalar_one_or_none()
            version_val = path_obj.version if path_obj else 1

            should_r = replan_resp.should_replan if replan_resp else False
            twin_path = TwinPathSummary(
                path_id=p_prog.path_id,
                version=version_val,
                name=p_prog.path_name,
                status="active",
                completion_percentage=p_prog.completion_percentage,
                completed_nodes=p_prog.completed_nodes,
                total_nodes=p_prog.total_nodes,
                remaining_minutes=p_prog.remaining_minutes,
                is_stale=should_r,
                replan_available=should_r,
            )

        # 7. Map Bottleneck from BottleneckAnalysisService
        primary_b = b_analysis.primary_bottleneck if b_analysis else None
        twin_bottleneck: TwinBottleneckSummary | None = None
        if primary_b:
            twin_bottleneck = TwinBottleneckSummary(
                skill_id=primary_b.skill_id,
                skill_name=primary_b.skill_name,
                mastery_score=primary_b.mastery,
                required_level=primary_b.required_level,
                gap=primary_b.gap,
                confidence=primary_b.confidence,
                dependency_impact=primary_b.dependency_impact,
                bottleneck_score=primary_b.bottleneck_score,
                reason=primary_b.explanation.primary_reason,
                affected_skills=primary_b.explanation.downstream_skills,
            )

        # 8. Map Next Action from NextActionService
        rec_action = next_action_resp.selected_action if next_action_resp else None
        twin_next_action: TwinNextActionSummary | None = None
        if rec_action and next_action_resp:
            action_type_str = rec_action.action_type.value if hasattr(rec_action.action_type, "value") else str(rec_action.action_type)
            twin_next_action = TwinNextActionSummary(
                action_type=action_type_str,
                title=rec_action.title,
                target_skill_id=rec_action.target_skill_id,
                target_skill_name=rec_action.target_skill_name,
                resource_id=rec_action.resource_id,
                node_id=rec_action.path_node_id,
                estimated_minutes=rec_action.estimated_minutes,
                action_confidence=next_action_resp.action_confidence,
                score=rec_action.score,
                primary_reason=rec_action.primary_reason,
                reasons=rec_action.supporting_reasons,
            )

        # 9. Map Replan Summary from ReplanningService
        twin_replan: TwinReplanSummary | None = None
        if replan_resp:
            replan_decision = replan_resp.decision
            trigger_str = replan_decision.trigger_type.value if replan_decision.trigger_type else None
            twin_replan = TwinReplanSummary(
                should_replan=replan_resp.should_replan,
                staleness_score=replan_resp.staleness_score,
                trigger_type=trigger_str,
                rationale=replan_decision.rationale,
                draft_path_id=replan_decision.draft_path_id,
            )

        # 10. Map Recent Changes from ProgressService
        recent_changes = [
            TwinRecentChangeItem(
                id=str(item.skill_id),
                title=f"{item.skill_name} Mastery Change",
                change_type=item.classification,
                description=item.explanation,
                timestamp=item.evaluated_at,
                impact_delta=f"{item.mastery_delta:+.0%}",
            )
            for item in progress_summary.recent_changes
        ]

        # 11. Evaluate State Completeness & Multi-Layer Confidence
        observed_dims = 0
        total_dims = 7
        missing_dims: list[str] = []

        if goal:
            observed_dims += 1
        else:
            missing_dims.append("goal")

        if goal and goal.target_role_id:
            observed_dims += 1
        else:
            missing_dims.append("target_role")

        if twin_skills:
            observed_dims += 1
        else:
            missing_dims.append("skills")

        if evidence_summary.total_evidence_count > 0:
            observed_dims += 1
        else:
            missing_dims.append("evidence")

        if twin_path:
            observed_dims += 1
        else:
            missing_dims.append("active_path")

        if twin_bottleneck:
            observed_dims += 1
        else:
            missing_dims.append("bottleneck")

        if twin_next_action:
            observed_dims += 1
        else:
            missing_dims.append("next_action")

        completeness_score = round(observed_dims / total_dims, 2)

        if completeness_score >= 0.85:
            conf_level = TwinConfidenceLevel.HIGH
            conf_reason = "Complete learner computational state assembled from all authoritative engines."
        elif completeness_score >= 0.50:
            conf_level = TwinConfidenceLevel.MEDIUM
            conf_reason = "Sufficient learner state assembled with minor missing evidence or path coverage."
        else:
            conf_level = TwinConfidenceLevel.LOW
            conf_reason = "Partial learner state due to missing goal, path, or mastery evidence."

        state_confidence = TwinStateConfidence(
            level=conf_level,
            score=completeness_score,
            reason=conf_reason,
            missing_dimensions=missing_dims,
        )

        # 12. Evaluate Freshness
        latest_mastery_dt = evidence_summary.last_assessed_at
        freshness_status = TwinFreshnessStatus.FRESH if (not replan_resp or not replan_resp.should_replan) else TwinFreshnessStatus.STALE
        freshness = TwinFreshness(
            status=freshness_status,
            generated_at=now,
            latest_mastery_update_at=latest_mastery_dt,
            latest_path_change_at=now if p_prog else None,
        )

        # 13. Construct Decision Trace
        decision_trace: DecisionTrace | None = None
        if include_trace:
            decision_trace = DecisionTrace(
                generated_at=now,
                learner_state_summary={
                    "learner_id": str(learner_id),
                    "goal_id": str(goal.id),
                    "objective": goal.objective,
                    "target_role": role_name,
                    "goal_skill_progress": f"{progress_summary.goal_skill_progress:.1%}",
                },
                skill_state_trace=[
                    {
                        "skill": sk.skill_name,
                        "mastery": f"{sk.mastery:.0%}",
                        "required": f"{sk.required:.0%}",
                        "confidence": f"{sk.confidence:.0%}",
                        "gap": f"{sk.gap:.0%}",
                        "status": sk.status,
                    }
                    for sk in twin_skills
                ],
                bottleneck_trace={
                    "primary_bottleneck": twin_bottleneck.skill_name if twin_bottleneck else None,
                    "bottleneck_score": twin_bottleneck.bottleneck_score if twin_bottleneck else 0.0,
                    "dependency_impact": twin_bottleneck.dependency_impact if twin_bottleneck else 0.0,
                    "reason": twin_bottleneck.reason if twin_bottleneck else "No bottleneck identified.",
                },
                next_action_trace={
                    "action_type": twin_next_action.action_type if twin_next_action else None,
                    "title": twin_next_action.title if twin_next_action else None,
                    "target_skill": twin_next_action.target_skill_name if twin_next_action else None,
                    "score": twin_next_action.score if twin_next_action else 0.0,
                    "action_confidence": f"{(twin_next_action.action_confidence if twin_next_action else 0.0):.0%}",
                    "primary_reason": twin_next_action.primary_reason if twin_next_action else None,
                },
                path_state_trace={
                    "path_id": str(twin_path.path_id) if twin_path else None,
                    "version": twin_path.version if twin_path else 1,
                    "completion_percentage": f"{(twin_path.completion_percentage if twin_path else 0.0):.0%}",
                    "remaining_minutes": twin_path.remaining_minutes if twin_path else 0,
                    "is_stale": twin_path.is_stale if twin_path else False,
                },
                replan_trace={
                    "should_replan": twin_replan.should_replan if twin_replan else False,
                    "staleness_score": twin_replan.staleness_score if twin_replan else 0.0,
                    "trigger_type": twin_replan.trigger_type if twin_replan else None,
                    "rationale": twin_replan.rationale if twin_replan else "No replanning evaluation recorded.",
                },
            )

        return LearningTwinResponse(
            learner_id=learner_id,
            display_name=display_name,
            goal=goal_summary,
            path=twin_path,
            skills=twin_skills,
            bottleneck=twin_bottleneck,
            next_action=twin_next_action,
            replan=twin_replan,
            recent_changes=recent_changes,
            evidence_summary=evidence_summary,
            state_confidence=state_confidence,
            state_completeness=completeness_score,
            freshness=freshness,
            decision_trace=decision_trace,
        )

    async def _build_evidence_summary(self, learner_id: UUID) -> TwinEvidenceSummary:
        """Helper querying SkillEvidence and MasteryOutcome for evidence summary."""
        ev_stmt = select(func.count(SkillEvidence.id)).where(SkillEvidence.learner_id == learner_id)
        total_ev = (await self.db.execute(ev_stmt)).scalar() or 0

        latest_ev_stmt = (
            select(SkillEvidence)
            .options(selectinload(SkillEvidence.skill))
            .where(SkillEvidence.learner_id == learner_id)
            .order_by(SkillEvidence.created_at.desc())
            .limit(5)
        )
        recent_evs = list((await self.db.execute(latest_ev_stmt)).scalars().all())
        last_assessed = recent_evs[0].created_at if recent_evs else None

        recently_verified_names = list(
            dict.fromkeys([ev.skill.name for ev in recent_evs if ev.skill])
        )

        sm_stmt = select(SkillMastery).where(SkillMastery.learner_id == learner_id)
        sms = list((await self.db.execute(sm_stmt)).scalars().all())

        demonstrated = sum(1 for sm in sms if sm.mastery_score >= 0.80 and sm.confidence >= 0.80)
        improving = sum(1 for sm in sms if 0.40 <= sm.mastery_score < 0.80)
        insufficient = sum(1 for sm in sms if sm.confidence < 0.60 or sm.mastery_score < 0.40)

        return TwinEvidenceSummary(
            total_evidence_count=total_ev,
            recent_evidence_count=len(recent_evs),
            last_assessed_at=last_assessed,
            demonstrated_skills_count=demonstrated,
            improving_skills_count=improving,
            insufficient_evidence_count=insufficient,
            recently_verified_skills=recently_verified_names,
        )

from uuid import UUID

from app.models.goal import Goal
from app.models.learning_activity_attempt import LearningActivityAttempt
from app.models.learning_path import LearningPath
from app.models.learning_path_node import LearningPathNode
from app.models.role_skill import RoleSkill
from app.models.skill_mastery import SkillMastery
from app.schemas.replanning import ReplanDecision, ReplanTriggerType
from app.services.bottleneck_analysis import BottleneckAnalysisService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ChangeDetectionService:
    """Deterministic service evaluating learner-state changes and path staleness."""

    # Material Change Thresholds
    MASTERY_DELTA_THRESHOLD = 0.10
    CONFIDENCE_DELTA_THRESHOLD = 0.15
    STALENESS_REPLAN_THRESHOLD = 0.35

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.b_service = BottleneckAnalysisService(db)

    async def detect_changes_and_evaluate(
        self,
        learner_id: UUID,
        goal_id: UUID,
        active_path: LearningPath,
    ) -> ReplanDecision:
        """Evaluate learner-state changes against active path to determine if replanning is needed."""
        # 1. Fetch current bottleneck analysis
        b_analysis = await self.b_service.analyze_bottlenecks(learner_id, goal_id)
        current_primary_b = b_analysis.primary_bottleneck
        primary_sk_name = current_primary_b.skill_name if current_primary_b else None
        primary_sk_id = current_primary_b.skill_id if current_primary_b else None

        # 2. Fetch active path nodes and completed attempts
        nodes_stmt = (
            select(LearningPathNode)
            .options(
                selectinload(LearningPathNode.resource),
                selectinload(LearningPathNode.skill),
            )
            .where(LearningPathNode.learning_path_id == active_path.id)
            .order_by(LearningPathNode.sequence)
        )
        nodes = list((await self.db.execute(nodes_stmt)).scalars().all())

        node_ids = [n.id for n in nodes]
        attempts_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.learner_id == learner_id,
            LearningActivityAttempt.learning_path_node_id.in_(node_ids),
        )
        attempts = list((await self.db.execute(attempts_stmt)).scalars().all())
        completed_node_ids = {
            att.learning_path_node_id for att in attempts if att.status in ("completed", "proven")
        }

        # 3. Batch-load SkillMastery & RoleSkill for path skills
        goal_stmt = select(Goal).where(Goal.id == goal_id)
        goal = (await self.db.execute(goal_stmt)).scalar_one()

        rs_stmt = select(RoleSkill).where(RoleSkill.role_id == goal.target_role_id)
        role_skills = list((await self.db.execute(rs_stmt)).scalars().all())
        rs_map = {rs.skill_id: rs for rs in role_skills}

        all_sk_ids = list(set([rs.skill_id for rs in role_skills] + [n.skill_id for n in nodes if n.skill_id]))
        sm_stmt = select(SkillMastery).where(
            SkillMastery.learner_id == learner_id,
            SkillMastery.skill_id.in_(all_sk_ids),
        )
        sm_records = list((await self.db.execute(sm_stmt)).scalars().all())
        sm_map = {sm.skill_id: sm for sm in sm_records}

        # 4. Check Replanning Triggers
        trigger_type: ReplanTriggerType | None = None
        trigger_skill_id: UUID | None = None
        trigger_skill_name: str | None = None
        rationale_parts: list[str] = []
        staleness_score = 0.0

        # Check A: Future path node obsolete (learner already mastered node skill)
        obsolete_nodes: list[LearningPathNode] = []
        for n in nodes:
            if n.id not in completed_node_ids and n.skill_id:
                sm = sm_map.get(n.skill_id)
                rs = rs_map.get(n.skill_id)
                raw_req = rs.required_level if rs else 0.80
                req = (raw_req / 5.0) if raw_req > 1.0 else raw_req
                if sm and sm.mastery_score >= req and sm.confidence >= 0.80:
                    obsolete_nodes.append(n)

        if obsolete_nodes:
            first_obs = obsolete_nodes[0]
            trigger_type = ReplanTriggerType.PATH_NODE_OBSOLETE
            trigger_skill_id = first_obs.skill_id
            trigger_skill_name = first_obs.skill.name if first_obs.skill else "Skill"
            staleness_score += 0.40
            obs_mastery = sm_map[first_obs.skill_id].mastery_score if first_obs.skill_id and first_obs.skill_id in sm_map else 0.80
            rationale_parts.append(
                f"Future activity '{first_obs.resource.title if first_obs.resource else 'Resource'}' is obsolete because {trigger_skill_name} mastery ({obs_mastery:.0%}) meets target requirement."
            )

        # Check B: Bottleneck Resolved or Shifted
        prev_reason = active_path.generation_reason or ""
        if current_primary_b and not trigger_type:
            if primary_sk_id and sm_map.get(primary_sk_id):
                sm_p = sm_map[primary_sk_id]
                rs_p = rs_map.get(primary_sk_id)
                raw_req_p = rs_p.required_level if rs_p else 0.80
                req_p = (raw_req_p / 5.0) if raw_req_p > 1.0 else raw_req_p
                if sm_p.mastery_score >= req_p:
                    trigger_type = ReplanTriggerType.BOTTLENECK_RESOLVED
                    trigger_skill_id = primary_sk_id
                    trigger_skill_name = primary_sk_name
                    staleness_score += 0.50
                    rationale_parts.append(
                        f"Primary bottleneck skill '{primary_sk_name}' has reached required mastery level ({sm_p.mastery_score:.0%})."
                    )

            if not trigger_type and prev_reason and primary_sk_name and primary_sk_name.lower() not in prev_reason.lower():
                trigger_type = ReplanTriggerType.BOTTLENECK_SHIFTED
                trigger_skill_id = primary_sk_id
                trigger_skill_name = primary_sk_name
                staleness_score += 0.40
                rationale_parts.append(
                    f"Structural bottleneck shifted to '{primary_sk_name}'."
                )

        # Check C: Material Skill Gap Changed
        max_mastery_delta = 0.0
        for sm in sm_records:
            delta = sm.mastery_score - 0.20
            if delta > max_mastery_delta:
                max_mastery_delta = delta

        if not trigger_type and max_mastery_delta >= 0.40:
            trigger_type = ReplanTriggerType.SKILL_GAP_CHANGED
            staleness_score += 0.30
            rationale_parts.append(
                "Significant mastery progression observed across target role skills."
            )

        # Calculate final staleness & decision
        staleness_score = min(1.0, round(staleness_score, 4))
        should_replan = (staleness_score >= self.STALENESS_REPLAN_THRESHOLD) or (trigger_type is not None)

        if not should_replan:
            rationale = "Current learning path remains structurally valid and optimal for current learner state."
            confidence = 0.90
        else:
            rationale = " • ".join(rationale_parts) if rationale_parts else "Learner state change warrants path replanning."
            confidence = 0.85

        return ReplanDecision(
            should_replan=should_replan,
            staleness_score=staleness_score,
            trigger_type=trigger_type,
            trigger_skill_id=trigger_skill_id,
            trigger_skill_name=trigger_skill_name,
            rationale=rationale,
            confidence=confidence,
            current_path_version=active_path.version,
        )

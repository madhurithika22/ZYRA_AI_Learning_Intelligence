from typing import Any
from uuid import UUID

from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learner_profile import LearnerProfile
from app.models.learning_activity_attempt import LearningActivityAttempt
from app.models.learning_path import LearningPath
from app.models.learning_path_node import LearningPathNode
from app.models.mastery_outcome import MasteryOutcome
from app.models.role_skill import RoleSkill
from app.models.skill import Skill
from app.models.skill_mastery import SkillMastery
from app.models.skill_relation import SkillRelation
from app.schemas.next_action import (
    ActionMetrics,
    ActionType,
    NextActionCandidatesResponse,
    NextActionItem,
    NextActionResponse,
)
from app.services.bottleneck_analysis import BottleneckAnalysisService
from app.services.dependency_impact import DependencyImpactService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class NextActionService:
    """Deterministic Next-Best-Action Engine evaluating current learner state."""

    # Explicit named scoring weights
    WEIGHT_GAP = 0.25
    WEIGHT_BOTTLENECK = 0.25
    WEIGHT_UNCERTAINTY = 0.15
    WEIGHT_PREREQUISITE = 0.15
    WEIGHT_PROGRESS = 0.10
    WEIGHT_EVIDENCE = 0.10
    WEIGHT_PRACTICAL = 0.05
    WEIGHT_TIME = 0.10
    WEIGHT_REDUNDANCY = 0.15
    WEIGHT_REPEAT = 0.20

    # Action type priority for deterministic tie-breaking
    ACTION_PRIORITY = {
        ActionType.CONTINUE: 1,
        ActionType.MASTERY_CHECK: 2,
        ActionType.SKIP: 3,
        ActionType.PREREQUISITE_REVIEW: 4,
        ActionType.LEARN: 5,
        ActionType.PROJECT: 6,
        ActionType.REASSESS: 7,
    }

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.bottleneck_service = BottleneckAnalysisService(db)
        self.dependency_service = DependencyImpactService(db)

    async def get_next_action(
        self, learner_id: UUID, goal_id: UUID | None = None
    ) -> NextActionResponse:
        """Evaluate current state and return the top selected next action with alternatives."""
        candidates_resp = await self.get_action_candidates(learner_id, goal_id)
        candidates = candidates_resp.candidates

        if not candidates:
            raise ValueError(f"No valid candidate actions found for learner {learner_id}.")

        selected_action = candidates[0]
        alternatives = candidates[1:3]

        # Calculate Action Confidence based on score gap to rank 2 candidate
        score_gap = 0.0
        if len(candidates) > 1:
            score_gap = max(0.0, selected_action.score - candidates[1].score)

        raw_conf = min(0.99, max(0.40, 0.50 + (score_gap * 1.5)))
        action_confidence = round(raw_conf, 4)

        if action_confidence >= 0.80:
            conf_label = "HIGH"
        elif action_confidence >= 0.60:
            conf_label = "MEDIUM"
        else:
            conf_label = "LOW"

        return NextActionResponse(
            learner_id=learner_id,
            goal_id=goal_id or candidates_resp.goal_id,
            selected_action=selected_action,
            action_confidence=action_confidence,
            confidence_label=conf_label,
            alternatives=alternatives,
        )

    async def get_action_candidates(
        self, learner_id: UUID, goal_id: UUID | None = None
    ) -> NextActionCandidatesResponse:
        """Batch-load state and generate ranked feasible candidate actions."""
        # 1. Verify Learner exists
        learner = (
            await self.db.execute(select(Learner).where(Learner.id == learner_id))
        ).scalar_one_or_none()
        if not learner:
            raise ValueError(f"Learner with ID {learner_id} not found.")

        # 2. Get active Goal
        if goal_id:
            goal = (
                await self.db.execute(
                    select(Goal).where(Goal.id == goal_id, Goal.learner_id == learner_id)
                )
            ).scalar_one_or_none()
        else:
            goal = (
                await self.db.execute(
                    select(Goal)
                    .where(Goal.learner_id == learner_id)
                    .order_by(Goal.created_at.desc())
                )
            ).scalars().first()

        if not goal:
            raise ValueError(f"No active goal found for learner {learner_id}.")

        # 3. Batch-load Learner Profile, Target Role Skills & Skill Mastery
        prof_stmt = select(LearnerProfile).where(LearnerProfile.learner_id == learner_id)
        profile = (await self.db.execute(prof_stmt)).scalar_one_or_none()
        daily_minutes = goal.daily_minutes or (
            int((profile.weekly_availability_hours * 60) / 7)
            if profile and profile.weekly_availability_hours
            else 60
        ) or 60

        role_skills_stmt = (
            select(RoleSkill)
            .options(selectinload(RoleSkill.skill))
            .where(RoleSkill.role_id == goal.target_role_id)
        )
        role_skills = (await self.db.execute(role_skills_stmt)).scalars().all()
        skill_ids = [rs.skill_id for rs in role_skills]
        role_skill_map = {rs.skill_id: rs for rs in role_skills}

        # 4. Batch-load Active Path & Nodes
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

        nodes: list[LearningPathNode] = []
        if active_path:
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

        all_skill_ids = list(
            set(skill_ids + [n.skill_id for n in nodes if n.skill_id])
        )
        sm_stmt = select(SkillMastery).where(
            SkillMastery.learner_id == learner_id,
            SkillMastery.skill_id.in_(all_skill_ids),
        )
        sm_records = (await self.db.execute(sm_stmt)).scalars().all()
        sm_map = {sm.skill_id: sm for sm in sm_records}

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

        # 5. Fetch Phase 5 Bottleneck Analysis
        b_analysis = await self.bottleneck_service.analyze_bottlenecks(learner_id, goal.id)
        primary_bottleneck_sk_id = (
            b_analysis.primary_bottleneck.skill_id if b_analysis.primary_bottleneck else None
        )
        secondary_bottleneck_sk_ids = [
            bg.skill_id for bg in b_analysis.secondary_bottlenecks
        ]

        # 6. Generate Candidate Actions
        candidates: list[NextActionItem] = []

        # A. Path Node Candidates
        for node in nodes:
            rs_info = role_skill_map.get(node.skill_id) if node.skill_id else None
            req_level = rs_info.required_level if rs_info else 0.8
            sm_info = sm_map.get(node.skill_id) if node.skill_id else None
            cur_mastery = sm_info.mastery_score if sm_info else 0.2
            cur_conf = sm_info.confidence if sm_info else 0.5

            att = attempts_by_node.get(node.id)
            status = att.status if att else "pending"
            out = outcomes_by_attempt.get(att.id) if att else None

            sk_name = node.skill.name if node.skill else "Target Skill"
            res_title = (
                node.resource.title if node.resource else f"Activity #{node.sequence}"
            )
            est_mins = node.estimated_minutes or 30

            # Candidate logic
            if status == "started":
                # In-progress activity -> CONTINUE
                cand = self._build_candidate(
                    action_type=ActionType.CONTINUE,
                    title=f"Continue: {res_title}",
                    target_skill_id=node.skill_id,
                    target_skill_name=sk_name,
                    resource_id=node.resource_id,
                    path_node_id=node.id,
                    attempt_id=att.id if att else None,
                    estimated_minutes=est_mins,
                    req_level=req_level,
                    cur_mastery=cur_mastery,
                    cur_conf=cur_conf,
                    primary_bottleneck_sk_id=primary_bottleneck_sk_id,
                    secondary_bottleneck_sk_ids=secondary_bottleneck_sk_ids,
                    daily_minutes=daily_minutes,
                    node_sequence=node.sequence,
                    total_nodes=len(nodes),
                )
                candidates.append(cand)

            elif status == "completed" and not out:
                # Activity completed but unproven -> MASTERY_CHECK
                cand = self._build_candidate(
                    action_type=ActionType.MASTERY_CHECK,
                    title=f"Prove Mastery: {sk_name}",
                    target_skill_id=node.skill_id,
                    target_skill_name=sk_name,
                    resource_id=node.resource_id,
                    path_node_id=node.id,
                    attempt_id=att.id if att else None,
                    estimated_minutes=15,
                    req_level=req_level,
                    cur_mastery=cur_mastery,
                    cur_conf=cur_conf,
                    primary_bottleneck_sk_id=primary_bottleneck_sk_id,
                    secondary_bottleneck_sk_ids=secondary_bottleneck_sk_ids,
                    daily_minutes=daily_minutes,
                    node_sequence=node.sequence,
                    total_nodes=len(nodes),
                )
                candidates.append(cand)

            elif cur_mastery >= req_level and cur_conf >= 0.8:
                # Skill already mastered -> SKIP
                cand = self._build_candidate(
                    action_type=ActionType.SKIP,
                    title=f"Skip Activity: {res_title}",
                    target_skill_id=node.skill_id,
                    target_skill_name=sk_name,
                    resource_id=node.resource_id,
                    path_node_id=node.id,
                    estimated_minutes=0,
                    req_level=req_level,
                    cur_mastery=cur_mastery,
                    cur_conf=cur_conf,
                    primary_bottleneck_sk_id=primary_bottleneck_sk_id,
                    secondary_bottleneck_sk_ids=secondary_bottleneck_sk_ids,
                    daily_minutes=daily_minutes,
                    node_sequence=node.sequence,
                    total_nodes=len(nodes),
                )
                candidates.append(cand)

            else:
                # Standard learning node -> LEARN or PROJECT
                is_proj = (
                    node.resource and node.resource.resource_type in ("project", "lab")
                )
                act_type = ActionType.PROJECT if is_proj else ActionType.LEARN
                act_title = (
                    f"Applied Project: {res_title}"
                    if is_proj
                    else f"Learn: {res_title}"
                )

                cand = self._build_candidate(
                    action_type=act_type,
                    title=act_title,
                    target_skill_id=node.skill_id,
                    target_skill_name=sk_name,
                    resource_id=node.resource_id,
                    path_node_id=node.id,
                    estimated_minutes=est_mins,
                    req_level=req_level,
                    cur_mastery=cur_mastery,
                    cur_conf=cur_conf,
                    primary_bottleneck_sk_id=primary_bottleneck_sk_id,
                    secondary_bottleneck_sk_ids=secondary_bottleneck_sk_ids,
                    daily_minutes=daily_minutes,
                    node_sequence=node.sequence,
                    total_nodes=len(nodes),
                )
                candidates.append(cand)

        # B. Check for High Uncertainty Skills -> REASSESS
        for sk_id, sm in sm_map.items():
            rs_info = role_skill_map.get(sk_id)
            req_l = rs_info.required_level if rs_info else 0.8
            if sm.confidence < 0.50 and (req_l - sm.mastery_score) > 0.20:
                sk_obj = (
                    await self.db.execute(select(Skill).where(Skill.id == sk_id))
                ).scalar_one_or_none()
                sk_name = sk_obj.name if sk_obj else "Target Skill"

                # Check if REASSESS already added
                if not any(
                    c.action_type == ActionType.REASSESS and c.target_skill_id == sk_id
                    for c in candidates
                ):
                    cand = self._build_candidate(
                        action_type=ActionType.REASSESS,
                        title=f"Targeted Assessment: {sk_name}",
                        target_skill_id=sk_id,
                        target_skill_name=sk_name,
                        estimated_minutes=15,
                        req_level=req_l,
                        cur_mastery=sm.mastery_score,
                        cur_conf=sm.confidence,
                        primary_bottleneck_sk_id=primary_bottleneck_sk_id,
                        secondary_bottleneck_sk_ids=secondary_bottleneck_sk_ids,
                        daily_minutes=daily_minutes,
                        node_sequence=1,
                        total_nodes=len(nodes) or 1,
                    )
                    candidates.append(cand)

        # C. Check for Unmet Prerequisites of Primary Bottleneck -> PREREQUISITE_REVIEW
        if primary_bottleneck_sk_id:
            pb_rel_stmt = (
                select(SkillRelation)
                .options(selectinload(SkillRelation.source_skill))
                .where(
                    SkillRelation.target_skill_id == primary_bottleneck_sk_id,
                    SkillRelation.relation_type == "prerequisite",
                )
            )
            pb_rels = (await self.db.execute(pb_rel_stmt)).scalars().all()

            for rel in pb_rels:
                pr = rel.source_skill
                if pr:
                    pr_sm = sm_map.get(pr.id)
                    pr_mastery = pr_sm.mastery_score if pr_sm else 0.2
                    if pr_mastery < 0.70:
                        if not any(c.target_skill_id == pr.id for c in candidates):
                            cand = self._build_candidate(
                                action_type=ActionType.PREREQUISITE_REVIEW,
                                title=f"Prerequisite Review: {pr.name}",
                                target_skill_id=pr.id,
                                target_skill_name=pr.name,
                                estimated_minutes=45,
                                req_level=0.80,
                                cur_mastery=pr_mastery,
                                cur_conf=pr_sm.confidence if pr_sm else 0.5,
                                primary_bottleneck_sk_id=primary_bottleneck_sk_id,
                                secondary_bottleneck_sk_ids=secondary_bottleneck_sk_ids,
                                daily_minutes=daily_minutes,
                                node_sequence=1,
                                total_nodes=len(nodes) or 1,
                                is_prereq_of_bottleneck=True,
                            )
                            candidates.append(cand)

        # 7. Sort & Rank Candidates with Deterministic Tie-Breakers
        sorted_candidates = self._rank_candidates(candidates)

        return NextActionCandidatesResponse(
            learner_id=learner_id,
            goal_id=goal.id,
            candidates=sorted_candidates,
        )

    # ----------------------------------------------------
    # Private Helper Methods
    # ----------------------------------------------------

    def _build_candidate(
        self,
        action_type: ActionType,
        title: str,
        target_skill_id: UUID | None,
        target_skill_name: str,
        resource_id: UUID | None = None,
        path_node_id: UUID | None = None,
        attempt_id: UUID | None = None,
        estimated_minutes: int = 30,
        req_level: float = 0.8,
        cur_mastery: float = 0.2,
        cur_conf: float = 0.5,
        primary_bottleneck_sk_id: UUID | None = None,
        secondary_bottleneck_sk_ids: list[UUID] | None = None,
        daily_minutes: int = 60,
        node_sequence: int = 1,
        total_nodes: int = 1,
        is_prereq_of_bottleneck: bool = False,
    ) -> NextActionItem:
        # Calculate normalized metrics
        gap = max(0.0, req_level - cur_mastery)
        gap_reduction = min(1.0, gap / req_level) if req_level > 0 else 0.0

        if target_skill_id == primary_bottleneck_sk_id:
            bottleneck_relevance = 1.0
        elif secondary_bottleneck_sk_ids and target_skill_id in secondary_bottleneck_sk_ids:
            bottleneck_relevance = 0.70
        elif is_prereq_of_bottleneck:
            bottleneck_relevance = 0.85
        else:
            bottleneck_relevance = 0.10

        if action_type in (ActionType.REASSESS, ActionType.MASTERY_CHECK):
            information_value = max(0.0, min(1.0, 1.0 - cur_conf))
        else:
            information_value = 0.30

        prerequisite_value = 0.90 if is_prereq_of_bottleneck else 0.20
        path_progress_value = (
            max(0.1, round((total_nodes - node_sequence + 1) / total_nodes, 4))
            if total_nodes > 0
            else 0.5
        )

        if action_type == ActionType.MASTERY_CHECK:
            evidence_value = 1.0
            gap_reduction = max(gap_reduction, 0.85)
            bottleneck_relevance = max(bottleneck_relevance, 0.80)
            path_progress_value = 1.0
            information_value = max(information_value, 0.80)
        elif action_type == ActionType.SKIP:
            evidence_value = 0.90
            path_progress_value = 0.80
            information_value = 0.50
        elif action_type == ActionType.REASSESS:
            evidence_value = 0.80
        elif action_type in (ActionType.LEARN, ActionType.PROJECT):
            evidence_value = 0.40
        else:
            evidence_value = 0.20

        practical_value = 0.90 if action_type == ActionType.PROJECT else 0.40
        time_cost = min(1.0, round(estimated_minutes / max(1, daily_minutes), 4))
        redundancy = 0.90 if (cur_mastery >= req_level and action_type != ActionType.SKIP) else 0.0
        repetition_penalty = 0.0

        # Compute ActionScore
        score = (
            self.WEIGHT_GAP * gap_reduction
            + self.WEIGHT_BOTTLENECK * bottleneck_relevance
            + self.WEIGHT_UNCERTAINTY * information_value
            + self.WEIGHT_PREREQUISITE * prerequisite_value
            + self.WEIGHT_PROGRESS * path_progress_value
            + self.WEIGHT_EVIDENCE * evidence_value
            + self.WEIGHT_PRACTICAL * practical_value
            - self.WEIGHT_TIME * time_cost
            - self.WEIGHT_REDUNDANCY * redundancy
            - self.WEIGHT_REPEAT * repetition_penalty
        )
        score = max(0.0, round(score, 4))

        metrics = ActionMetrics(
            gap_reduction=round(gap_reduction, 4),
            bottleneck_relevance=round(bottleneck_relevance, 4),
            information_value=round(information_value, 4),
            prerequisite_value=round(prerequisite_value, 4),
            path_progress_value=round(path_progress_value, 4),
            evidence_value=round(evidence_value, 4),
            practical_value=round(practical_value, 4),
            time_cost=round(time_cost, 4),
            redundancy=round(redundancy, 4),
            repetition_penalty=round(repetition_penalty, 4),
        )

        # Build structured explanation
        primary_reason = ""
        supporting_reasons: list[str] = []
        constraints_considered: list[str] = []
        tradeoffs: list[str] = []

        if action_type == ActionType.CONTINUE:
            primary_reason = f"You have an in-progress activity for {target_skill_name}."
            supporting_reasons.append("Resuming active learning avoids context switching.")
        elif action_type == ActionType.MASTERY_CHECK:
            primary_reason = f"You completed activity for {target_skill_name} but mastery is not yet proven."
            supporting_reasons.append("Completing the post-learning check converts activity effort into verified mastery.")
        elif action_type == ActionType.SKIP:
            primary_reason = f"Demonstrated mastery of {target_skill_name} ({cur_mastery*100:.0f}%) meets target requirement."
            supporting_reasons.append("Skipping sufficient competency accelerates your overall path completion.")
        elif action_type == ActionType.PREREQUISITE_REVIEW:
            primary_reason = f"{target_skill_name} is a required prerequisite for your primary bottleneck."
            supporting_reasons.append("Strengthening this foundational skill unlocks downstream Deep Learning progress.")
        elif action_type == ActionType.REASSESS:
            primary_reason = f"Mastery estimate for {target_skill_name} has low confidence ({cur_conf*100:.0f}%)."
            supporting_reasons.append("Targeted evaluation reduces diagnostic uncertainty to inform path decisions.")
        elif action_type == ActionType.PROJECT:
            primary_reason = f"Applied project for {target_skill_name} provides high practical mastery value."
            supporting_reasons.append("Hands-on implementation solidifies theoretical understanding.")
        else:
            primary_reason = f"{target_skill_name} addresses a target skill gap of {gap*100:.0f} points."
            if bottleneck_relevance >= 0.8:
                supporting_reasons.append("Directly targets your primary learning bottleneck.")

        if estimated_minutes > daily_minutes:
            constraints_considered.append(
                f"Estimated duration ({estimated_minutes} mins) exceeds preferred daily study window ({daily_minutes} mins)."
            )
            tradeoffs.append("May require split sessions across multiple days.")
        else:
            constraints_considered.append(
                f"Fits within preferred daily study window ({estimated_minutes} / {daily_minutes} mins)."
            )

        return NextActionItem(
            rank=1,
            action_type=action_type,
            title=title,
            target_skill_id=target_skill_id,
            target_skill_name=target_skill_name,
            resource_id=resource_id,
            path_node_id=path_node_id,
            attempt_id=attempt_id,
            score=score,
            feasible=True,
            estimated_minutes=estimated_minutes,
            primary_reason=primary_reason,
            supporting_reasons=supporting_reasons,
            metrics_used=metrics,
            constraints_considered=constraints_considered,
            tradeoffs=tradeoffs,
        )

    def _rank_candidates(self, candidates: list[NextActionItem]) -> list[NextActionItem]:
        def sort_key(cand: NextActionItem) -> tuple[Any, ...]:
            prio = self.ACTION_PRIORITY.get(cand.action_type, 99)
            return (
                -cand.score,
                -cand.metrics_used.bottleneck_relevance,
                -cand.metrics_used.gap_reduction,
                cand.estimated_minutes,
                prio,
                cand.title,
            )

        sorted_cands = sorted(candidates, key=sort_key)
        for i, c in enumerate(sorted_cands, start=1):
            c.rank = i
        return sorted_cands

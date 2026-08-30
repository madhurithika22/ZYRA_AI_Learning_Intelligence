from typing import Any
from uuid import UUID

from app.models.goal import Goal
from app.models.learning_activity_attempt import LearningActivityAttempt
from app.models.learning_path import LearningPath
from app.models.learning_path_node import LearningPathNode
from app.models.learning_resource import LearningResource
from app.models.role_skill import RoleSkill
from app.models.skill import Skill
from app.models.skill_mastery import SkillMastery
from app.models.skill_resource import SkillResource
from app.schemas.replanning import (
    NodeDeltaAction,
    NodeDeltaItem,
    PathDeltaSummary,
    PathDiffResponse,
    PathVersionItem,
    ReplanDecision,
    ReplanStatusResponse,
    ReplanTriggerType,
)
from app.services.bottleneck_analysis import BottleneckAnalysisService
from app.services.change_detection_service import ChangeDetectionService
from app.services.path_optimizer import PathOptimizer
from app.services.resource_candidate_filter import ResourceCandidateFilter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ReplanningService:
    """Orchestrates dynamic path replanning, minimal-change deltas, and path versioning."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.cd_service = ChangeDetectionService(db)
        self.b_service = BottleneckAnalysisService(db)
        self.optimizer = PathOptimizer()
        self.candidate_filter = ResourceCandidateFilter(db)

    async def get_replan_status(self, learner_id: UUID, goal_id: UUID) -> ReplanStatusResponse:
        """Fetch current active path replan status without creating a draft."""
        path_stmt = (
            select(LearningPath)
            .where(
                LearningPath.learner_id == learner_id,
                LearningPath.goal_id == goal_id,
                LearningPath.status == "active",
            )
            .order_by(LearningPath.version.desc())
        )
        active_path = (await self.db.execute(path_stmt)).scalars().first()

        if not active_path:
            raise ValueError(f"No active learning path found for learner {learner_id} and goal {goal_id}.")

        decision = await self.cd_service.detect_changes_and_evaluate(learner_id, goal_id, active_path)
        b_analysis = await self.b_service.analyze_bottlenecks(learner_id, goal_id)
        primary_b_name = b_analysis.primary_bottleneck.skill_name if b_analysis.primary_bottleneck else None

        trigger_str = decision.trigger_type.value if decision.trigger_type else "state change"
        summary = (
            f"Path V{active_path.version} status evaluated. "
            + (f"Replan recommended due to {trigger_str}." if decision.should_replan else "Path remains current.")
        )

        return ReplanStatusResponse(
            learner_id=learner_id,
            goal_id=goal_id,
            current_path_id=active_path.id,
            current_path_version=active_path.version,
            should_replan=decision.should_replan,
            staleness_score=decision.staleness_score,
            trigger_type=decision.trigger_type,
            primary_bottleneck_skill_name=primary_b_name,
            summary=summary,
            decision=decision,
        )

    async def generate_replan(
        self,
        learner_id: UUID,
        goal_id: UUID,
        manual_trigger: bool = False,
    ) -> ReplanDecision:
        """Generate a draft replanned path version V_{k+1} with a minimal path delta."""
        path_stmt = (
            select(LearningPath)
            .options(selectinload(LearningPath.nodes).selectinload(LearningPathNode.resource))
            .where(
                LearningPath.learner_id == learner_id,
                LearningPath.goal_id == goal_id,
                LearningPath.status == "active",
            )
            .order_by(LearningPath.version.desc())
        )
        active_path = (await self.db.execute(path_stmt)).scalars().first()

        if not active_path:
            raise ValueError(f"No active learning path found for learner {learner_id} and goal {goal_id}.")

        decision = await self.cd_service.detect_changes_and_evaluate(learner_id, goal_id, active_path)
        if manual_trigger:
            decision.should_replan = True
            decision.trigger_type = ReplanTriggerType.MANUAL_REPLAN
            decision.rationale = "Manual path replan explicitly requested by learner."

        if not decision.should_replan:
            return decision

        # 1. Fetch completed/proven attempts
        node_ids = [n.id for n in active_path.nodes]
        attempts_stmt = select(LearningActivityAttempt).where(
            LearningActivityAttempt.learner_id == learner_id,
            LearningActivityAttempt.learning_path_node_id.in_(node_ids),
        )
        attempts = list((await self.db.execute(attempts_stmt)).scalars().all())
        completed_node_map = {
            att.learning_path_node_id: att for att in attempts if att.status in ("completed", "proven")
        }

        # 2. Analyze Bottlenecks and Skill Mastery
        b_analysis = await self.b_service.analyze_bottlenecks(learner_id, goal_id)
        current_primary_b = b_analysis.primary_bottleneck
        primary_sk_id = current_primary_b.skill_id if current_primary_b else None

        goal_stmt = select(Goal).where(Goal.id == goal_id)
        goal = (await self.db.execute(goal_stmt)).scalar_one()

        rs_stmt = select(RoleSkill).where(RoleSkill.role_id == goal.target_role_id)
        role_skills = list((await self.db.execute(rs_stmt)).scalars().all())
        rs_map = {rs.skill_id: rs for rs in role_skills}

        all_sk_ids = list(set([rs.skill_id for rs in role_skills] + [n.skill_id for n in active_path.nodes if n.skill_id]))
        sm_stmt = select(SkillMastery).where(
            SkillMastery.learner_id == learner_id,
            SkillMastery.skill_id.in_(all_sk_ids),
        )
        sm_records = list((await self.db.execute(sm_stmt)).scalars().all())
        sm_map = {sm.skill_id: sm for sm in sm_records}

        # 3. Construct Path Delta (KEEP, SKIP, REMOVE, INSERT, REORDER)
        kept_nodes: list[NodeDeltaItem] = []
        removed_nodes: list[NodeDeltaItem] = []
        skipped_nodes: list[NodeDeltaItem] = []
        added_nodes: list[NodeDeltaItem] = []
        reordered_nodes: list[NodeDeltaItem] = []

        new_path_nodes_data: list[dict[str, Any]] = []
        seq = 1

        for old_node in sorted(active_path.nodes, key=lambda x: x.sequence):
            res_title = old_node.resource.title if old_node.resource else "Resource"
            sk_name = old_node.skill.name if old_node.skill else "Skill"

            # Case A: Completed / Proven work (PRESERVED ALWAYS)
            if old_node.id in completed_node_map:
                delta_item = NodeDeltaItem(
                    action=NodeDeltaAction.COMPLETE,
                    resource_id=old_node.resource_id,
                    resource_title=res_title,
                    skill_id=old_node.skill_id,
                    skill_name=sk_name,
                    old_sequence=old_node.sequence,
                    new_sequence=seq,
                    reason="Completed activity preserved from previous path version.",
                )
                kept_nodes.append(delta_item)
                new_path_nodes_data.append({
                    "sequence": seq,
                    "resource_id": old_node.resource_id,
                    "skill_id": old_node.skill_id,
                    "milestone_label": old_node.milestone_label,
                    "estimated_minutes": old_node.estimated_minutes,
                    "rationale": "Preserved completed activity.",
                    "source_node_id": old_node.id,
                    "status": "completed",
                })
                seq += 1
                continue

            # Case B: Future node skill already mastered (SKIP / OBSOLETE)
            if old_node.skill_id and sm_map.get(old_node.skill_id):
                sm = sm_map[old_node.skill_id]
                rs = rs_map.get(old_node.skill_id)
                req = rs.required_level if rs else 0.80
                if sm.mastery_score >= req and sm.confidence >= 0.80:
                    delta_item = NodeDeltaItem(
                        action=NodeDeltaAction.SKIP,
                        resource_id=old_node.resource_id,
                        resource_title=res_title,
                        skill_id=old_node.skill_id,
                        skill_name=sk_name,
                        old_sequence=old_node.sequence,
                        new_sequence=None,
                        reason=f"Skipped because {sk_name} mastery ({sm.mastery_score:.0%}) meets requirement.",
                    )
                    skipped_nodes.append(delta_item)
                    continue

            # Case C: Retain valid future node
            delta_item = NodeDeltaItem(
                action=NodeDeltaAction.KEEP,
                resource_id=old_node.resource_id,
                resource_title=res_title,
                skill_id=old_node.skill_id,
                skill_name=sk_name,
                old_sequence=old_node.sequence,
                new_sequence=seq,
                reason="Retained valid learning activity.",
            )
            kept_nodes.append(delta_item)
            new_path_nodes_data.append({
                "sequence": seq,
                "resource_id": old_node.resource_id,
                "skill_id": old_node.skill_id,
                "milestone_label": old_node.milestone_label,
                "estimated_minutes": old_node.estimated_minutes,
                "rationale": old_node.rationale,
                "source_node_id": old_node.id,
                "status": "pending",
            })
            seq += 1

        # Case D: Insert new activity if primary bottleneck lacks active coverage
        has_primary_coverage = any(n["skill_id"] == primary_sk_id for n in new_path_nodes_data)
        if primary_sk_id and not has_primary_coverage:
            sr_stmt = (
                select(LearningResource)
                .join(SkillResource, SkillResource.resource_id == LearningResource.id)
                .where(SkillResource.skill_id == primary_sk_id)
            )
            candidates = list((await self.db.execute(sr_stmt)).scalars().all())
            if candidates:
                res_to_add = candidates[0]
                sk_obj = (await self.db.execute(select(Skill).where(Skill.id == primary_sk_id))).scalar_one_or_none()
                sk_name = sk_obj.name if sk_obj else "Primary Bottleneck Skill"

                delta_item = NodeDeltaItem(
                    action=NodeDeltaAction.INSERT,
                    resource_id=res_to_add.id,
                    resource_title=res_to_add.title,
                    skill_id=primary_sk_id,
                    skill_name=sk_name,
                    old_sequence=None,
                    new_sequence=seq,
                    reason=f"Inserted to address new primary bottleneck in {sk_name}.",
                )
                added_nodes.append(delta_item)
                new_path_nodes_data.append({
                    "sequence": seq,
                    "resource_id": res_to_add.id,
                    "skill_id": primary_sk_id,
                    "milestone_label": f"Mastery: {sk_name}",
                    "estimated_minutes": res_to_add.estimated_minutes or 45,
                    "rationale": f"Targeted intervention for {sk_name}.",
                    "source_node_id": None,
                    "status": "pending",
                })
                seq += 1

        # 4. Build Structured Path Delta Summary
        total_est_minutes = sum(n["estimated_minutes"] for n in new_path_nodes_data if n["estimated_minutes"])
        summary_text = (
            f"Replan V{active_path.version + 1}: {len(kept_nodes)} kept/completed, "
            f"{len(added_nodes)} inserted, {len(skipped_nodes)} skipped."
        )

        delta_summary = PathDeltaSummary(
            added_nodes=added_nodes,
            removed_nodes=removed_nodes,
            kept_nodes=kept_nodes,
            reordered_nodes=reordered_nodes,
            skipped_nodes=skipped_nodes,
            summary_text=summary_text,
        )

        # 5. Persist Draft LearningPath Version V_{k+1}
        new_path_version = LearningPath(
            learner_id=learner_id,
            goal_id=goal_id,
            name=f"{active_path.name} (V{active_path.version + 1})",
            strategy=active_path.strategy,
            status="draft",
            version=active_path.version + 1,
            parent_path_id=active_path.id,
            generation_reason=decision.rationale,
            change_summary=delta_summary.model_dump(mode="json"),
            estimated_minutes=total_est_minutes,
            expected_readiness=active_path.expected_readiness,
        )
        self.db.add(new_path_version)
        await self.db.flush()

        # Add Nodes to new draft path
        for nd in new_path_nodes_data:
            node_obj = LearningPathNode(
                learning_path_id=new_path_version.id,
                sequence=nd["sequence"],
                resource_id=nd["resource_id"],
                skill_id=nd["skill_id"],
                milestone_label=nd["milestone_label"],
                estimated_minutes=nd["estimated_minutes"],
                rationale=nd["rationale"],
                source_node_id=nd["source_node_id"],
                status=nd["status"],
            )
            self.db.add(node_obj)

        await self.db.commit()

        decision.draft_path_id = new_path_version.id
        decision.path_delta = delta_summary
        return decision

    async def accept_replan(self, draft_path_id: UUID) -> PathVersionItem:
        """Accept draft path version, marking parent path superseded and draft path active."""
        draft_stmt = (
            select(LearningPath)
            .options(selectinload(LearningPath.nodes))
            .where(LearningPath.id == draft_path_id)
        )
        draft_path = (await self.db.execute(draft_stmt)).scalar_one_or_none()

        if not draft_path:
            raise ValueError(f"Draft path {draft_path_id} not found.")

        if draft_path.status != "draft":
            raise ValueError(f"Path {draft_path_id} status is '{draft_path.status}', expected 'draft'.")

        # Mark parent path superseded
        if draft_path.parent_path_id:
            parent_stmt = select(LearningPath).where(LearningPath.id == draft_path.parent_path_id)
            parent_path = (await self.db.execute(parent_stmt)).scalar_one_or_none()
            if parent_path:
                parent_path.status = "superseded"

        # Activate draft path
        draft_path.status = "active"
        await self.db.commit()

        return PathVersionItem(
            path_id=draft_path.id,
            version=draft_path.version,
            parent_path_id=draft_path.parent_path_id,
            status=draft_path.status,
            generation_reason=draft_path.generation_reason,
            created_at=draft_path.created_at,
            nodes_count=len(draft_path.nodes),
            estimated_minutes=draft_path.estimated_minutes,
        )

    async def reject_replan(self, draft_path_id: UUID) -> PathVersionItem:
        """Reject draft path version, setting status to rejected while parent remains active."""
        draft_stmt = (
            select(LearningPath)
            .options(selectinload(LearningPath.nodes))
            .where(LearningPath.id == draft_path_id)
        )
        draft_path = (await self.db.execute(draft_stmt)).scalar_one_or_none()

        if not draft_path:
            raise ValueError(f"Draft path {draft_path_id} not found.")

        draft_path.status = "rejected"
        await self.db.commit()

        return PathVersionItem(
            path_id=draft_path.id,
            version=draft_path.version,
            parent_path_id=draft_path.parent_path_id,
            status=draft_path.status,
            generation_reason=draft_path.generation_reason,
            created_at=draft_path.created_at,
            nodes_count=len(draft_path.nodes),
            estimated_minutes=draft_path.estimated_minutes,
        )

    async def get_path_versions(self, path_id: UUID) -> list[PathVersionItem]:
        """Fetch complete version lineage history for a learning path."""
        target_stmt = select(LearningPath).where(LearningPath.id == path_id)
        target_path = (await self.db.execute(target_stmt)).scalar_one_or_none()

        if not target_path:
            raise ValueError(f"LearningPath {path_id} not found.")

        lineage_stmt = (
            select(LearningPath)
            .options(selectinload(LearningPath.nodes))
            .where(
                LearningPath.learner_id == target_path.learner_id,
                LearningPath.goal_id == target_path.goal_id,
            )
            .order_by(LearningPath.version.asc())
        )
        paths = list((await self.db.execute(lineage_stmt)).scalars().all())

        return [
            PathVersionItem(
                path_id=p.id,
                version=p.version,
                parent_path_id=p.parent_path_id,
                status=p.status,
                generation_reason=p.generation_reason,
                created_at=p.created_at,
                nodes_count=len(p.nodes),
                estimated_minutes=p.estimated_minutes,
            )
            for p in paths
        ]

    async def get_path_diff(self, from_path_id: UUID, to_path_id: UUID) -> PathDiffResponse:
        """Compare two path versions and return structured diff response."""
        p_from_stmt = (
            select(LearningPath)
            .options(selectinload(LearningPath.nodes).selectinload(LearningPathNode.resource))
            .where(LearningPath.id == from_path_id)
        )
        p_from = (await self.db.execute(p_from_stmt)).scalar_one()

        p_to_stmt = (
            select(LearningPath)
            .options(selectinload(LearningPath.nodes).selectinload(LearningPathNode.resource))
            .where(LearningPath.id == to_path_id)
        )
        p_to = (await self.db.execute(p_to_stmt)).scalar_one()

        change_summary_json = p_to.change_summary or {}
        delta = PathDeltaSummary.model_validate(change_summary_json)

        return PathDiffResponse(
            from_path_id=p_from.id,
            from_version=p_from.version,
            to_path_id=p_to.id,
            to_version=p_to.version,
            delta=delta,
        )

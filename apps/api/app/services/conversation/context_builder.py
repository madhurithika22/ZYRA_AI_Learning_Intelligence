from typing import Any
from uuid import UUID

from app.schemas.conversation import ConversationIntent, SourceReference, SourceType
from app.schemas.learning_twin import LearningTwinResponse
from app.services.learning_twin_service import LearningTwinService
from sqlalchemy.ext.asyncio import AsyncSession


class ContextBuilder:
    """Retrieves minimal, authoritative context payloads and maps valid source references."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.twin_service = LearningTwinService(db)

    async def build_grounded_context(
        self,
        learner_id: UUID,
        intent: ConversationIntent,
        entities: dict[str, Any],
    ) -> tuple[dict[str, Any], list[SourceReference], dict[str, SourceReference]]:
        """Build targeted grounded context payload and return valid source reference list and map."""
        twin: LearningTwinResponse = await self.twin_service.get_learning_twin(learner_id, include_trace=True)

        valid_sources: list[SourceReference] = []
        source_map: dict[str, SourceReference] = {}

        def add_source(s_type: SourceType, s_id: str, s_label: str) -> None:
            ref = SourceReference(source_type=s_type, source_id=s_id, label=s_label)
            valid_sources.append(ref)
            source_map[s_id] = ref

        context_data: dict[str, Any] = {
            "learner_name": twin.display_name,
            "intent": intent.value,
        }

        # 1. Goal Context
        if twin.goal:
            context_data["goal"] = {
                "objective": twin.goal.objective,
                "target_role": twin.goal.target_role_name,
                "goal_skill_progress": f"{twin.goal.goal_skill_progress:.1%}",
            }
            if twin.goal.goal_id:
                add_source(SourceType.GOAL, f"goal-{twin.goal.goal_id}", f"Goal: {twin.goal.objective}")
            if twin.goal.target_role_id:
                add_source(SourceType.ROLE_REQUIREMENT, f"role-{twin.goal.target_role_id}", f"Role Requirement: {twin.goal.target_role_name}")

        # 2. Bottleneck Context
        if twin.bottleneck and intent in (
            ConversationIntent.BOTTLENECK_EXPLANATION,
            ConversationIntent.NEXT_ACTION_EXPLANATION,
            ConversationIntent.COMPARISON,
            ConversationIntent.PROGRESS_SUMMARY,
        ):
            b = twin.bottleneck
            context_data["primary_bottleneck"] = {
                "skill_name": b.skill_name,
                "mastery": f"{b.mastery_score:.0%}",
                "required_level": f"{b.required_level:.0%}",
                "gap": f"{b.gap:.0%}",
                "confidence": f"{b.confidence:.0%}",
                "dependency_impact": b.dependency_impact,
                "bottleneck_score": b.bottleneck_score,
                "reason": b.reason,
                "affected_skills": b.affected_skills,
            }
            add_source(SourceType.BOTTLENECK_ANALYSIS, "bottleneck-analysis", f"Bottleneck Analysis: {b.skill_name}")

        # 3. Next Action Context
        if twin.next_action and intent in (
            ConversationIntent.NEXT_ACTION_EXPLANATION,
            ConversationIntent.BOTTLENECK_EXPLANATION,
            ConversationIntent.COMPARISON,
        ):
            na = twin.next_action
            context_data["next_best_action"] = {
                "action_type": na.action_type,
                "title": na.title,
                "target_skill": na.target_skill_name,
                "estimated_minutes": na.estimated_minutes,
                "action_confidence": f"{na.action_confidence:.0%}",
                "score": na.score,
                "primary_reason": na.primary_reason,
                "supporting_reasons": na.reasons,
            }
            add_source(SourceType.NEXT_ACTION, "next-action", f"Next Action: {na.title}")

        # 4. Path & Replanning Context
        if twin.path:
            p = twin.path
            context_data["active_path"] = {
                "version": f"V{p.version}",
                "name": p.name,
                "completion_percentage": f"{p.completion_percentage:.0%}",
                "completed_nodes": p.completed_nodes,
                "total_nodes": p.total_nodes,
                "remaining_minutes": p.remaining_minutes,
                "is_stale": p.is_stale,
            }
            if p.path_id:
                add_source(SourceType.LEARNING_PATH, f"learning-path-{p.path_id}", f"Learning Path V{p.version}")

        if twin.replan and twin.replan.should_replan and intent in (
            ConversationIntent.PATH_EXPLANATION,
            ConversationIntent.REPLAN_EXPLANATION,
        ):
            r = twin.replan
            context_data["replan_status"] = {
                "should_replan": r.should_replan,
                "staleness_score": r.staleness_score,
                "trigger_type": r.trigger_type,
                "rationale": r.rationale,
            }
            add_source(SourceType.PATH_DIFF, "path-replan", f"Path Replan Trigger: {r.trigger_type}")

        # 5. Skills Matrix Context
        if twin.skills:
            skills_ctx = []
            for sk in twin.skills:
                skills_ctx.append({
                    "skill_name": sk.skill_name,
                    "mastery": f"{sk.mastery:.0%}",
                    "required": f"{sk.required:.0%}",
                    "gap": f"{sk.gap:.0%}",
                    "confidence": f"{sk.confidence:.0%}",
                    "status": sk.status,
                    "evidence_count": sk.evidence_count,
                })
                add_source(SourceType.SKILL_MASTERY, f"skill-{sk.skill_id}", f"Skill Mastery: {sk.skill_name}")
            context_data["target_skills"] = skills_ctx

        # 6. Evidence Summary Context
        if twin.evidence_summary and intent in (
            ConversationIntent.EVIDENCE_QUERY,
            ConversationIntent.SKILL_HISTORY,
            ConversationIntent.UNCERTAINTY_QUERY,
        ):
            ev = twin.evidence_summary
            context_data["evidence_summary"] = {
                "total_evidence_records": ev.total_evidence_count,
                "demonstrated_skills_count": ev.demonstrated_skills_count,
                "improving_skills_count": ev.improving_skills_count,
                "insufficient_evidence_count": ev.insufficient_evidence_count,
                "recently_verified_skills": ev.recently_verified_skills,
            }
            add_source(SourceType.SKILL_EVIDENCE, "evidence-summary", "Evidence & Mastery Summary")

        return context_data, valid_sources, source_map

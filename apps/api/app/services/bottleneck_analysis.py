from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.models.goal import Goal
from app.models.learner import Learner
from app.models.role_skill import RoleSkill
from app.models.skill_evidence import SkillEvidence
from app.models.skill_mastery import SkillMastery
from app.schemas.bottleneck import (
    BottleneckAnalysisResponse,
    BottleneckExplanation,
    SkillGapItem,
)
from app.services.dependency_impact import DependencyImpactService
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class BottleneckAnalysisService:
    """Service orchestrating deterministic skill gap analysis, bottleneck scoring, and explanation generation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.dependency_service = DependencyImpactService(session)

    async def analyze_bottlenecks(
        self,
        learner_id: UUID,
        goal_id: UUID,
    ) -> BottleneckAnalysisResponse:
        now = datetime.now(timezone.utc)

        # 1. Validate learner and goal exist
        learner = await self.session.get(Learner, learner_id)
        if not learner:
            raise ValueError(f"Learner with ID '{learner_id}' not found.")

        goal = await self.session.get(Goal, goal_id)
        if not goal:
            raise ValueError(f"Goal with ID '{goal_id}' not found.")

        # 2. Fetch role skill requirements
        role_skills_stmt = (
            select(RoleSkill)
            .where(RoleSkill.role_id == goal.target_role_id)
            .options(
                selectinload(RoleSkill.skill),
                selectinload(RoleSkill.role),
            )
        )
        role_skills_res = await self.session.execute(role_skills_stmt)
        role_skills = role_skills_res.scalars().all()
        if not role_skills:
            raise ValueError("No skill requirements defined for target role.")

        target_role_name = role_skills[0].role.name if role_skills[0].role else "Target Role"
        target_skill_ids = [rs.skill_id for rs in role_skills]
        role_importance_map = {rs.skill_id: rs.importance for rs in role_skills}

        # 3. Compute weighted dependency impacts via DependencyImpactService
        impact_results = await self.dependency_service.compute_dependency_impacts(
            target_skill_ids=target_skill_ids,
            role_importance_map=role_importance_map,
        )

        # 4. Fetch existing learner SkillMastery and SkillEvidence records
        mastery_stmt = select(SkillMastery).where(
            SkillMastery.learner_id == learner_id,
            SkillMastery.skill_id.in_(target_skill_ids),
        )
        mastery_res = await self.session.execute(mastery_stmt)
        masteries = {m.skill_id: m for m in mastery_res.scalars().all()}

        evidence_counts: dict[UUID, int] = {}
        for skill_id in target_skill_ids:
            cnt_stmt = select(func.count(SkillEvidence.id)).where(
                SkillEvidence.learner_id == learner_id,
                SkillEvidence.skill_id == skill_id,
            )
            cnt = (await self.session.execute(cnt_stmt)).scalar() or 0
            evidence_counts[skill_id] = cnt

        # 5. Compute raw metric items for all target skills
        raw_items: list[dict[str, Any]] = []

        for rs in role_skills:
            skill = rs.skill
            skill_name = skill.name if skill else "Unknown Skill"
            req_level = rs.required_level

            # Normalize required_level to [0.0, 1.0] if stored on 1.0-5.0 scale
            norm_req = (req_level - 1.0) / 4.0 if req_level > 1.0 else req_level
            norm_req = max(0.0, min(1.0, norm_req))

            m_rec = masteries.get(rs.skill_id)
            mastery_score = m_rec.mastery_score if m_rec else 0.0
            confidence = m_rec.confidence if m_rec else 0.0
            ev_count = evidence_counts.get(rs.skill_id, 0)

            gap = max(0.0, norm_req - mastery_score)
            role_imp = rs.importance
            impact_res = impact_results.get(rs.skill_id)
            dep_impact = impact_res.impact_score if impact_res else 1.0
            downstream_names = impact_res.downstream_skill_names if impact_res else []

            # Uncertainty factor: 1.0 - (confidence * 0.5)
            uncertainty_factor = 1.0 - (confidence * 0.5)

            # Deterministic Bottleneck Score
            bottleneck_score = round(gap * role_imp * dep_impact * uncertainty_factor, 4)

            # Classification logic
            if ev_count == 0 or confidence < 0.25:
                classification = "insufficient_evidence"
            elif bottleneck_score >= 1.5 and confidence >= 0.4:
                classification = "critical"
            elif bottleneck_score >= 1.0 and confidence >= 0.3:
                classification = "high"
            elif bottleneck_score >= 0.5:
                classification = "moderate"
            else:
                classification = "low"

            raw_items.append(
                {
                    "skill_id": rs.skill_id,
                    "skill_name": skill_name,
                    "required_level": norm_req,
                    "mastery": mastery_score,
                    "confidence": confidence,
                    "gap": round(gap, 4),
                    "role_importance": role_imp,
                    "dependency_impact": dep_impact,
                    "uncertainty_factor": round(uncertainty_factor, 4),
                    "bottleneck_score": bottleneck_score,
                    "classification": classification,
                    "downstream_names": downstream_names,
                    "evidence_count": ev_count,
                }
            )

        # 6. Sort deterministically: -bottleneck_score, -role_importance, -gap, skill_name
        sorted_items = sorted(
            raw_items,
            key=lambda x: (
                -x["bottleneck_score"],
                -x["role_importance"],
                -x["gap"],
                x["skill_name"],
            ),
        )

        # 7. Build structured SkillGapItem list with explanations
        final_gap_items: list[SkillGapItem] = []
        for idx, item in enumerate(sorted_items, start=1):
            explanation = self._build_explanation(
                skill_name=item["skill_name"],
                mastery=item["mastery"],
                required_level=item["required_level"],
                role_importance=item["role_importance"],
                dep_impact=item["dependency_impact"],
                confidence=item["confidence"],
                classification=item["classification"],
                downstream_names=item["downstream_names"],
            )

            final_gap_items.append(
                SkillGapItem(
                    skill_id=item["skill_id"],
                    skill_name=item["skill_name"],
                    required_level=round(item["required_level"], 4),
                    mastery=round(item["mastery"], 4),
                    confidence=round(item["confidence"], 4),
                    gap=item["gap"],
                    role_importance=item["role_importance"],
                    dependency_impact=item["dependency_impact"],
                    uncertainty_factor=item["uncertainty_factor"],
                    bottleneck_score=item["bottleneck_score"],
                    rank=idx,
                    classification=item["classification"],
                    explanation=explanation,
                )
            )

        primary = final_gap_items[0] if final_gap_items else None
        secondary = [
            item
            for item in final_gap_items[1:]
            if item.classification in ("critical", "high", "moderate")
        ]

        return BottleneckAnalysisResponse(
            learner_id=learner_id,
            goal_id=goal_id,
            target_role=target_role_name,
            analyzed_at=now,
            primary_bottleneck=primary,
            secondary_bottlenecks=secondary,
            all_gaps=final_gap_items,
        )

    @staticmethod
    def _build_explanation(
        skill_name: str,
        mastery: float,
        required_level: float,
        role_importance: float,
        dep_impact: float,
        confidence: float,
        classification: str,
        downstream_names: list[str],
    ) -> BottleneckExplanation:
        evidence_bullets = [
            f"Demonstrated Mastery = {Math_pct(mastery)}",
            f"Target Required Level = {Math_pct(required_level)}",
            f"Role Importance = {role_importance:.2f}",
            f"Evidence Confidence = {Math_pct(confidence)}",
        ]

        if downstream_names:
            evidence_bullets.append(
                f"Downstream dependency impact score = {dep_impact:.2f} affecting {len(downstream_names)} target skill(s)."
            )

        if classification == "critical":
            reason = f"Critical learning bottleneck in high-priority skill '{skill_name}' with significant downstream dependency impact."
        elif classification == "high":
            reason = f"High-priority skill gap in '{skill_name}' restricting progress in downstream target competencies."
        elif classification == "insufficient_evidence":
            reason = f"Insufficient assessment evidence for '{skill_name}'. Diagnostic confidence remains low."
        elif classification == "moderate":
            reason = f"Moderate skill gap in '{skill_name}' relative to target role requirements."
        else:
            reason = f"Competency in '{skill_name}' is currently sufficient for target role requirements."

        return BottleneckExplanation(
            primary_reason=reason,
            evidence=evidence_bullets,
            downstream_skills=downstream_names,
        )


def Math_pct(val: float) -> str:
    """Helper formatting float to clean percentage string."""
    return f"{round(val * 100)}%"

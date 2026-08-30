from typing import NamedTuple
from uuid import UUID

from app.models.learning_resource import LearningResource
from app.models.skill_resource import SkillResource
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class SkillCoverageInfo(NamedTuple):
    skill_id: UUID
    relevance: float


class CandidateResource(NamedTuple):
    resource_id: UUID
    title: str
    resource_type: str
    difficulty: float
    estimated_minutes: int
    covered_skills: list[SkillCoverageInfo]
    incremental_gap_value: float
    practical_value: float


class ResourceCandidateFilter:
    """Service for batch-loading catalog resources and filtering out zero-utility or fully mastered content."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_candidate_resources(
        self,
        target_skill_gaps: dict[UUID, float],
        role_importance_map: dict[UUID, float],
        mastered_skill_ids: set[UUID],
    ) -> list[CandidateResource]:
        stmt = select(LearningResource).options(
            selectinload(LearningResource.covered_skills).selectinload(SkillResource.skill)
        )
        res = await self.session.execute(stmt)
        all_resources = res.scalars().all()

        candidates: list[CandidateResource] = []

        for r in all_resources:
            covered: list[SkillCoverageInfo] = []
            incremental_value: float = 0.0
            has_unmastered_need = False

            for sr in r.covered_skills:
                covered.append(SkillCoverageInfo(skill_id=sr.skill_id, relevance=sr.relevance))

                # Check if this covered skill is in target role requirements and has a gap
                gap = target_skill_gaps.get(sr.skill_id, 0.0)
                imp = role_importance_map.get(sr.skill_id, 0.0)

                if sr.skill_id not in mastered_skill_ids and gap > 0.0:
                    has_unmastered_need = True
                    incremental_value += sr.relevance * gap * imp

            # If resource covers ONLY mastered skills with zero remaining gap, exclude it
            if not has_unmastered_need and covered:
                continue

            # Determine practical value based on resource type
            r_type = r.resource_type.lower()
            if r_type in ("project", "interactive", "coding_exercise", "applied_lab"):
                practical_value = 0.90
            elif r_type in ("video", "article", "reading", "documentation"):
                practical_value = 0.40
            else:
                practical_value = 0.50

            est_minutes = (
                r.estimated_minutes if r.estimated_minutes and r.estimated_minutes > 0 else 60
            )

            candidates.append(
                CandidateResource(
                    resource_id=r.id,
                    title=r.title,
                    resource_type=r.resource_type,
                    difficulty=r.difficulty,
                    estimated_minutes=est_minutes,
                    covered_skills=covered,
                    incremental_gap_value=round(incremental_value, 4),
                    practical_value=practical_value,
                )
            )

        return candidates

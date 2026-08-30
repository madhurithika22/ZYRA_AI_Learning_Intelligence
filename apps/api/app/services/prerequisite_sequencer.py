from uuid import UUID

from app.models.skill_relation import SkillRelation
from app.services.resource_candidate_filter import CandidateResource
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class PrerequisiteSequencer:
    """Service for topological and prerequisite-aware sequencing of learning activities."""

    def __init__(self, session: AsyncSession | None = None) -> None:
        self.session = session


    async def get_prerequisite_map(self) -> dict[UUID, set[UUID]]:
        """Returns map: target_skill_id -> set of prerequisite source_skill_ids."""
        if not self.session:
            raise ValueError("AsyncSession is required to fetch prerequisite map.")

        stmt = select(SkillRelation).where(SkillRelation.relation_type == "prerequisite")
        res = await self.session.execute(stmt)
        relations = res.scalars().all()


        prereq_map: dict[UUID, set[UUID]] = {}
        for rel in relations:
            # rel.source_skill_id is prerequisite for rel.target_skill_id
            prereq_map.setdefault(rel.target_skill_id, set()).add(rel.source_skill_id)

        return prereq_map

    def sequence_resources(
        self,
        candidate_resources: list[CandidateResource],
        prereq_map: dict[UUID, set[UUID]],
        mastered_skill_ids: set[UUID],
    ) -> list[CandidateResource]:
        """Sequences selected resources so unfulfilled prerequisite skills are scheduled before downstream skills."""
        if not candidate_resources:
            return []

        satisfied_skills = set(mastered_skill_ids)
        remaining = list(candidate_resources)
        sequenced: list[CandidateResource] = []

        while remaining:
            schedulable: CandidateResource | None = None
            schedulable_idx: int = -1

            # Find the best resource whose prerequisites are satisfied or already covered in sequenced steps
            for idx, r in enumerate(remaining):
                unmet_prereqs = False
                for cov in r.covered_skills:
                    prereqs = prereq_map.get(cov.skill_id, set())
                    # Check if any prerequisite for this target skill is missing from satisfied_skills
                    # AND covered by another resource in remaining
                    for p_id in prereqs:
                        if p_id not in satisfied_skills and any(
                            p_id in [c.skill_id for c in rem.covered_skills]
                            for rem in remaining
                            if rem != r
                        ):
                            unmet_prereqs = True
                            break
                    if unmet_prereqs:
                        break

                if not unmet_prereqs:
                    schedulable = r
                    schedulable_idx = idx
                    break

            # Fallback: if no perfectly schedulable candidate found (e.g. cycle or strict lock), pop first remaining
            if not schedulable:
                schedulable = remaining.pop(0)
            else:
                remaining.pop(schedulable_idx)

            sequenced.append(schedulable)
            for cov in schedulable.covered_skills:
                satisfied_skills.add(cov.skill_id)

        return sequenced

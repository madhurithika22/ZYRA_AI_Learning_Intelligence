import re

from app.models.skill import Skill
from app.schemas.goal_intelligence import ResolvedSkillInfo, ResolvedSkillItem
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

SKILL_ALIASES: dict[str, str] = {
    "basic ml": "Machine Learning",
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "python": "Python",
    "stats": "Statistics",
    "statistics": "Statistics",
    "lin alg": "Linear Algebra",
    "linear algebra": "Linear Algebra",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "pytorch": "PyTorch",
    "docker": "Docker",
    "deployment": "Model Deployment",
    "model deployment": "Model Deployment",
    "mlops": "MLOps",
    "system design": "System Design",
}


class SkillResolutionService:
    """Service for resolving learner-stated existing skill phrases to canonical database skills."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve_skills(self, stated_skills: list[str]) -> ResolvedSkillInfo:
        if not stated_skills:
            return ResolvedSkillInfo(resolved_skills=[], unresolved_skills=[])

        stmt = select(Skill)
        result = await self.session.execute(stmt)
        all_skills = result.scalars().all()
        skills_by_name = {s.name.lower(): s for s in all_skills}

        resolved: list[ResolvedSkillItem] = []
        unresolved: list[str] = []
        seen_skill_ids: set[str] = set()

        for raw_phrase in stated_skills:
            cleaned = raw_phrase.lower().strip()
            cleaned = re.sub(r"\s+", " ", cleaned)

            matched_skill: Skill | None = None

            # 1. Exact match
            if cleaned in skills_by_name:
                matched_skill = skills_by_name[cleaned]
            # 2. Alias dictionary match
            elif cleaned in SKILL_ALIASES:
                target_name = SKILL_ALIASES[cleaned].lower()
                if target_name in skills_by_name:
                    matched_skill = skills_by_name[target_name]

            if matched_skill:
                skill_id_str = str(matched_skill.id)
                if skill_id_str not in seen_skill_ids:
                    seen_skill_ids.add(skill_id_str)
                    resolved.append(
                        ResolvedSkillItem(
                            skill_id=matched_skill.id,
                            name=matched_skill.name,
                        )
                    )
            else:
                unresolved.append(raw_phrase)

        return ResolvedSkillInfo(
            resolved_skills=resolved,
            unresolved_skills=unresolved,
        )

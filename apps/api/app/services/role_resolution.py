import re

from app.models.role import Role
from app.schemas.goal_intelligence import ResolvedRoleInfo
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

ROLE_ALIASES: dict[str, str] = {
    "ml engineer": "ML Engineer",
    "machine learning engineer": "ML Engineer",
    "ai/ml engineer": "ML Engineer",
    "ai engineer": "AI Engineer",
    "artificial intelligence engineer": "AI Engineer",
    "data scientist": "Data Scientist",
    "ds": "Data Scientist",
}


class RoleResolutionService:
    """Service for resolving natural language role statements to canonical database roles."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve_role(self, raw_role_text: str) -> ResolvedRoleInfo:
        if not raw_role_text or not raw_role_text.strip():
            return ResolvedRoleInfo(
                is_resolved=False,
                confidence=0.0,
                ambiguity_reason="Target role input string was empty.",
            )

        # 1. Normalize input string
        cleaned = raw_role_text.lower().strip()
        cleaned = re.sub(r"^(become\s+(?:an?\s+)?|work\s+as\s+(?:an?\s+)?)", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)

        # 2. Query all roles from database
        stmt = select(Role).where(func.lower(Role.name) == cleaned.lower().strip())
        result = await self.session.execute(stmt)
        roles = result.scalar_one_or_none()
        roles_by_name = {r.name.lower(): r for r in roles}

        # 3. Exact match against DB role names
        if cleaned in roles_by_name:
            matched = roles_by_name[cleaned]
            return ResolvedRoleInfo(
                canonical_role_id=matched.id,
                canonical_role_name=matched.name,
                confidence=1.0,
                is_resolved=True,
            )

        # 4. Alias dictionary match
        if cleaned in ROLE_ALIASES:
            alias_target = ROLE_ALIASES[cleaned].lower()
            if alias_target in roles_by_name:
                matched = roles_by_name[alias_target]
                return ResolvedRoleInfo(
                    canonical_role_id=matched.id,
                    canonical_role_name=matched.name,
                    confidence=0.95,
                    is_resolved=True,
                )

        # 5. Fallback substring match if unique
        matching_roles = [
            r for name, r in roles_by_name.items() if cleaned in name or name in cleaned
        ]
        if len(matching_roles) == 1:
            matched = matching_roles[0]
            return ResolvedRoleInfo(
                canonical_role_id=matched.id,
                canonical_role_name=matched.name,
                confidence=0.85,
                is_resolved=True,
            )

        # Unresolved role case
        return ResolvedRoleInfo(
            canonical_role_id=None,
            canonical_role_name=None,
            confidence=0.0,
            is_resolved=False,
            ambiguity_reason=f"Target role '{raw_role_text}' could not be deterministically matched to existing roles.",
        )

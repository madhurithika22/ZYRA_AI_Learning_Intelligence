from app.providers.llm.base import LLMProvider
from app.providers.llm.factory import get_llm_provider
from app.schemas.goal_intelligence import (
    GoalIntelligenceResult,
    GoalInterpretation,
)
from app.services.role_resolution import RoleResolutionService
from app.services.skill_resolution import SkillResolutionService
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession


class GoalIntelligenceService:
    """Core domain service orchestrating goal interpretation, role resolution, and validation."""

    def __init__(
        self,
        session: AsyncSession,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.session = session
        self.llm_provider = llm_provider or get_llm_provider()
        self.role_resolver = RoleResolutionService(session)
        self.skill_resolver = SkillResolutionService(session)

    async def interpret_goal(self, prompt: str) -> GoalIntelligenceResult:
        validation_errors: list[str] = []

        # 1. Invoke LLM provider for structured interpretation
        try:
            interpretation = await self.llm_provider.generate_structured(
                prompt=prompt,
                response_model=GoalInterpretation,
            )
        except ValidationError as err:
            return GoalIntelligenceResult(
                interpretation=GoalInterpretation(
                    target_role="Unspecified",
                    objective=prompt,
                ),
                resolved_role=await self.role_resolver.resolve_role("Unspecified"),
                resolved_skills=await self.skill_resolver.resolve_skills([]),
                validation_status="invalid",
                is_valid=False,
                validation_errors=[f"Schema validation failed: {str(err)}"],
            )
        except Exception as err:
            return GoalIntelligenceResult(
                interpretation=GoalInterpretation(
                    target_role="Unspecified",
                    objective=prompt,
                ),
                resolved_role=await self.role_resolver.resolve_role("Unspecified"),
                resolved_skills=await self.skill_resolver.resolve_skills([]),
                validation_status="invalid",
                is_valid=False,
                validation_errors=[f"LLM provider generation failed: {str(err)}"],
            )

        # 2. Resolve target role deterministically
        resolved_role = await self.role_resolver.resolve_role(interpretation.target_role)
        if not resolved_role.is_resolved:
            validation_errors.append(
                resolved_role.ambiguity_reason
                or f"Unresolved target role: '{interpretation.target_role}'."
            )

        # 3. Resolve stated skills deterministically
        resolved_skills = await self.skill_resolver.resolve_skills(
            interpretation.stated_existing_skills
        )

        # 4. Check interpretation ambiguity flags
        if interpretation.ambiguities:
            for amb in interpretation.ambiguities:
                validation_errors.append(f"Ambiguity noted: {amb}")

        # 5. Compute overall validity status
        is_valid = resolved_role.is_resolved and len(validation_errors) == 0
        if is_valid:
            status = "valid"
        elif not resolved_role.is_resolved:
            status = "invalid"
        else:
            status = "ambiguous"

        return GoalIntelligenceResult(
            interpretation=interpretation,
            resolved_role=resolved_role,
            resolved_skills=resolved_skills,
            validation_status=status,
            is_valid=is_valid,
            validation_errors=validation_errors,
        )

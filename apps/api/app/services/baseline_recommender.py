from typing import Any
from uuid import UUID

from pydantic import BaseModel


class BaselineRecommendationItem(BaseModel):
    rank: int
    resource_id: str
    title: str
    target_skill_id: str
    target_skill_name: str
    relevance_score: float
    estimated_minutes: int


class BaselineRecommendationResponse(BaseModel):
    learner_id: str
    target_role: str
    recommendations: list[BaselineRecommendationItem]
    total_estimated_minutes: int


class BaselineRecommendationEngine:
    """Conventional relevance-based course recommender.

    Recommends resources strictly based on resource-role/skill relevance metadata
    without taking into account learner mastery, bottleneck analysis, prerequisite
    dependencies, proof of mastery, or dynamic replanning.
    """

    def recommend(
        self,
        learner_id: UUID | str,
        target_role: str,
        resource_catalog: list[dict[str, Any]],
        max_minutes: int | None = None,
    ) -> BaselineRecommendationResponse:
        """Rank and return resources ordered by static relevance score alone."""
        # Sort catalog purely by static relevance score descending
        sorted_resources = sorted(
            resource_catalog,
            key=lambda r: float(r.get("relevance_score", 0.5)),
            reverse=True,
        )

        items: list[BaselineRecommendationItem] = []
        accumulated_minutes = 0

        for rank, r in enumerate(sorted_resources, start=1):
            duration = int(r.get("estimated_minutes", r.get("duration_minutes", 30)))
            if max_minutes is not None and accumulated_minutes + duration > max_minutes:
                continue

            items.append(
                BaselineRecommendationItem(
                    rank=rank,
                    resource_id=str(r.get("id", f"res-{rank}")),
                    title=str(r.get("title", f"Resource {rank}")),
                    target_skill_id=str(r.get("target_skill_id", "skill-0")),
                    target_skill_name=str(r.get("target_skill_name", "General Skill")),
                    relevance_score=float(r.get("relevance_score", 0.5)),
                    estimated_minutes=duration,
                )
            )
            accumulated_minutes += duration

        return BaselineRecommendationResponse(
            learner_id=str(learner_id),
            target_role=target_role,
            recommendations=items,
            total_estimated_minutes=accumulated_minutes,
        )

from collections import deque
from typing import NamedTuple
from uuid import UUID

from app.models.skill_relation import SkillRelation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

RELATION_WEIGHTS: dict[str, float] = {
    "prerequisite": 1.0,
    "supports": 0.5,
    "related": 0.0,
}


class Edge(NamedTuple):
    target_id: UUID
    relation_type: str
    strength: float


class DependencyImpactResult(NamedTuple):
    impact_score: float
    downstream_skill_ids: list[UUID]
    downstream_skill_names: list[str]


class DependencyImpactService:
    """Service for traversing directed skill graphs and computing weighted downstream dependency impact."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def compute_dependency_impacts(
        self,
        target_skill_ids: list[UUID],
        role_importance_map: dict[UUID, float],
    ) -> dict[UUID, DependencyImpactResult]:
        # 1. Fetch all skill relations where source is in target_skill_ids
        stmt = select(SkillRelation).options(
            selectinload(SkillRelation.source_skill),
            selectinload(SkillRelation.target_skill),
        )
        res = await self.session.execute(stmt)
        all_relations = res.scalars().all()

        # Build adjacency graph: source_id -> list[Edge]
        graph: dict[UUID, list[Edge]] = {}
        skill_names: dict[UUID, str] = {}

        for rel in all_relations:
            if rel.source_skill:
                skill_names[rel.source_skill_id] = rel.source_skill.name
            if rel.target_skill:
                skill_names[rel.target_skill_id] = rel.target_skill.name

            graph.setdefault(rel.source_skill_id, []).append(
                Edge(
                    target_id=rel.target_skill_id,
                    relation_type=rel.relation_type.lower(),
                    strength=rel.strength,
                )
            )

        # 2. Compute impact for each candidate skill
        results: dict[UUID, DependencyImpactResult] = {}
        for candidate_id in target_skill_ids:
            results[candidate_id] = self._traverse_downstream(
                candidate_id=candidate_id,
                graph=graph,
                skill_names=skill_names,
                role_importance_map=role_importance_map,
            )

        return results

    def _traverse_downstream(
        self,
        candidate_id: UUID,
        graph: dict[UUID, list[Edge]],
        skill_names: dict[UUID, str],
        role_importance_map: dict[UUID, float],
    ) -> DependencyImpactResult:
        visited: set[UUID] = {candidate_id}
        queue: deque[tuple[UUID, int, float]] = deque([(candidate_id, 0, 1.0)])

        impact_sum: float = 1.0  # Base self impact
        downstream_ids: list[UUID] = []
        downstream_names: list[str] = []

        while queue:
            current_id, depth, accumulated_weight = queue.popleft()

            for edge in graph.get(current_id, []):
                rel_weight = RELATION_WEIGHTS.get(edge.relation_type, 0.0)
                if rel_weight <= 0.0:
                    continue

                if edge.target_id not in visited:
                    visited.add(edge.target_id)
                    next_depth = depth + 1
                    target_importance = role_importance_map.get(edge.target_id, 0.5)

                    # Weighted impact decays with depth
                    depth_decay = 0.75 ** (next_depth - 1)
                    contribution = rel_weight * target_importance * edge.strength * depth_decay
                    impact_sum += contribution

                    downstream_ids.append(edge.target_id)
                    t_name = skill_names.get(edge.target_id, str(edge.target_id)[:8])
                    if t_name not in downstream_names:
                        downstream_names.append(t_name)

                    queue.append((edge.target_id, next_depth, contribution))

        return DependencyImpactResult(
            impact_score=round(impact_sum, 4),
            downstream_skill_ids=downstream_ids,
            downstream_skill_names=downstream_names,
        )

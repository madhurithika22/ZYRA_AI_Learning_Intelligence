import asyncio
import os
import sys
import time
from pathlib import Path

root_path = Path(__file__).resolve().parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

api_path = root_path / "apps" / "api"
if str(api_path) not in sys.path:
    sys.path.insert(0, str(api_path))

import dotenv
dotenv.load_dotenv(root_path / "apps" / "api" / ".env")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.models.learner import Learner
from app.models.goal import Goal
from app.services.baseline_recommender import BaselineRecommendationEngine
from app.services.bottleneck_analysis import BottleneckAnalysisService
from app.services.next_action_service import NextActionService
from app.services.learning_twin_service import LearningTwinService
from app.services.replanning_service import ReplanningService


def calc_stats(latencies: list[float]) -> dict[str, float]:
    sorted_lats = sorted(latencies)
    n = len(sorted_lats)
    median = sorted_lats[n // 2]
    p95_idx = int(n * 0.95)
    p95 = sorted_lats[min(p95_idx, n - 1)]
    max_val = sorted_lats[-1]
    return {"median": median, "p95": p95, "max": max_val}


async def benchmark_operation(func, reps=10) -> dict[str, float]:
    latencies: list[float] = []
    for _ in range(reps):
        t0 = time.perf_counter()
        await func()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # ms

    return calc_stats(latencies)


async def main():
    print("==================================================")
    print("PHASE 13 PERFORMANCE BENCHMARK SUITE")
    print("==================================================")

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://adaptive_learning:adaptive_learning_dev@127.0.0.1:5432/adaptive_learning",
    )
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    baseline_engine = BaselineRecommendationEngine()
    catalog = [
        {"id": f"res-{i}", "title": f"Resource {i}", "target_skill_id": f"sk-{i}", "relevance_score": 0.8, "duration_minutes": 30}
        for i in range(10)
    ]

    # Baseline Latency
    t0 = time.perf_counter()
    for _ in range(50):
        baseline_engine.recommend("benchmark-learner", "ML Engineer", catalog)
    t1 = time.perf_counter()
    baseline_ms = ((t1 - t0) / 50.0) * 1000.0

    print(f"\n1. Baseline Recommendation Engine Latency: {baseline_ms:.2f} ms")

    async with session_factory() as session:
        alex = (await session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()
        alex_goal = (await session.execute(select(Goal).where(Goal.learner_id == alex.id))).scalars().first()

        bottleneck_service = BottleneckAnalysisService(session)
        next_action_service = NextActionService(session)
        twin_service = LearningTwinService(session)
        replanning_service = ReplanningService(session)

        # 2. Bottleneck Analysis
        if alex_goal:
            bn_stats = await benchmark_operation(lambda: bottleneck_service.analyze_bottlenecks(alex.id, alex_goal.id), reps=10)
            print(f"\n2. Bottleneck Analysis Service:")
            print(f"   Median: {bn_stats['median']:.2f} ms | p95: {bn_stats['p95']:.2f} ms | Max: {bn_stats['max']:.2f} ms")

        # 3. Next Action Determination
        na_stats = await benchmark_operation(lambda: next_action_service.get_next_action(alex.id), reps=10)
        print(f"\n3. Next Action Intelligence Service:")
        print(f"   Median: {na_stats['median']:.2f} ms | p95: {na_stats['p95']:.2f} ms | Max: {na_stats['max']:.2f} ms")

        # 4. Learning Twin State Query
        twin_stats = await benchmark_operation(lambda: twin_service.get_learning_twin(alex.id), reps=10)
        print(f"\n4. Learning Twin Service:")
        print(f"   Median: {twin_stats['median']:.2f} ms | p95: {twin_stats['p95']:.2f} ms | Max: {twin_stats['max']:.2f} ms")

        # 5. Replanning Evaluation
        if alex_goal:
            replan_stats = await benchmark_operation(lambda: replanning_service.get_replan_status(alex.id, alex_goal.id), reps=10)
            print(f"\n5. Replanning Engine Evaluation:")
            print(f"   Median: {replan_stats['median']:.2f} ms | p95: {replan_stats['p95']:.2f} ms | Max: {replan_stats['max']:.2f} ms")

    print("\n==================================================")
    print("PERFORMANCE BENCHMARK COMPLETE")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())

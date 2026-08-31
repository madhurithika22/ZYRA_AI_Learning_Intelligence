import asyncio
import os
import sys
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
from app.models.skill import Skill
from app.models.skill_mastery import SkillMastery


async def main():
    print("==================================================")
    print("DEMO STATE RESET SCRIPT")
    print("==================================================")

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://adaptive_learning:adaptive_learning_dev@127.0.0.1:5432/adaptive_learning",
    )
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        alex = (await session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one_or_none()
        if not alex:
            print("Alex Chen record not found. Seeding database...")
            from scripts.seed_database import seed_all
            await seed_all()
            print("Database seeded.")
            return

        print("Resetting Alex Chen's skill mastery values to baseline demo state...")
        skills = (await session.execute(select(Skill))).scalars().all()
        for sk in skills:
            sm = (await session.execute(
                select(SkillMastery).where(SkillMastery.learner_id == alex.id, SkillMastery.skill_id == sk.id)
            )).scalar_one_or_none()

            if sm:
                if sk.name == "Python":
                    sm.mastery_score = 0.90
                    sm.confidence = 0.95
                elif sk.name in ("Machine Learning", "Deep Learning"):
                    sm.mastery_score = 0.20
                    sm.confidence = 0.40
                elif sk.name == "PyTorch":
                    sm.mastery_score = 0.25
                    sm.confidence = 0.30
                elif sk.name in ("MLOps", "Model Deployment"):
                    sm.mastery_score = 0.15
                    sm.confidence = 0.30

        await session.commit()
        print("Demo state reset successfully.")

    print("\n==================================================")
    print("DEMO RESET COMPLETE")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text

from app.api.v1.app_state import router as app_state_router
from app.api.v1.auth import router as auth_router
from app.api.v1.bottlenecks import router as bottlenecks_router
from app.api.v1.conversation import router as conversation_router
from app.api.v1.diagnostics import router as diagnostics_router
from app.api.v1.goal_intelligence import router as goal_intelligence_router
from app.api.v1.learning_activities import router as learning_activities_router
from app.api.v1.learning_paths import router as learning_paths_router
from app.api.v1.learning_twin import router as learning_twin_router
from app.api.v1.mastery_checks import router as mastery_checks_router
from app.api.v1.next_action import router as next_action_router
from app.api.v1.profile import router as profile_router
from app.api.v1.progress import router as progress_router
from app.api.v1.replanning import router as replanning_router
from app.core.database import AsyncSessionLocal
from app.models.assessment import Assessment
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.learning_path import LearningPath
from app.models.learning_resource import LearningResource
from app.models.role import Role
from app.models.skill import Skill

app = FastAPI(
    title="Adaptive Learning Intelligence Engine",
    version="0.1.0",
    description="Outcome-driven adaptive learning intelligence platform.",
)

# Configure CORS for local web clients
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://zyra-ai-learning-intelligence.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth_router, prefix="/api")
app.include_router(app_state_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api")
app.include_router(goal_intelligence_router, prefix="/api")
app.include_router(diagnostics_router, prefix="/api")
app.include_router(bottlenecks_router, prefix="/api")
app.include_router(learning_paths_router, prefix="/api")
app.include_router(learning_activities_router, prefix="/api")
app.include_router(mastery_checks_router, prefix="/api")
app.include_router(progress_router, prefix="/api")
app.include_router(next_action_router, prefix="/api")
app.include_router(replanning_router, prefix="/api")
app.include_router(learning_twin_router, prefix="/api")
app.include_router(conversation_router, prefix="/api")


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    """Return basic API information."""
    return {
        "name": "Adaptive Learning Intelligence Engine",
        "version": "0.1.0",
        "status": "ok",
    }


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    """Return application health status."""
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))

    return {"status": "healthy"}


@app.get("/health/database", tags=["system"])
async def database_health() -> dict[str, str]:
    """Verify PostgreSQL connectivity."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT current_database(), current_user"))

    database, user = result.one()

    return {
        "status": "healthy",
        "database": database,
        "user": user,
    }


@app.get("/health/domain", tags=["system"])
async def domain_health() -> dict[str, str | dict[str, int]]:
    """Verify domain database persistence and return entity counts."""
    async with AsyncSessionLocal() as session:
        learners_cnt = (
            await session.execute(select(func.count()).select_from(Learner))
        ).scalar() or 0
        roles_cnt = (await session.execute(select(func.count()).select_from(Role))).scalar() or 0
        skills_cnt = (await session.execute(select(func.count()).select_from(Skill))).scalar() or 0
        goals_cnt = (await session.execute(select(func.count()).select_from(Goal))).scalar() or 0
        paths_cnt = (
            await session.execute(select(func.count()).select_from(LearningPath))
        ).scalar() or 0
        resources_cnt = (
            await session.execute(select(func.count()).select_from(LearningResource))
        ).scalar() or 0
        assessments_cnt = (
            await session.execute(select(func.count()).select_from(Assessment))
        ).scalar() or 0

    return {
        "status": "healthy",
        "counts": {
            "learners": learners_cnt,
            "roles": roles_cnt,
            "skills": skills_cnt,
            "goals": goals_cnt,
            "learning_paths": paths_cnt,
            "learning_resources": resources_cnt,
            "assessments": assessments_cnt,
        },
    }

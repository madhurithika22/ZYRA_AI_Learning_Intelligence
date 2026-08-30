from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from app.core.settings import DATABASE_URL
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture(autouse=True)
def enforce_test_llm_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure all automated tests use MockLLMProvider by default with ZERO network calls."""
    monkeypatch.setenv("LLM_PRIMARY_PROVIDER", "mock")
    monkeypatch.setenv("LLM_PROVIDER", "mock")


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database session that rolls back after each test."""
    test_engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
    )

    import sys
    from pathlib import Path
    root_path = Path(__file__).resolve().parent.parent.parent.parent
    if str(root_path) not in sys.path:
        sys.path.insert(0, str(root_path))

    from app.models.base import Base
    from scripts.seed_database import seed_all

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as session:
            # Check if database is seeded
            from app.models.learner import Learner
            from sqlalchemy import select
            res = await session.execute(select(Learner))
            if not res.scalars().first():
                await seed_all()

            try:
                yield session
            finally:
                if transaction.is_active:
                    await transaction.rollback()

    await test_engine.dispose()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX AsyncClient bound to FastAPI app with test db session dependency override."""
    from app.core.database import get_db_session
    from app.main import app
    from httpx import ASGITransport, AsyncClient

    async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

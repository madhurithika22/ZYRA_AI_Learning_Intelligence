import pytest
from app.core.security import create_session_token, hash_password
from app.models.goal import Goal
from app.models.learner import Learner
from app.models.user_account import UserAccount
from httpx import AsyncClient
from sqlalchemy import select


@pytest.mark.asyncio
async def test_get_app_state_unauthenticated(async_client: AsyncClient):
    response = await async_client.get("/api/v1/learners/me/state")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_app_state_new_user_returns_goal_required(
    async_client: AsyncClient, db_session
):
    # 1. Create a fresh learner and user account
    learner = Learner(display_name="State Test Learner", email="statetest@example.com")
    db_session.add(learner)
    await db_session.flush()

    user = UserAccount(
        learner_id=learner.id,
        email="statetest@example.com",
        password_hash=hash_password("Password123!"),
        display_name="State Test Learner",
    )
    db_session.add(user)
    await db_session.commit()

    token = create_session_token(str(user.id), str(learner.id), user.email)
    async_client.cookies.set("session_id", token)

    # 2. Fetch App State
    response = await async_client.get("/api/v1/learners/me/state")
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "GOAL_REQUIRED"
    assert data["next_action_label"] == "Define My Goal"
    assert data["next_action_route"] == "goal"


@pytest.mark.asyncio
async def test_get_app_state_goal_created_returns_diagnostic_required(
    async_client: AsyncClient, db_session
):
    learner = Learner(display_name="Goal State Learner", email="goalstate@example.com")
    db_session.add(learner)
    await db_session.flush()

    user = UserAccount(
        learner_id=learner.id,
        email="goalstate@example.com",
        password_hash=hash_password("Password123!"),
        display_name="Goal State Learner",
    )
    db_session.add(user)

    from app.models.role import Role
    res = await db_session.execute(select(Role))
    role = res.scalars().first()
    if not role:
        role = Role(name="State Test Role")
        db_session.add(role)
        await db_session.flush()

    goal = Goal(
        learner_id=learner.id,
        target_role_id=role.id,
        objective="I want to become an AI Engineer",
    )
    db_session.add(goal)
    await db_session.commit()

    token = create_session_token(str(user.id), str(learner.id), user.email)
    async_client.cookies.set("session_id", token)

    response = await async_client.get("/api/v1/learners/me/state")
    assert response.status_code == 200
    data = response.json()
    assert data["stage"] == "DIAGNOSTIC_REQUIRED"
    assert data["next_action_label"] == "Start Diagnostic"
    assert data["next_action_route"] == "diagnostic"
    assert data["goal_id"] == str(goal.id)

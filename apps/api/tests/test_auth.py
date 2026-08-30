from uuid import uuid4

import pytest
from app.core.security import hash_password, verify_password
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_password_hashing_security():
    password = "SuperSecretPassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert "pbkdf2_sha256" in hashed
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


@pytest.mark.asyncio
async def test_register_and_get_me(async_client: AsyncClient):
    email = f"test_user_{uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "Password123!",
        "display_name": "Test User",
    }

    # 1. Register
    reg_res = await async_client.post("/api/v1/auth/register", json=payload)
    assert reg_res.status_code == 201, reg_res.text
    data = reg_res.json()
    assert data["email"] == email
    assert data["display_name"] == "Test User"
    assert "learner_id" in data
    assert "user_id" in data
    assert "password_hash" not in data

    # 2. Get Me
    me_res = await async_client.get("/api/v1/auth/me")
    assert me_res.status_code == 200, me_res.text
    me_data = me_res.json()
    assert me_data["email"] == email
    assert me_data["learner_id"] == data["learner_id"]


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(async_client: AsyncClient):
    email = f"dup_user_{uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "password": "Password123!",
        "display_name": "Duplicate Test",
    }
    res1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_login_and_logout(async_client: AsyncClient):
    email = f"login_user_{uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"
    reg_payload = {
        "email": email,
        "password": password,
        "display_name": "Login User",
    }
    await async_client.post("/api/v1/auth/register", json=reg_payload)

    # 1. Logout
    logout_res = await async_client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200

    # 2. Try auth me after logout -> 401
    me_res1 = await async_client.get("/api/v1/auth/me")
    assert me_res1.status_code == 401

    # 3. Login with invalid password -> 401
    bad_login = await async_client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword"})
    assert bad_login.status_code == 401
    assert bad_login.json()["detail"] == "Email or password is incorrect."

    # 4. Login with valid password -> 200
    good_login = await async_client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert good_login.status_code == 200
    assert good_login.json()["email"] == email

    # 5. Me after login -> 200
    me_res2 = await async_client.get("/api/v1/auth/me")
    assert me_res2.status_code == 200


@pytest.mark.asyncio
async def test_user_isolation_user_a_cannot_access_user_b(async_client: AsyncClient):
    # Create User A
    email_a = f"user_a_{uuid4().hex[:8]}@example.com"
    reg_a = await async_client.post("/api/v1/auth/register", json={
        "email": email_a,
        "password": "PasswordA123!",
        "display_name": "User A",
    })
    learner_a_id = reg_a.json()["learner_id"]

    # Logout User A
    await async_client.post("/api/v1/auth/logout")

    # Create User B
    email_b = f"user_b_{uuid4().hex[:8]}@example.com"
    reg_b = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email_b,
            "password": "PasswordB123!",
            "display_name": "User B",
        },
    )
    assert reg_b.status_code == 201

    # As User B, try to access User A's learning twin / progress / goals -> 404 Not Found
    res_twin = await async_client.get(f"/api/v1/learners/{learner_a_id}/learning-twin")
    assert res_twin.status_code == 404

    res_progress = await async_client.get(f"/api/v1/learners/{learner_a_id}/progress")
    assert res_progress.status_code == 404

    res_next_action = await async_client.get(f"/api/v1/learners/{learner_a_id}/next-action")
    assert res_next_action.status_code == 404

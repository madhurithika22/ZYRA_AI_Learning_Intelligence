import asyncio
from uuid import uuid4

import httpx

BASE_URL = "http://127.0.0.1:8000"

async def test_live_auth():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Unauthenticated GET /auth/me -> 401
        r = await client.get("/api/v1/auth/me")
        print("1. Unauthenticated /auth/me status:", r.status_code)
        assert r.status_code == 401

        # 2. Register User A
        email_a = f"alpha_{uuid4().hex[:6]}@example.com"
        reg_a = await client.post("/api/v1/auth/register", json={
            "email": email_a,
            "password": "Password123!",
            "display_name": "Learner Alpha",
        })
        print("2. Register User A status:", reg_a.status_code, reg_a.json())
        assert reg_a.status_code == 201
        data_a = reg_a.json()
        learner_a_id = data_a["learner_id"]

        # 3. GET /auth/me as User A -> 200
        me_a = await client.get("/api/v1/auth/me")
        print("3. GET /auth/me User A status:", me_a.status_code, me_a.json()["email"])
        assert me_a.status_code == 200
        assert me_a.json()["email"] == email_a

        # 4. Create Goal for User A
        goal_a = await client.post(f"/api/v1/learners/{learner_a_id}/goals", json={
            "natural_language_goal": "I want to become a Machine Learning Engineer in 6 months."
        })
        data_goal_a = goal_a.json()
        assert "goal_id" in data_goal_a or "id" in data_goal_a

        # 5. Logout User A
        logout_a = await client.post("/api/v1/auth/logout")
        print("5. Logout User A status:", logout_a.status_code)
        assert logout_a.status_code == 200

        # 6. GET /auth/me after logout -> 401
        me_logout = await client.get("/api/v1/auth/me")
        print("6. GET /auth/me after logout status:", me_logout.status_code)
        assert me_logout.status_code == 401

        # 7. Register User B
        email_b = f"beta_{uuid4().hex[:6]}@example.com"
        reg_b = await client.post("/api/v1/auth/register", json={
            "email": email_b,
            "password": "Password123!",
            "display_name": "Learner Beta",
        })
        print("7. Register User B status:", reg_b.status_code, reg_b.json())
        assert reg_b.status_code == 201
        data_b = reg_b.json()
        learner_b_id = data_b["learner_id"]

        # 8. Attempt as User B to access User A's learning twin -> 404
        twin_access = await client.get(f"/api/v1/learners/{learner_a_id}/learning-twin")
        print("8. User B accessing User A twin status:", twin_access.status_code)
        assert twin_access.status_code == 404

        # 9. Create Goal for User B
        goal_b = await client.post(f"/api/v1/learners/{learner_b_id}/goals", json={
            "natural_language_goal": "I want to become an AI Engineer in 6 months."
        })
        print("9. Create Goal User B status:", goal_b.status_code, "JSON:", goal_b.json())
        assert goal_b.status_code == 201

        # 10. User B fetches their twin -> 200 OK
        twin_b = await client.get(f"/api/v1/learners/{learner_b_id}/learning-twin")
        print("10. User B twin status:", twin_b.status_code, "JSON:", twin_b.json())
        assert twin_b.status_code == 200

        # 11. Logout User B and login as User A
        await client.post("/api/v1/auth/logout")
        login_a = await client.post("/api/v1/auth/login", json={"email": email_a, "password": "Password123!"})
        print("11. Login User A status:", login_a.status_code)
        assert login_a.status_code == 200

        # 12. User A fetches their twin -> 200 OK
        twin_a = await client.get(f"/api/v1/learners/{learner_a_id}/learning-twin")
        print("12. User A twin status:", twin_a.status_code, "JSON:", twin_a.json())
        assert twin_a.status_code == 200

        print("\nALL LIVE E2E AUTH & MULTI-USER ISOLATION CHECKS PASSED EMPIRICALLY!")

if __name__ == "__main__":
    asyncio.run(test_live_auth())

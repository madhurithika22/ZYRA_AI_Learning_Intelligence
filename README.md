# Adaptive Learning Intelligence Engine

An outcome-driven adaptive learning platform that continuously determines what a learner should learn next based on demonstrated knowledge, target outcomes, constraints, and learning evidence.

## Core Concept

The system is designed around the following loop:

Assess → Diagnose → Plan → Learn → Prove → Update → Adapt → Replan

---

## Phase 3: Goal Intelligence & Learner Profiling

Phase 3 introduces the first intelligent learner-facing workflow: natural language goal interpretation, structured parameter extraction, deterministic target-role and stated-skill resolution, learner profile persistence, and an interactive Goal Setup UI.

### Key Components Implemented

1. **LLM Provider Abstraction (`app/providers/llm/`)**:
   - Interface `LLMProvider` defining `generate_structured(prompt, model)`.
   - `MockLLMProvider`: Deterministic mock for test isolation and offline runs without requiring an API key.
   - `OpenAIProvider`: Configurable real provider adapter using structured JSON output.
   - Provider factory `get_llm_provider()` reading `LLM_PROVIDER` environment variable (defaults to `mock`).

2. **Goal Intelligence & Validation (`app/schemas/goal_intelligence.py` & `app/services/goal_intelligence_service.py`)**:
   - Extracts structured parameters (`target_role`, `objective`, `timeline_weeks`, `daily_minutes`, `desired_outcome`, `constraints`, `stated_existing_skills`, `ambiguities`, `confidence`).
   - Validates strict numerical bounds (`timeline_weeks > 0`, `0 < daily_minutes <= 1440`, `0 <= confidence <= 1.0`).

3. **Deterministic Role Resolution (`app/services/role_resolution.py`)**:
   - Normalizes casing, whitespace, and matches aliases (e.g., "machine learning engineer" → canonical `ML Engineer`).
   - Flags unresolved or ambiguous target roles explicitly without inventing arbitrary database `Role` entities.

4. **Stated Skill Resolution (`app/services/skill_resolution.py`)**:
   - Matches learner-stated skill phrases against canonical `Skill` entities.
   - Stores stated skills as learner profile background metadata—NOT as `SkillMastery` records (self-claims are not mastery evidence).

5. **Learner Profile & Transactional Persistence (`app/models/learner_profile.py` & `app/services/goal_creation_service.py`)**:
   - Dedicated `LearnerProfile` table (`learner_id`, `experience_level`, `preferred_learning_mode`, `weekly_availability_hours`, `stated_background`, `profile_metadata`).
   - Transactional `GoalCreationService` that commits `Goal` and `LearnerProfile` atomically or rolls back completely if validation or role resolution fails.

6. **FastAPI Endpoints (`app/api/v1/goal_intelligence.py`)**:
   - `POST /api/v1/goal-intelligence/interpret`: Pure goal extraction, validation, and resolution.
   - `POST /api/v1/learners/{learner_id}/goals`: End-to-end interpret, validate, resolve, and persist flow.
   - `GET /api/v1/learners/{learner_id}/profile`: Profile & goal retrieval.

7. **Next.js Goal Setup UI (`apps/web/src/app/page.tsx`)**:
   - Interactive Goal Setup interface allowing learners to submit natural language goals, review AI interpretation vs Learner-provided facts vs Ambiguities, and persist goals to PostgreSQL.

---

## Local Development & Operations

### Environment Configuration
Copy `.env.example` to `apps/api/.env`:

```env
DATABASE_URL=postgresql+asyncpg://adaptive_learning:adaptive_learning_dev@127.0.0.1:5432/adaptive_learning
LLM_PROVIDER=mock
```

### Database Migrations
From `apps/api`:

```powershell
.venv\Scripts\alembic.exe current
.venv\Scripts\alembic.exe upgrade head
.venv\Scripts\alembic.exe check
```

### Automated Tests & Quality Checks
From `apps/api`:

```powershell
# Run 25 automated backend tests (Phase 2 & Phase 3)
.venv\Scripts\pytest.exe

# Run linting check
.venv\Scripts\ruff.exe check .

# Run static type check
.venv\Scripts\mypy.exe app
```

### API Backend Server
From `apps/api`:

```powershell
.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

### Frontend Web Server
From `apps/web`:

```powershell
npm run dev
```

Visit `http://localhost:3000` to interact with the Goal Setup UI.
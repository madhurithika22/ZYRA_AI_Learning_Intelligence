# Adaptive Learning Intelligence Engine

> An outcome-driven AI learning platform that builds a personalized **Learning Twin**, identifies skill gaps with evidence-based analysis, and continuously adapts your learning path toward a target career role.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

**[Overview](#-overview) · [Why This Project?](#-why-this-project) · [Features](#-features) · [Architecture](#-system-architecture) · [Learning Loop](#-adaptive-learning-loop) · [AI Engine](#-ai-architecture) · [Quick Start](#-quick-start) · [API](#-api-reference) · [Database](#-database) · [Testing](#-testing) · [Security](#-security) · [Roadmap](#-roadmap)**

---

## 📌 Overview

Most adaptive learning systems are just course catalogs with progress bars. This project is different.

The Adaptive Learning Intelligence Engine models each learner as a **Learning Twin** — a unified, deterministic computational representation of their current skill mastery, confidence, bottlenecks, active learning path, and next recommended action. Every recommendation is explainable, evidence-grounded, and reproducible.

The platform:

- Interprets a natural language career goal and resolves it to a structured **target role with required skills**
- Runs an **adaptive diagnostic** to estimate baseline skill mastery, selecting each question to maximize information gain
- Identifies the **primary learning bottleneck** — the skill gap with the highest downstream impact on the target role
- Generates **four strategy-optimized learning paths** for the learner to choose from
- Requires **post-activity proof of mastery** before crediting a skill as demonstrated
- Continuously detects mastery drift and triggers **dynamic path replanning** when the active path becomes stale
- Provides a **grounded AI assistant** that answers questions strictly from the learner's verified state

---

## 🎯 Why This Project?

Traditional learning platforms track content consumption. This platform tracks **demonstrated competency** and continuously adjusts based on what the learner actually knows.

| Traditional Learning Platform | Adaptive Learning Intelligence Engine |
|---|---|
| Static, pre-built learning paths | Dynamically generated and replanned paths |
| Completion-based progress (watched video = learned) | Evidence-based mastery (must prove understanding) |
| Generic content recommendations | Personalized next-best-action with scoring rationale |
| Fixed assessments in a fixed order | Adaptive diagnostics that maximize information gain |
| Basic chatbot with scripted replies | Grounded conversational AI anchored to verified learner state |
| Manual path changes | Automatic replanning on mastery drift or bottleneck shift |
| Course completion certificate | Verified proof of mastery per skill |
| No explanation for recommendations | Full decision trace: why this skill, why now, what evidence |

---

## ✨ Features

- **Goal Intelligence** — Converts a natural language goal into a resolved role and required skill set via Gemini LLM
- **Adaptive Diagnostic Engine** — Selects questions using uncertainty × skill importance × difficulty fit × coverage balance × novelty; terminates at 75% confidence or 10 questions
- **Incremental Mastery Engine** — Updates mastery using an evidence-weighted signal model with consistency bonuses; confidence tracked separately from mastery score
- **Bottleneck Analysis** — Ranks all skill gaps by `gap × role_importance × dependency_impact × uncertainty_factor`; identifies primary and secondary blockers
- **Learning Twin** — Real-time snapshot across 7 confidence dimensions with a full deterministic decision trace
- **Four Learning Path Strategies** — FASTEST (minimize time), BALANCED (breadth + depth), DEEP MASTERY (maximize confidence), PROJECT FIRST (applied-first)
- **Proof of Mastery** — Post-activity assessments that convert activity completion into verified, persisted skill evidence
- **Next-Best-Action Engine** — 7-weight scoring system recommending CONTINUE, LEARN, MASTERY\_CHECK, SKIP, REASSESS, PREREQUISITE\_REVIEW, or PROJECT
- **Dynamic Replanning** — Detects path node obsolescence, bottleneck resolution, and mastery drift; generates structured V\_k → V\_{k+1} diff with accept/reject workflow
- **Grounded Conversational Assistant** — Gemini-powered chat strictly grounded in verified learner state; filters hallucinated source references; prompt injection defense built in
- **Gamification** — XP, levels, daily streak, and achievement badges derived exclusively from real activity data
- **Multi-Key Gemini Router** — Up to 3 API keys with automatic 429 rotation and bounded cooldown per slot
- **Mock LLM Provider** — Full test isolation with zero network calls; deterministic output

---

## 🏗️ System Architecture

The architecture separates concerns into four distinct layers. Critically, **most of the intelligence runs without any LLM call** — only goal interpretation, answer evaluation (for open-ended questions), and conversational reasoning invoke Gemini.

```mermaid
flowchart TD
    subgraph Frontend["Frontend — Next.js 16 + React 19"]
        UI[SPA Views\nLearning Twin · Diagnostic · Path · Assistant]
        Auth[Auth Context\nHttpOnly Cookie Session]
    end

    subgraph APILayer["API Layer — FastAPI :8000"]
        Routes[14 Route Modules\n/api/v1/...]
        Deps[Dependency Injection\nSession Auth · DB Session]
    end

    subgraph Intelligence["Domain Intelligence Services"]
        direction LR
        subgraph LLMPowered["LLM-Powered (3 services)"]
            GoalSvc[Goal Intelligence\nLLM → Role + Skills]
            EvalSvc[Answer Evaluation\nLLM Rubric Scoring]
            ChatSvc[Conversational Assistant\nLLM + Context Grounding]
        end
        subgraph Deterministic["Deterministic (7 engines — zero LLM)"]
            DiagSvc[Adaptive Diagnostic\nQuestion Selection]
            MasterySvc[Mastery Engine\nEvidence Scoring]
            BnSvc[Bottleneck Analysis\nGap × Impact × Uncertainty]
            NextSvc[Next-Best-Action\n7-Weight Scoring]
            TwinSvc[Learning Twin\nUnified State Snapshot]
            PathSvc[Path Optimizer\n4 Strategy Generation]
            ReplanSvc[Dynamic Replanning\nDrift Detection + Diff]
        end
    end

    subgraph LLMLayer["LLM Layer — Google Gemini 2.5 Flash"]
        Router[GeminiKeyRouter\nUp to 3 keys · 429 Rotation]
        Mock[MockLLMProvider\nTests Only]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL 17\nDocker)]
        Alembic[Alembic\nMigrations]
    end

    UI --> Auth
    Auth -->|cookie session| Routes
    Routes --> Deps
    Deps --> Intelligence
    LLMPowered --> Router
    Router --> GoalSvc & EvalSvc & ChatSvc
    LLMPowered -.->|test env| Mock
    Intelligence --> PG
    Alembic --> PG
```

---

## 🔄 Adaptive Learning Loop

The platform operates as a continuous feedback cycle. Mastery evidence from every activity feeds back into the learning model and can trigger an automatic path adjustment.

```mermaid
flowchart LR
    A([Career Goal]) --> B[Goal Intelligence\nLLM interprets NL goal\n→ Role + Required Skills]
    B --> C[Self-Assessment\nBaseline confidence ratings]
    C --> D[Adaptive Diagnostic\nAdaptive question selection\nmaximising information gain]
    D --> E[Mastery Engine\nEvidence-weighted score update\n+ confidence estimation]
    E --> F[Learning Twin\nUnified learner-state snapshot\nacross 7 confidence dimensions]
    F --> G[Bottleneck Analysis\ngap × importance × dep_impact\n× uncertainty_factor]
    G --> H[Path Optimizer\n4 strategy-optimised candidates\nFASTEST · BALANCED · DEEP MASTERY · PROJECT FIRST]
    H --> I[Learner Selects Path\nActivated · V1]
    I --> J[Next-Best-Action Engine\n7-weight scored candidates\nCONTINUE · LEARN · MASTERY_CHECK\nSKIP · REASSESS · PROJECT]
    J --> K[Learning Activity\nStart → Draft → Complete]
    K --> L[Proof of Mastery\nPost-activity assessment\nRequired before skill credit]
    L --> E
    E --> M{Change Detection\nMastery delta ≥ 0.10?\nBottleneck shifted?\nNode obsolete?}
    M -->|Staleness ≥ 0.35| N[Dynamic Replanning\nGenerate V_k+1 diff\nAccept or Reject]
    N --> I
    M -->|Path still valid| J
    F --> O[Grounded Assistant\nLLM answers grounded\nin verified learner state]
```

---

## 🧠 Core Intelligence

### 1. Goal Intelligence
**Input:** Natural language string — e.g. *"I want to become a DevOps Engineer in 3 months"*
**Processing:** Gemini 2.5 Flash extracts target role, objective, timeline, stated skills, and ambiguities into a structured schema. A deterministic `RoleResolutionService` then matches the extracted role against the database catalog.
**Output:** Resolved `Role` with required `Skill` list and validation status (`valid` / `ambiguous` / `invalid`).
**Why it matters:** Learners rarely know how to articulate a structured goal. This converts intent into an actionable skill-gap target.

### 2. Adaptive Diagnostic Engine
**Input:** Diagnostic session, learner mastery state, target skill requirements.
**Processing:** Each question is scored by `uncertainty × skill_importance × difficulty_fit × novelty × coverage_balance`. The highest-scoring unasked question is selected next. Session terminates when confidence reaches 0.75 across target skills or 10 questions are answered.
**Output:** Updated `SkillMastery` and `SkillEvidence` records per answered question.
**Why it matters:** Avoids wasting time on questions the learner clearly knows or clearly doesn't know.

### 3. Mastery Engine
**Input:** Answered question, its difficulty (1.0–5.0), evaluation result (is\_correct, confidence, rubric coverage).
**Processing:** Difficulty-normalized signal calculation. Correct answer: `signal = 0.70 + 0.30 × norm_difficulty`. Incorrect: `signal = 0.30 × norm_difficulty`. Evidence weight decreases as prior confidence grows: `weight = evidence_strength × (1.0 − prior_confidence × 0.5) × 0.40`. Consistency bonuses applied when result aligns with current mastery direction.
**Output:** Updated mastery score ∈ [0.0, 1.0] and confidence ∈ [0.0, 1.0].
**Why it matters:** Mastery and confidence evolve independently, making the system resilient to single flawed responses and honest about estimation uncertainty.

### 4. Bottleneck Analysis
**Input:** All target role skills, learner mastery records, skill prerequisite dependency graph.
**Processing:** For each skill, computes `bottleneck_score = gap × role_importance × dependency_impact × uncertainty_factor`. Dependencies propagated via `DependencyImpactService`. Skills sorted deterministically by descending bottleneck score.
**Output:** Ranked `SkillGapItem` list with classifications (critical / high / moderate / low / insufficient\_evidence) and human-readable explanations.
**Why it matters:** Not all skill gaps are equal. A gap in a foundational skill that blocks 5 downstream skills is far more critical than an isolated gap.

### 5. Learning Twin
**Input:** Learner ID — orchestrates all domain services.
**Processing:** Composes a unified snapshot from Progress, Bottleneck, NextAction, and Replanning services. Evaluates state completeness across 7 dimensions (goal, role, skills, evidence, path, bottleneck, next action) and derives a confidence level (HIGH ≥ 85%, MEDIUM ≥ 50%, LOW < 50%). Builds a structured decision trace explaining every output field.
**Output:** `LearningTwinResponse` — a single object containing goal summary, skill matrix, path health, bottleneck, next action, replan status, evidence summary, state confidence, and decision trace.
**Why it matters:** Provides a single source of truth for the frontend and eliminates data inconsistency between views.

### 6. Learning Path Optimizer
**Input:** Learner goal, target skills, bottleneck analysis, skill resources.
**Processing:** Generates 4 candidates — FASTEST (fewest nodes, highest mastery skills skipped), BALANCED (mixed depth), DEEP\_MASTERY (all skills covered with high confidence targets), PROJECT\_FIRST (applied projects sequenced before theory). Each path is sequenced by prerequisite dependencies.
**Output:** `PathComparisonResponse` with 4 `PathStrategyOption` objects, each with an ordered node list.
**Why it matters:** Different learners have different constraints; offering four strategies respects time, depth, and learning-style preferences.

### 7. Next-Best-Action Engine
**Input:** Learner state, active path, skill mastery, bottleneck analysis.
**Processing:** Generates candidate actions (CONTINUE, LEARN, MASTERY\_CHECK, SKIP, REASSESS, PREREQUISITE\_REVIEW, PROJECT). Scores each across 7 weighted dimensions: gap reduction, bottleneck relevance, information value, prerequisite value, path progress, evidence value, practical value — minus time cost, redundancy, and repetition penalty. Ties broken deterministically by action type priority then title.
**Output:** `NextActionResponse` — selected action with score, rationale, constraints considered, tradeoffs, and up to 2 alternatives.
**Why it matters:** Answers the hardest question in self-directed learning: *"What should I do right now?"*

### 8. Proof of Mastery
**Input:** Completed activity attempt, post-activity assessment questions.
**Processing:** Learner answers are evaluated via `LLMEvaluator` (open-ended) or `DeterministicEvaluator` (multiple choice). Passed checks write `MasteryOutcome` and `SkillEvidence` records. Activity completion alone does **not** update mastery.
**Output:** `ProofOfMasteryOutcomeResponse` with updated mastery state and evidence record.
**Why it matters:** Prevents the common failure mode of passive content consumption counting as demonstrated competency.

### 9. Dynamic Replanning
**Input:** Active path, learner mastery state, bottleneck analysis.
**Processing:** `ChangeDetectionService` evaluates three triggers: (A) future path node obsolete — skill already mastered; (B) primary bottleneck resolved or shifted to a different skill; (C) material mastery delta ≥ 0.10 across target skills. Staleness score aggregated; replanning triggered at ≥ 0.35. When triggered, a new path draft (V\_{k+1}) is generated and diffed against V\_k.
**Output:** `ReplanStatusResponse` with staleness score, trigger type, rationale, and optional draft path. Learner can accept or reject.
**Why it matters:** Paths that were optimal at diagnostic time become suboptimal as mastery evolves. Without automatic correction, learners spend time on work they no longer need.

### 10. Grounded Conversational Assistant
**Input:** Learner question, conversation session.
**Processing:** `IntentClassifier` categorises the intent. `ContextBuilder` fetches the minimal verified learner state (goal, skills, bottleneck, next action, evidence) and serialises it into the Gemini prompt. Simple factual queries (e.g. "what is my mastery in X?") are answered deterministically without an LLM call. The LLM response is validated against an allowlist of source IDs before being returned.
**Output:** `MessageResponse` with answer, source references, confidence, limitations, and suggested follow-ups.
**Why it matters:** Prevents the assistant from fabricating mastery percentages, inventing resources, or providing advice inconsistent with the learner's actual state.

---

## 🧩 Decision-Making Pipeline

How the system determines what a learner should do next:

```mermaid
flowchart TD
    A[Learner State] --> B[Skill Mastery Records\nmastery_score ∈ 0.0–1.0]
    B --> C[Confidence Estimates\nconfidence ∈ 0.0–1.0]
    C --> D[Skill Gap Calculation\ngap = required_level − mastery_score]
    D --> E[Role Importance Weights\nper RoleSkill record]
    E --> F[Dependency Impact\nDependencyImpactService\ndownstream skill propagation]
    F --> G[Bottleneck Score\ngap × importance × dep_impact × uncertainty]
    G --> H[Active Learning Path State\nnode status · attempt history]
    H --> I[Candidate Action Generation\nCONTINUE · LEARN · MASTERY_CHECK\nSKIP · REASSESS · PREREQUISITE_REVIEW · PROJECT]
    I --> J[7-Weight Scoring\nGap Reduction 0.25\nBottleneck Relevance 0.25\nUncertainty 0.15\nPrerequisite Value 0.15\nPath Progress 0.10\nEvidence Value 0.10\nPractical Value 0.05\n− Time Cost 0.10\n− Redundancy 0.15\n− Repetition 0.20]
    J --> K[Deterministic Ranking\nScore → Bottleneck Relevance → Gap → Time → Action Priority]
    K --> L([Next Best Action\nWith rationale + constraints + tradeoffs])
```

---

## 📂 Project Structure

```text
adaptive-learning-ai/
│
├── apps/
│   ├── api/                    # FastAPI backend (Python 3.12)
│   │   ├── app/
│   │   │   ├── api/v1/         # 14 route modules (auth, diagnostics, paths, twin…)
│   │   │   ├── core/           # Database engine, security, settings
│   │   │   ├── models/         # 22 SQLAlchemy ORM models
│   │   │   ├── providers/llm/  # Gemini provider, multi-key router, mock
│   │   │   ├── schemas/        # Pydantic request/response schemas
│   │   │   └── services/       # 20+ domain intelligence services
│   │   │       └── conversation/ # Context builder, intent classifier, service
│   │   ├── alembic/            # 10 incremental database migrations
│   │   ├── tests/              # 18 pytest test modules
│   │   ├── requirements.txt
│   │   └── pyproject.toml      # Ruff, mypy, pytest configuration
│   │
│   └── web/                    # Next.js 16 frontend (TypeScript)
│       └── src/
│           ├── app/            # Root layout + single SPA entry page
│           ├── components/     # 20+ view components (Twin, Diagnostic, Path…)
│           └── lib/            # api.ts, auth.tsx, types.ts, theme.tsx
│
├── infra/
│   └── postgres/               # Docker Compose for PostgreSQL 17
│       └── docker-compose.yml
│
├── docs/                       # Feature design documents (12 files)
├── data/                       # Seed data directories (roles, skills, assessments)
├── evaluation/                 # Evaluation reports, metrics, scenarios
├── .env.example                # Root environment variable template
└── Makefile                    # make api-dev · make web-dev
```

**Key responsibilities:**

| Directory | Responsibility |
|---|---|
| `apps/api/app/api/v1/` | HTTP transport — request parsing, auth, response serialisation |
| `apps/api/app/services/` | All domain logic — no HTTP concerns, no direct SDK calls |
| `apps/api/app/providers/llm/` | LLM abstraction — Gemini, mock, key routing |
| `apps/api/app/models/` | PostgreSQL schema via SQLAlchemy ORM |
| `apps/api/app/schemas/` | Pydantic models for API contracts and LLM response shapes |
| `apps/web/src/components/` | One component per learner journey view |
| `apps/web/src/lib/` | API client, auth context, shared TypeScript types |
| `infra/postgres/` | Isolated local PostgreSQL with persistent volume |

---

## 🛠️ Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Backend language | Python | 3.12 | API and domain services |
| API framework | FastAPI | 0.141.1 | Async REST with OpenAPI |
| ORM | SQLAlchemy | 2.0.52 | Async database access |
| Migrations | Alembic | 1.19.1 | Schema version control |
| DB driver | asyncpg | 0.31.0 | Async PostgreSQL driver |
| Database | PostgreSQL | 17 (Alpine) | Primary data store |
| LLM SDK | google-genai | latest | Gemini 2.5 Flash access |
| Schema validation | Pydantic v2 | bundled with FastAPI | Request/response + LLM schemas |
| Token encryption | cryptography (Fernet) | latest | Session token encryption |
| ASGI server | uvicorn | 0.52.4 | Production-ready async server |
| Frontend framework | Next.js | 16.3.3 | React full-stack framework |
| UI library | React | 19.2.8 | Component rendering |
| Language | TypeScript | 5 | Frontend type safety |
| Styling | Tailwind CSS | 4 | Utility-first CSS |
| Test framework | pytest + pytest-asyncio | 7+ | Async Python testing |
| Linter | Ruff | configured | Fast Python linting |
| Type checker | mypy | strict mode | Python static analysis |
| Container | Docker Compose | latest | Local PostgreSQL |

---

## ⚡ Quick Start

> Requires Python 3.12+, Node.js 20+, and Docker.

```bash
# 1. Clone
git clone https://github.com/madhurithika22/ZYRA_AI_Learning_Intelligence.git
cd ZYRA_AI_Learning_Intelligence

# 2. Start PostgreSQL
cd infra/postgres
docker compose up -d
cd ../..

# 3. Set up environment variables
cp .env.example .env
# Edit .env — set GEMINI_API_KEY_1 (or use LLM_PRIMARY_PROVIDER=mock for zero-key local dev)

cp apps/api/.env.example apps/api/.env
# Edit apps/api/.env with the same values

# 4. Set up Python backend
cd apps/api
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
alembic upgrade head

# 5. Start the API server (Terminal 2)
python -m uvicorn app.main:app --reload
# → http://127.0.0.1:8000
# → http://127.0.0.1:8000/docs  (interactive API docs)

# 6. Set up and start frontend (Terminal 3)
cd ../web
npm install
npm run dev
# → http://localhost:3000
```

**Using the Makefile** (from project root, with venv active):

```bash
make api-dev    # Start FastAPI with --reload
make web-dev    # Start Next.js dev server
```

> **No Gemini key?** Set `LLM_PRIMARY_PROVIDER=mock` in `apps/api/.env` to run the full platform with deterministic mock responses — useful for local development and testing.

---

## 🔐 Environment Configuration

### Variable Reference

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | PostgreSQL async connection string |
| `LLM_PRIMARY_PROVIDER` | Yes | `gemini` | LLM provider: `gemini` or `mock` |
| `GEMINI_MODEL` | Gemini only | `gemini-2.5-flash` | Gemini model identifier |
| `GEMINI_API_KEY_1` | Gemini only | — | Primary Gemini API key |
| `GEMINI_API_KEY_2` | No | — | Secondary key (auto-failover on 429) |
| `GEMINI_API_KEY_3` | No | — | Tertiary key (auto-failover on 429) |
| `SECRET_KEY` | Production | built-in default | Fernet session token encryption key |
| `APP_ENV` | No | `development` | Environment label |
| `NEXT_PUBLIC_API_BASE_URL` | Web only | `http://localhost:8000` | API base URL for frontend |

### `apps/api/.env`

```env
DATABASE_URL=postgresql+asyncpg://postgres:Madhu%%21216223@db.wjvizreljylvghqiejnj.supabase.co:5432/postgres
LLM_PRIMARY_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_KEY_1=your_api_key_here
GEMINI_API_KEY_2=
GEMINI_API_KEY_3=
```

### `apps/web/.env`

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### `infra/postgres/.env`

```env
POSTGRES_DB=adaptive_learning
POSTGRES_USER=adaptive_learning
POSTGRES_PASSWORD=your_secure_password_here
```

> **Production note:** Always set a custom `SECRET_KEY` in production. The default value in `security.py` is a development fallback only.

---

## 📡 API Reference

All endpoints require cookie-based session authentication except `/api/v1/auth/register`, `/api/v1/auth/login`, and health endpoints. Full interactive docs at `http://127.0.0.1:8000/docs`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account + learner; sets HttpOnly cookie |
| `POST` | `/api/v1/auth/login` | Validate credentials; sets HttpOnly cookie |
| `POST` | `/api/v1/auth/logout` | Clear session cookie |
| `GET` | `/api/v1/auth/me` | Current authenticated user identity |

### Learner State & Profile

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/learners/me/state` | Onboarding stage + active goal/path IDs |
| `GET` | `/api/v1/learners/{learner_id}/app-state` | Same, by explicit learner ID |
| `GET` | `/api/v1/learners/{learner_id}/profile` | Full profile with gamification and journey progress |
| `PUT` | `/api/v1/learners/{learner_id}/profile` | Update name, experience, availability, avatar |

### Goal Intelligence

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/goal-intelligence/interpret` | Interpret NL goal without persisting |
| `POST` | `/api/v1/learners/{learner_id}/goals` | Interpret + persist goal to database |
| `GET` | `/api/v1/learners/{learner_id}/profile` | Retrieve learner profile and all goals |
| `PUT` | `/api/v1/learners/{learner_id}/profile` | Update profile preferences |

### Adaptive Diagnostics

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/diagnostics` | Start or resume diagnostic session |
| `GET` | `/api/v1/diagnostics/{diagnostic_id}` | Session status and progress |
| `GET` | `/api/v1/learners/{learner_id}/diagnostics/latest` | Most recent session for a goal |
| `GET` | `/api/v1/learners/{learner_id}/diagnostics/history` | Full diagnostic history |
| `POST` | `/api/v1/diagnostics/{diagnostic_id}/self-assessment` | Submit pre-diagnostic baseline ratings |
| `POST` | `/api/v1/diagnostics/{diagnostic_id}/next-question` | Select next adaptive question |
| `POST` | `/api/v1/diagnostics/{diagnostic_id}/responses` | Submit answer; update mastery |
| `GET` | `/api/v1/learners/{learner_id}/skill-state` | Current mastery + confidence across target skills |

### Learning Twin

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/learners/{learner_id}/learning-twin` | Full unified snapshot + decision trace |
| `GET` | `/api/v1/learners/{learner_id}/learning-twin/trace` | Decision trace only |

### Bottleneck Analysis

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/learners/{learner_id}/goals/{goal_id}/bottlenecks` | Ranked skill gap analysis with bottleneck scores |

### Learning Paths

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/learners/{learner_id}/goals/{goal_id}/paths/generate` | Generate 4 strategy path candidates |
| `GET` | `/api/v1/learners/{learner_id}/goals/{goal_id}/paths` | Retrieve existing path candidates |
| `GET` | `/api/v1/learning-paths/{path_id}` | Single path with ordered nodes |
| `POST` | `/api/v1/learning-paths/{path_id}/activate` | Activate chosen path |

### Learning Activities

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/learning-activities/{path_node_id}/start` | Start activity attempt |
| `POST` | `/api/v1/learning-activities/{attempt_id}/save-draft` | Save draft without completing |
| `POST` | `/api/v1/learning-activities/{attempt_id}/complete` | Mark as completed |
| `GET` | `/api/v1/learning-activities/active-attempt` | Current active activity for authenticated learner |
| `GET` | `/api/v1/learning-activities/latest-attempt` | Most recent attempt |
| `GET` | `/api/v1/learning-activities/{attempt_id}` | Specific attempt details |
| `GET` | `/api/v1/learning-activities/{attempt_id}/outcome` | Proof-of-mastery outcome |

### Mastery Checks

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/mastery-checks/{activity_attempt_id}/start` | Start post-activity mastery check |
| `POST` | `/api/v1/mastery-checks/{check_id}/submit` | Submit answers; update mastery |
| `GET` | `/api/v1/mastery-checks/active` | Active check for an activity attempt |
| `GET` | `/api/v1/mastery-checks/{check_id}` | Check attempt by ID |

### Progress

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/learners/{learner_id}/progress` | Full longitudinal progress summary |
| `GET` | `/api/v1/learners/{learner_id}/goals/{goal_id}/progress` | Goal-level skill breakdown |
| `GET` | `/api/v1/learning-paths/{path_id}/progress` | Path node completion and time |
| `GET` | `/api/v1/learners/{learner_id}/skills/{skill_id}/history` | Chronological mastery history |

### Next-Best-Action

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/learners/{learner_id}/next-action` | Top action across all goals |
| `GET` | `/api/v1/learners/{learner_id}/goals/{goal_id}/next-action` | Top action for a goal |
| `GET` | `/api/v1/learners/{learner_id}/goals/{goal_id}/next-actions` | Full ranked candidate list |

### Dynamic Replanning

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/learners/{learner_id}/goals/{goal_id}/replan-status` | Check if replanning is triggered |
| `POST` | `/api/v1/learners/{learner_id}/goals/{goal_id}/replan` | Generate V\_{k+1} draft |
| `GET` | `/api/v1/learning-paths/{path_id}/versions` | Path version history |
| `GET` | `/api/v1/learning-paths/{from_path_id}/diff/{to_path_id}` | Node-level diff between versions |
| `POST` | `/api/v1/learning-paths/{draft_path_id}/accept` | Accept draft; activate V\_{k+1} |
| `POST` | `/api/v1/learning-paths/{draft_path_id}/reject` | Reject draft; keep current active |

### Conversational Assistant

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/learners/{learner_id}/conversation/sessions` | Create session |
| `POST` | `/api/v1/conversation/sessions/{session_id}/messages` | Send message; receive grounded response |
| `GET` | `/api/v1/conversation/sessions/{session_id}` | Session + full message history |
| `GET` | `/api/v1/conversation/sessions/{session_id}/messages` | Message history only |

### System Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API name, version, status |
| `GET` | `/health` | Application liveness |
| `GET` | `/health/database` | PostgreSQL connectivity |
| `GET` | `/health/domain` | Entity counts across all domain tables |

---

## 🗄️ Database

PostgreSQL 17 with Alembic migrations. All primary keys are UUIDs. Schema shipped across 10 incremental migration versions.

### Data Model Overview

```text
Learner
├── UserAccount          (email + hashed password)
├── LearnerProfile       (experience, availability, avatar, background)
├── Goals
│    └── Target Role
│         └── RoleSkill  (required_level, importance per skill)
│              └── Skill (name, difficulty, parent_skill, prerequisite graph)
├── SkillMastery         (mastery_score, confidence per skill)
├── SkillEvidence        (individual evidence records with metadata)
├── LearningPaths
│    ├── version, strategy, status (draft/active/completed/archived)
│    ├── parent_path_id  (lineage for replanning)
│    └── LearningPathNodes → LearningResource
├── LearningActivityAttempts → MasteryCheckAttempts → MasteryOutcomes
├── DiagnosticSessions → DiagnosticResponses
└── ConversationSessions → ConversationMessages
```

### Entity Relationship Diagram

```mermaid
erDiagram
    USER_ACCOUNT ||--|| LEARNER : "belongs to"
    LEARNER ||--o| LEARNER_PROFILE : "has"
    LEARNER ||--o{ GOAL : "sets"
    GOAL }o--|| ROLE : "targets"
    ROLE ||--o{ ROLE_SKILL : "requires"
    ROLE_SKILL }o--|| SKILL : "defines requirement"
    SKILL ||--o{ SKILL_RELATION : "has prerequisites"
    SKILL ||--o{ ASSESSMENT_QUESTION : "assessed by"
    LEARNER ||--o{ SKILL_MASTERY : "scored per skill"
    LEARNER ||--o{ SKILL_EVIDENCE : "generates"
    LEARNER ||--o{ LEARNING_PATH : "follows"
    GOAL ||--o{ LEARNING_PATH : "has"
    LEARNING_PATH ||--o| LEARNING_PATH : "parent version"
    LEARNING_PATH ||--o{ LEARNING_PATH_NODE : "contains"
    LEARNING_PATH_NODE }o--|| LEARNING_RESOURCE : "uses"
    LEARNING_PATH_NODE }o--|| SKILL : "targets"
    LEARNER ||--o{ LEARNING_ACTIVITY_ATTEMPT : "makes"
    LEARNING_ACTIVITY_ATTEMPT ||--o| MASTERY_CHECK_ATTEMPT : "followed by"
    MASTERY_CHECK_ATTEMPT ||--o| MASTERY_OUTCOME : "produces"
    LEARNER ||--o{ DIAGNOSTIC_SESSION : "has"
    DIAGNOSTIC_SESSION ||--o{ DIAGNOSTIC_RESPONSE : "contains"
    LEARNER ||--o{ CONVERSATION_SESSION : "has"
    CONVERSATION_SESSION ||--o{ CONVERSATION_MESSAGE : "contains"
```

### Key Tables

| Table | Purpose |
|---|---|
| `learners` | Core identity — email, display\_name |
| `user_accounts` | Authentication — password\_hash, linked to learner |
| `learner_profiles` | Experience level, availability, avatar, background |
| `goals` | Target role + timeline + daily\_minutes per learner |
| `roles` | Career role catalog |
| `skills` | Canonical skill catalog with difficulty and hierarchy |
| `role_skills` | Required skills per role with `importance` and `required_level` |
| `skill_relations` | Prerequisite graph edges between skills |
| `skill_mastery` | Per-learner `mastery_score` + `confidence` per skill |
| `skill_evidence` | Individual evidence records with source, score, metadata |
| `assessments` | Assessment containers (diagnostic / mastery types) |
| `assessment_questions` | Questions with difficulty (1–5), type, expected answer |
| `diagnostic_sessions` | Session state, metadata, termination reason |
| `diagnostic_responses` | Answers with idempotency key |
| `learning_paths` | Generated paths — strategy, status, `version`, `parent_path_id` |
| `learning_path_nodes` | Sequenced nodes — skill, resource, estimated minutes |
| `learning_resources` | Curated resources with URL and type |
| `learning_activity_attempts` | Engagement lifecycle: pending → started → completed |
| `mastery_check_attempts` | Post-activity assessment sessions |
| `mastery_outcomes` | Final evidence from passed mastery checks |
| `conversation_sessions` | Chat session containers |
| `conversation_messages` | Messages with intent, source references, confidence |

---

## 🤖 AI Architecture

The system deliberately separates LLM-dependent operations from deterministic computation. This is a core architectural decision, not an optimisation.

### LLM-Powered (3 operations)

| Operation | Service | When LLM is called |
|---|---|---|
| Goal interpretation | `GoalIntelligenceService` | On natural language goal submission |
| Answer evaluation | `LLMEvaluator` | For short-answer, coding, scenario questions only (not multiple choice) |
| Conversational reasoning | `ConversationalService` | For "why" / explanation / comparison questions (factual queries bypass LLM) |

The Gemini provider is accessed exclusively through the `LLMProvider` abstraction. Domain services never import a vendor SDK directly.

### Deterministic (7 engines — zero LLM)

| Engine | Service | Description |
|---|---|---|
| Adaptive question selection | `QuestionSelectionService` | Scoring: `uncertainty × importance × difficulty_fit × novelty × coverage_balance` |
| Mastery scoring | `MasteryEngine` | Evidence-weighted incremental update with consistency bonus |
| Bottleneck ranking | `BottleneckAnalysisService` | `gap × role_importance × dep_impact × uncertainty_factor` |
| Dependency propagation | `DependencyImpactService` | Downstream skill impact scoring across prerequisite graph |
| Next-best-action | `NextActionService` | 7-weight scoring with deterministic tie-breaking |
| Unified state snapshot | `LearningTwinService` | Composes all engines; no independent inference |
| Drift detection + replanning | `ChangeDetectionService` + `ReplanningService` | Threshold-based triggers; staleness score 0.0–1.0 |

### Why This Hybrid Architecture?

| Benefit | How it's achieved |
|---|---|
| Predictability | Identical database state always produces identical decisions in deterministic engines |
| Explainability | Every recommendation carries a decision trace with named inputs and weights |
| Reduced hallucination risk | Factual learner-state data is never inferred by an LLM — it comes from the database |
| Lower LLM dependency | Core learning loop (mastery, bottleneck, next action, replan) runs with zero API calls |
| Test isolation | `MockLLMProvider` replaces all LLM calls; 18 test modules run with zero network dependency |
| Graceful degradation | `LLMEvaluator` falls back to `DeterministicEvaluator` on any provider failure |

### Multi-Key Router

`GeminiKeyRouter` manages up to 3 API key slots. On HTTP 429 (quota exhaustion), the failing key is marked unavailable with a configurable cooldown (default: 60 seconds) and the next healthy key is used. All 3 keys exhausted → `RuntimeError` with clear message. Key slot status is exposed diagnostically without revealing key values.

---

## 🔍 Explainability and Decision Trace

The system is designed to answer *why* at every step.

**Why was this skill identified as a bottleneck?**
Every `SkillGapItem` includes `primary_reason`, `evidence` bullets (mastery %, required level, role importance, confidence, dependency impact), `classification`, and `downstream_skills` affected.

**Why was this action recommended?**
Every `NextActionItem` includes `primary_reason`, `supporting_reasons`, `metrics_used` (all 7 named weights with computed values), `constraints_considered` (daily time budget), and `tradeoffs`.

**Why was the path replanned?**
Every `ReplanDecision` includes `trigger_type` (PATH\_NODE\_OBSOLETE / BOTTLENECK\_RESOLVED / BOTTLENECK\_SHIFTED / SKILL\_GAP\_CHANGED), `staleness_score`, and a human-readable `rationale`.

**What changed mastery?**
Every `SkillEvidence` record stores the source question ID, question difficulty, question type, `is_correct`, `rubric_coverage`, and `misconception_code`.

**What is the full learner state?**
The Learning Twin's `DecisionTrace` contains: `learner_state_summary`, `skill_state_trace` (per-skill mastery/required/confidence/gap/status), `bottleneck_trace`, `next_action_trace`, `path_state_trace`, and `replan_trace` — all computed deterministically from database state.

---

## 🧪 Testing

### Strategy

The test suite is designed for full isolation and determinism.

- `MockLLMProvider` is applied via `autouse` fixture in `conftest.py` — all 18 test modules run with zero real Gemini API calls
- Each test uses an isolated `AsyncSession` with rollback semantics
- Domain logic tests operate directly on service classes, not via HTTP
- API integration tests use `httpx.AsyncClient`
- Deterministic engines are tested with exact score assertions

```text
pytest
 ├── conftest.py (autouse: MockLLMProvider + isolated DB session)
 ├── Domain service tests → Services → DB
 └── API integration tests → httpx → FastAPI → Services → DB
```

### Running Tests

```bash
cd apps/api
# Activate venv first
pytest                                    # All tests
pytest tests/test_learning_twin.py -v    # Single module, verbose
pytest tests/ -k "mastery" -v            # Filter by name
pytest --tb=short                         # Compact failure output
```

### Test Modules

| Module | Coverage Area |
|---|---|
| `test_auth.py` | Registration, login, logout, session cookie lifecycle |
| `test_adaptive_diagnostic.py` | Diagnostic session, question selection algorithm |
| `test_bottleneck_detection.py` | Bottleneck scoring, classification, dependency impact |
| `test_learning_twin.py` | Unified Learning Twin composition, confidence levels |
| `test_next_action.py` | Candidate generation, 7-weight scoring, ranking |
| `test_replanning.py` | Drift detection triggers, diff generation, accept/reject |
| `test_mastery_check_lifecycle.py` | Post-activity proof of mastery flow |
| `test_proof_of_mastery.py` | Mastery evidence recording, outcome persistence |
| `test_learning_path_optimizer.py` | 4-strategy path generation |
| `test_conversation.py` | Grounded conversational assistant, intent classification |
| `test_goal_intelligence.py` | LLM goal interpretation, role resolution |
| `test_progress.py` | Progress summary, skill history |
| `test_gemini_key_router.py` | Key rotation, cooldown, quota failure handling |
| `test_gamification.py` | XP, level, streak, achievement badge logic |
| `test_app_state.py` | Learner onboarding stage resolution |
| `test_domain_models.py` | ORM model integrity and relationships |

---

## 🔒 Security

### Implemented

| Mechanism | Implementation |
|---|---|
| Password hashing | PBKDF2-HMAC-SHA256, 200,000 iterations, 16-byte random salt |
| Password comparison | `secrets.compare_digest` — constant-time, prevents timing attacks |
| Session tokens | Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256), 7-day expiry, derived from `SECRET_KEY` via SHA-256 |
| Cookie security | `HttpOnly=True`, `SameSite=Lax` — inaccessible to JavaScript |
| Resource authorization | Every protected route verifies `current_learner.id == learner_id` before any data access |
| LLM prompt injection defense | System prompt labels user messages as `[UNTRUSTED INPUT]`; explicit rules prohibit following user instructions to override system behaviour |
| Source ID validation | Conversational assistant responses are post-processed — source IDs not in the backend-provided allowlist are filtered out before returning |
| API key safety | Gemini key slot status is exposed diagnostically (`healthy` / `exhausted`) without revealing key values |
| CORS | Restricted to `localhost:3000` / `127.0.0.1:3000` and `127.0.0.1:8000` in development |
| Input validation | All API inputs validated by Pydantic v2 schemas before reaching service layer |

### Recommended for Production

- Set a strong, unique `SECRET_KEY` environment variable (the development default in `security.py` is a fallback only)
- Enable `secure=True` on session cookies when serving over HTTPS
- Restrict CORS `allow_origins` to the specific production domain
- Add rate limiting per learner on LLM-backed endpoints

---

## 📈 Scalability and Performance

### Implemented

- **Fully async** — FastAPI + SQLAlchemy async engine + asyncpg; no blocking I/O on any request path
- **Connection pooling** — SQLAlchemy async engine with `pool_pre_ping` for stale connection recovery
- **No N+1 queries** — All hot-path services (NextActionService, LearningTwinService, BottleneckAnalysisService) batch-load all required records in separate bulk queries using `selectinload` and `in_` clauses
- **LLM cost control** — Factual learner-state queries in the conversational assistant bypass the LLM entirely; only explanation/reasoning queries invoke Gemini
- **Quota resilience** — GeminiKeyRouter eliminates single-key quota exhaustion as a hard failure; bounded cooldown ensures keys recover automatically

### Recommended for Production

- **Redis cache** — Learning Twin snapshots are high-read / low-write; a short TTL cache would significantly reduce DB load at scale
- **Background task queue** — Path generation and replanning for large skill graphs are CPU-bound; moving them to a task queue (Celery, ARQ) would keep API response times predictable
- **Additional DB indexes** — Add composite indexes on `(learner_id, skill_id)` for `skill_mastery` and `skill_evidence` at query scale
- **Rate limiting** — Per-learner rate limits on LLM-backed endpoints to prevent quota abuse

---

## 🚢 Deployment

Production deployment configuration is not currently included in this repository. The project runs fully locally using the setup described in [Quick Start](#-quick-start).

### Current Local Architecture

```mermaid
flowchart LR
    Browser -->|:3000| Web[Next.js Dev Server\nnpm run dev]
    Web -->|HTTP :8000| API[FastAPI\nuvicorn --reload]
    API --> PG[(PostgreSQL 17\nDocker :5432)]
    API -->|HTTPS| Gemini[Google Gemini API\ncloud.google.com]
```

### Recommended Next Steps for Production

1. Add a `Dockerfile` for the FastAPI API (Python 3.12 slim base, `pip install -r requirements.txt`, `uvicorn` entrypoint)
2. Add a `Dockerfile` for the Next.js web app (`npm run build`, `npm start`)
3. Create a root-level `docker-compose.yml` orchestrating all three services (api, web, postgres) with environment variable injection
4. Configure `SECRET_KEY`, `GEMINI_API_KEY_*`, and `DATABASE_URL` as secrets in your deployment platform
5. Enable HTTPS and set `secure=True` on session cookies

---

## 📊 Project Status

| Area | Status | Notes |
|---|---|---|
| FastAPI backend | ✅ Complete | 14 route modules, 22 ORM models |
| Next.js frontend | ✅ Complete | Full learner journey, 20+ components |
| Goal Intelligence | ✅ Complete | NL → Role + Skills via Gemini |
| Adaptive Diagnostic | ✅ Complete | Information-gain question selection |
| Mastery Engine | ✅ Complete | Evidence-weighted scoring + confidence |
| Bottleneck Analysis | ✅ Complete | Dependency-aware gap ranking |
| Learning Twin | ✅ Complete | 7-dimension state + decision trace |
| Path Optimizer | ✅ Complete | 4 strategy candidates |
| Next-Best-Action | ✅ Complete | 7-weight deterministic scoring |
| Proof of Mastery | ✅ Complete | Post-activity verification |
| Dynamic Replanning | ✅ Complete | Drift detection + V\_k → V\_{k+1} diff |
| Conversational AI | ✅ Complete | Grounded, injection-defended |
| Gamification | ✅ Complete | XP, levels, streaks, badges |
| Automated tests | ✅ Complete | 18 modules, mock LLM isolation |

---

## 🛣️ Roadmap

```text
Phase 1 — Core Domain Model             ✅  Learner, Goal, Role, Skill, Path
Phase 2 — Adaptive Assessment           ✅  Diagnostic, Mastery Engine, Evidence
Phase 3 — Intelligence Engines          ✅  Bottleneck, Next Action, Path Optimizer
Phase 4 — Learning Twin                 ✅  Unified state, decision trace, confidence
Phase 5 — Proof of Mastery             ✅  Activity lifecycle, post-activity checks
Phase 6 — Dynamic Replanning           ✅  Drift detection, V_k versioning, diff
Phase 7 — Conversational AI            ✅  Grounded assistant, intent classification
Phase 8 — Gamification & Profile       ✅  XP, levels, streaks, achievements
Phase 9 — Production Hardening         🚧  Docker, prod config, rate limiting
Phase 10 — Observability & Scale       📋  Caching, background tasks, monitoring
```

**Near-term additions (planned):**
- Seed data management CLI or admin endpoint
- Email verification on registration
- Token-based password reset
- Spaced repetition / retention assessments for idle skills
- Root-level Docker Compose for one-command startup

**Longer term (recommended):**
- Redis TTL cache for Learning Twin snapshots
- Background task queue for path generation
- Admin dashboard for role/skill catalog management
- Multi-goal parallel tracking in the frontend

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Follow the conventions in `docs/development-conventions.md` — particularly: separate concerns, deterministic logic for deterministic decisions, LLM calls only through the provider abstraction layer
4. Run tests: `cd apps/api && pytest`
5. Run type checking: `mypy app/`
6. Run linting: `ruff check app/ tests/`
7. Commit: `git commit -m "feat: describe your change"`
8. Push and open a pull request

---

## 📄 License

No license has been specified for this project yet.

---

**Authors:** Girikannan M P, Madhu Rithika R K, Raj Moorthy

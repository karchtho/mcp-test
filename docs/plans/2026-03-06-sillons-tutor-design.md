# Sillons Tutor — Architecture Design

**Date:** 2026-03-06
**Status:** Approved
**Context:** POC for Lycée Agricole de Rouffach (EPLEFPA Les Sillons de Haute-Alsace)

---

## 1. Project Intent

An offline-first educational tool that guides students through TDs (Travaux Dirigés) using a local AI tutor. The AI acts as a Socratic guide — it never gives direct answers, only asks questions and provides calibrated hints. Teachers upload content, configure hint levels, and monitor progress. Students log in with a PIN and the system remembers where they left off.

Target audience: students in viticulture, oenology, agronomy, and related agricultural sciences.

**Phase 1:** Local POC, single machine, manual setup.
**Phase 2 (planned):** Shared school server, multi-user, deployed via Docker.

---

## 2. High-Level Architecture

```
Docker Compose (local / school server)
├── frontend     Angular app           :4200
├── backend      FastAPI REST API       :8000
├── ollama       Local LLM, no internet :11434
└── db           PostgreSQL             :5432
```

All services communicate on an internal Docker network. No internet required after initial setup (model pull, package installs).

---

## 3. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | Angular + TypeScript | Rigorous, opinionated, familiar |
| Backend | FastAPI (Python) | Async, type-safe, auto-docs, AI ecosystem |
| Database | PostgreSQL | JSONB for chat history, full-text search, production-grade |
| ORM | SQLModel + Alembic | FastAPI-native, Pydantic models = DB models, versioned migrations |
| Local LLM | Ollama | One-command install, no internet at runtime, swappable models |
| Containerization | Docker + Docker Compose | Same setup POC → school server |

---

## 4. Service Breakdown

### Frontend (Angular)

Two lazy-loaded feature modules:

```
src/app/
├── student/
│   ├── login/       PIN entry
│   ├── td-list/     pick a TD or resume session
│   └── chat/        main tutor chat interface (SSE streaming)
└── teacher/
    ├── login/       password entry
    ├── td-manager/  upload TDs, configure hint levels, preview parsed exercises
    └── progress/    student progress dashboard
```

### Backend (FastAPI)

Versioned REST API, auto-documented at `/docs`.

```
/api/v1/
├── auth/
│   ├── POST /student/login        PIN → JWT
│   └── POST /teacher/login        password → JWT
├── tds/
│   ├── GET    /                   list all TDs
│   ├── POST   /                   create TD (teacher)
│   ├── GET    /{id}               get TD + exercises
│   └── POST   /{id}/upload        upload MD file (teacher)
├── sessions/
│   ├── POST   /                   start or resume session
│   ├── GET    /{id}               get session state + progress
│   └── PATCH  /{id}/progress      update current exercise
├── chat/
│   └── POST   /{session_id}       send message → SSE stream (AI response)
└── admin/
    ├── GET    /students            all student progress (teacher)
    └── GET    /tds/{id}/stats      per-TD analytics (teacher)
```

Chat uses **Server-Sent Events (SSE)** to stream Ollama tokens progressively to the frontend.

---

## 5. Data Model

```sql
students
  id            uuid PK
  name          varchar
  pin_hash      varchar        -- bcrypt, never store raw
  created_at    timestamp

tds
  id            uuid PK
  title         varchar
  subject       varchar        -- viticulture, agronomie, etc.
  hint_level    enum           -- none | guided | progressive (default: guided)
  file_path     varchar        -- original uploaded file
  created_at    timestamp

exercises
  id            uuid PK
  td_id         uuid FK → tds
  order         int            -- question sequence within TD
  content       text           -- parsed from MD
  hint_level    enum nullable  -- overrides TD hint_level if set; null = inherit

sessions
  id            uuid PK
  student_id    uuid FK → students
  td_id         uuid FK → tds
  current_exercise_id  uuid FK → exercises
  status        enum           -- in_progress | completed
  started_at    timestamp
  updated_at    timestamp      -- used for "last seen" / resume

messages
  id            uuid PK
  session_id    uuid FK → sessions
  role          enum           -- user | assistant | system
  content       text
  created_at    timestamp
```

**Key rules:**
- `exercises.hint_level` is nullable — null inherits from parent `td.hint_level`
- `tds.hint_level` defaults to `guided` — safe default when teacher sets nothing
- `messages` stores full history per session — enables AI context on resume + teacher audit

---

## 6. Content Pipeline

Teachers upload Markdown files only (PDF in v2). Parsing is automatic and invisible to the teacher.

**Required MD template:**
```markdown
# TD 3 — La vinification en rouge

## Question 1
Citez les étapes de la vinification en rouge.

## Question 2
Quel est le rôle des levures dans la fermentation ?
```

**Upload flow:**
1. Teacher uploads `.md` file via Angular UI
2. FastAPI parser extracts TD metadata + splits on `## Question N` headings
3. DB populated: one `tds` row + N `exercises` rows
4. Teacher sees preview: "We found 4 exercises — does this look right?"
5. Teacher can adjust hint level per exercise if needed

---

## 7. AI / Socratic Logic

The Socratic behavior is enforced in FastAPI. Ollama is a token generator — the intelligence is in prompt design.

### System prompt (built dynamically per session)

```
You are a learning assistant for [subject] at Lycée Agricole de Rouffach.

EXERCISE:
[exercise content injected here]

HINT LEVEL: guided

RULES:
- Never state the answer directly
- Ask guiding questions that lead the student to discover the answer
- If the student is wrong, do not say "wrong" — ask them to reconsider a specific aspect
- If stuck after 3 attempts:
    none:        redirect to course notes ("Refer to your notes on [topic]")
    guided:      give a concrete clue without the answer
    progressive: reveal reasoning steps one at a time
- Always respond in French
- If asked directly for the answer, refuse warmly and redirect
```

### Safeguard layers

| Layer | Mechanism |
|---|---|
| 1 — LLM-level | System prompt rules |
| 2 — Response filtering | FastAPI post-processes response, scans for direct answer patterns |
| 3 — Attempt tracking | Attempt counter per exercise in session; escalates hint level after N tries |

---

## 8. Authentication

| Actor | Method | Scope |
|---|---|---|
| Student | PIN (4-6 digits) → JWT | Student routes only |
| Teacher | Password → JWT | Teacher + admin routes |

Auth via JWT bearer tokens. No user accounts, no email. Full auth system planned for Phase 2.

---

## 9. Environment & Docker

### Files

```
sillons-tutor/
├── .env                     single source of truth, gitignored
├── .env.example             committed, placeholder values
├── docker-compose.yml       production config (`docker compose up`)
├── docker-compose.dev.yml   dev overrides (volumes, hot reload) — explicit only
├── docker/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
├── backend/
├── frontend/
└── docs/
```

### Dev vs Prod

- **Prod:** `docker compose up` — built images, no mounts
- **Dev:** `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` — source mounted, hot reload enabled

Dev uses `uvicorn --reload` for FastAPI and `ng serve --poll 500` for Angular (polling required on macOS Docker).

---

## 10. Conventions & Tooling

### Linting & Formatting

| Layer | Tool |
|---|---|
| Frontend | ESLint + Prettier + Angular ESLint |
| Backend | Ruff (replaces flake8 + black + isort) |
| Both | pre-commit hooks |

### Git

- **Conventional commits:** `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`
- **Branches:** `main` (stable) + `feature/*`
- **Pre-commit:** lint + format checks block dirty commits

### Documentation

```
docs/
├── architecture.md      high-level diagram + ADRs (Architecture Decision Records)
├── api.md               endpoint reference
├── data-model.md        schema + field explanations
├── conventions.md       linting, git, naming, file structure rules
├── ai-behavior.md       Socratic rules, prompt design, safeguard layers
├── workflow-with-ai.md  how to work with Claude on this project
├── journal.md           running dev log — decisions, explorations, process
└── plans/               one file per feature/session design doc
```

---

## 11. Out of Scope for POC

- PDF upload (v2)
- Full authentication system (v2)
- Multi-tenant school server deployment (v2)
- Student self-registration (v2)
- Analytics dashboard beyond basic progress (v2)

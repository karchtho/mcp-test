# Sillons Tutor — Claude Project Memory

This file is loaded at the start of every session. Keep it concise and current.

---

## Project

An offline-first educational tool for Lycée Agricole de Rouffach (EPLEFPA Les Sillons de Haute-Alsace). A local AI tutor guides students through TDs (Travaux Dirigés) using Socratic questioning — never giving direct answers. Teachers upload content, configure hint levels, track progress.

Full design: `docs/plans/2026-03-06-sillons-tutor-design.md`

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Angular + TypeScript |
| Backend | FastAPI (Python) + SQLModel + Alembic |
| Database | PostgreSQL |
| Local LLM | Ollama (no internet at runtime) |
| Containers | Docker Compose |

---

## Repo Structure

```
sillons-tutor/
├── .env                      gitignored, single source of truth
├── .env.example              committed, placeholder values
├── docker-compose.yml        prod — `docker compose up`
├── docker-compose.dev.yml    dev — explicit, hot reload, mounted volumes
├── docker/                   Dockerfiles per service
├── backend/                  FastAPI app
├── frontend/                 Angular app
└── docs/
    ├── plans/                one design doc per feature/session
    ├── journal.md            running dev log (see below)
    ├── architecture.md
    ├── api.md
    ├── conventions.md
    ├── ai-behavior.md
    └── workflow-with-ai.md
```

---

## Key Conventions

- **Commits:** conventional commits (`feat:`, `fix:`, `docs:`, `chore:`)
- **Branches:** `main` (stable) + `feature/*`
- **Linting:** ESLint + Prettier + Angular ESLint (frontend) / Ruff (backend)
- **Pre-commit hooks:** block dirty commits
- **API:** versioned REST under `/api/v1/`, auto-docs at `/docs`
- **Auth:** JWT — student via PIN, teacher via password

---

## POC Scope (what's in / out)

**In:** Angular UI, FastAPI, Ollama, Postgres, Docker, PIN auth, MD upload, Socratic chat, progress tracking, SSE streaming

**Out (v2):** PDF upload, full auth system, school server deployment, multi-tenant, analytics dashboard

---

## Session Workflow

### Starting a session
1. Read this file and `docs/journal.md` to load context
2. Check `docs/plans/` for the most recent design doc
3. Ask the user what to work on if not specified

### Ending a session
**Always run `/session-end` before closing.** Then append to `docs/journal.md`:
- What was worked on
- Decisions made and why
- What the AI did (proposed, pushed back on, got wrong)
- What shaped the design from the conversation
- Next session starting point

The journal documents the *process* — how this project was built with AI assistance — not just the code changes. Write it as a human-readable account, not a changelog.

---

## Architecture Decisions (brief)

- PostgreSQL over MySQL: JSONB, full-text search, modern standard
- `.env` at root: Docker Compose reads it automatically; one source of truth
- `docker-compose.dev.yml` explicit (not override): prod stays `docker compose up`
- Markdown-only uploads for POC: PDF parsing is fragile; simple template is reliable
- SSE not WebSockets for chat: simpler, native browser support, Ollama streams tokens
- `exercises.hint_level` nullable: inherits from parent TD when not set
- Default hint level: `guided` — safe when teacher forgets to configure

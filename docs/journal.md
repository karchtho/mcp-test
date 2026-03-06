# Dev Journal — Sillons Tutor

A running log of the development process: decisions made, things explored, dead ends, and how working with AI shaped the project. Written to document not just *what* was built but *how* and *why*.

---

## 2026-03-06 — Session 1: Brainstorming & Architecture Design

**Starting point:** An existing MCP server (Python, Flask, MySQL) that could search and upload course content to Claude Desktop. The idea: turn it into a proper educational tool.

**What we figured out:**

Started with a vague idea — "an MCP + local LLM to guide students through TDs." The brainstorming process forced precision:

- **Who uses it?** POC on one machine (teacher's), but designed with a shared school server (option C) as the north star from day one.
- **Which school?** Lycée Agricole de Rouffach (EPLEFPA Les Sillons de Haute-Alsace) — the only viticultural lycée in Alsace. Subjects: viticulture, oenology, agronomy, STAV. This context shaped the Socratic safeguard design (domain knowledge, not code execution).
- **Local LLM:** Ollama — no internet at runtime. Docker makes the POC and future school server the same stack.
- **Why not keep MySQL?** PostgreSQL is better for this: JSONB for chat history, native full-text search for exercises, modern standard. Since we're redesigning the schema anyway, switching costs nothing.
- **Frontend:** Angular (TypeScript) — the user has Angular experience and likes its rigorous, opinionated structure. Pairs with FastAPI (Python) for the backend. Two languages, clean REST boundary. Python owns the AI/ML toolchain.
- **Why not NestJS?** NestJS would feel familiar (same decorator/DI patterns as Angular) but Python is the right choice for AI work (Ollama, LangChain ecosystem).

**Key decisions and their reasoning:**

| Decision | Alternatives considered | Why this |
|---|---|---|
| PostgreSQL | MySQL (existing), SQLite | JSONB, full-text search, production-grade |
| SQLModel + Alembic | raw SQLAlchemy, Tortoise | FastAPI-native, Pydantic = DB models, versioned migrations |
| Ollama | LM Studio, llama.cpp | Simplest local setup, REST API, swappable models |
| Markdown-only uploads (POC) | PDF support now | PDF parsing is messy; MD with a simple template is reliable |
| SSE for chat streaming | WebSockets, polling | Simpler than WebSockets, native browser support, Ollama streams tokens |
| Single `.env` at root | backend/.env, multiple .env files | Docker Compose reads from root; one source of truth |
| `docker-compose.dev.yml` explicit | `docker-compose.override.yml` auto-merged | Prod is `docker compose up` (simple for school server admin); dev is explicit |
| PIN auth for students | no auth, full login | Simple enough for POC, maps to progress tracking, full auth in v2 |
| Socratic default: `guided` | `none` (too strict), `progressive` | Safe middle ground when teacher forgets to configure |

**What the AI did well:**
- Pushed back on "just use MySQL" with concrete reasons
- Flagged the Next.js vs NestJS naming confusion before it caused problems
- Suggested the `docker-compose.dev.yml` / `docker-compose.yml` flip (prod = simple command) when the user's instinct was right but the framing was off
- Kept the POC scope tight while designing for future expansion

**What shaped the design from conversation:**
- The school context (agricultural, viticultural) came from a web search mid-session — changed how the Socratic safeguards were framed
- The "one .env" constraint came from the user pushing back on complexity — good call, simplified the architecture
- The teacher "forgetting to configure" hint levels led to the nullable `exercises.hint_level` with inheritance from the parent TD

**Output:** Full architecture design doc at `docs/plans/2026-03-06-sillons-tutor-design.md`

**Next session:** Implementation planning — scaffold the monorepo, set up Docker Compose, initialize Angular + FastAPI projects.

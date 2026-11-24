# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Warehouse management system, currently only a foundation: config, DB wiring, health checks, and placeholder analytics/agent modules. No business features exist yet.

## Commands

Local setup (from repo root):
```bash
cp .env.example .env
docker compose up -d db          # PostgreSQL 17
```

Backend (run from `backend/`; dependencies are managed with uv only, so use `uv add` / `uv add --dev`, never pip):
```bash
uv sync
uv run uvicorn app.main:app --reload            # http://localhost:8000/docs
uv run pytest                                   # all tests
uv run pytest tests/test_health.py::test_health # single test
uv run ruff check --fix . && uv run ruff format .
uv run alembic revision --autogenerate -m "msg"
uv run alembic upgrade head
```

Frontend (run from `frontend/`):
```bash
npm install
npm run dev      # http://localhost:5173, proxies /api -> backend
npm run build    # tsc -b type-check + vite build
```

## Architecture

- **One shared `.env` at the repo root** feeds everything: `backend/app/core/config.py` (pydantic-settings, `env_file=(".env", "../.env")` so it works from root or `backend/`), `docker-compose.yml`, and Vite (`envDir: ".."`, only `VITE_*` vars reach the browser). Add new settings to both `Settings` and `.env.example`. List settings like `CORS_ORIGINS` are JSON strings.
- **Settings access** is always `get_settings()` (cached), never a fresh `Settings()`.
- **Request flow:** the browser calls relative `/api/...` (via `frontend/src/api/client.ts`). In dev the Vite proxy forwards it to FastAPI, so there are no CORS issues locally. `app/main.py` mounts `app/api/router.py` under `settings.api_prefix` (`/api`). New feature routers go in `app/api/routes/` and must be registered in `router.py`.
- **Database:** sync SQLAlchemy 2 with the psycopg 3 driver (`postgresql+psycopg://`). Routes get a session through the `get_db` dependency in `app/db/session.py`. All ORM models subclass `app.db.base.Base` and must be imported where Alembic can see them, because `migrations/env.py` uses `Base.metadata` for autogenerate and reads its URL from `DATABASE_URL`. `alembic.ini`'s `sqlalchemy.url` is intentionally blank.
- **Analytics (`app/analytics/`):** Pandas/NumPy/Scikit-learn/Matplotlib. Its `__init__` forces Matplotlib's `Agg` backend, so import plotting code through this package on the server.
- **Agents (`app/agents/`):** every agent gets its chat model from `get_chat_model()` in `llm.py` (LangChain `ChatAnthropic`, model from `LLM_MODEL`, default `claude-opus-5-5`). It raises if `ANTHROPIC_API_KEY` is unset, so it is only called lazily, never at import time. LangGraph graphs follow the `build_graph()` pattern in `graph.py` with a `TypedDict` state using the `add_messages` reducer.
- **Frontend:** React 19 + TypeScript + Vite single-page app. Server state goes through React Query (`QueryClientProvider` in `main.tsx`) rather than a global store.

Keep the architecture simple and maintainable.

Use type hints and clear naming conventions.

Separate API routes, business logic and database operations.

Implement only what is requested.

Plan before making significant changes.

Test every implemented feature.

Explain important technical decisions.

Never hardcode credentials.

Never push to GitHub without approval.

Do not introduce unnecessary dependencies.
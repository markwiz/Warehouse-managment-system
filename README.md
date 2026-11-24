# Warehouse Management System

Project foundation only: structure, dependencies, configuration and a minimal
end-to-end wiring (frontend → API → PostgreSQL). No business features yet.

## Layout

```
.
├── backend/                 FastAPI app (managed with uv)
│   ├── app/
│   │   ├── main.py          App factory, CORS, router mounting
│   │   ├── core/config.py   Pydantic settings (reads .env)
│   │   ├── db/              SQLAlchemy engine, session dependency, declarative Base
│   │   ├── api/             router.py + routes/ (one module per feature)
│   │   ├── analytics/       Pandas / NumPy / Scikit-learn / Matplotlib code
│   │   └── agents/          LangChain model factory + LangGraph graphs
│   ├── migrations/          Alembic (uses DATABASE_URL and Base.metadata)
│   └── tests/
├── frontend/                React + TypeScript + Vite
├── docker-compose.yml       PostgreSQL for local development
└── .env.example             Single shared config file
```

## Getting started

```bash
cp .env.example .env
docker compose up -d db

cd backend
uv sync
uv run uvicorn app.main:app --reload     # http://localhost:8000/docs

cd ../frontend
npm install
npm run dev                              # http://localhost:5173
```

The page shows the API and database health. Useful commands in `backend/`:
`uv run pytest`, `uv run ruff check .`, `uv run alembic revision --autogenerate -m "..."`,
`uv run alembic upgrade head`.

## Adding a feature

1. Models in `app/db/` (or a feature package), imported so Alembic sees them.
2. Pydantic schemas + a router in `app/api/routes/`, registered in `app/api/router.py`.
3. Analytics or agent logic in `app/analytics/` / `app/agents/`, called from the router.
4. Frontend API calls in `frontend/src/api/`, data fetched with React Query.

## Frontend choice: React + TypeScript + Vite

- **Built for data-heavy screens.** A WMS is mostly tables, forms, filters and
  dashboards. React has the largest choice of mature data grids, form libraries
  and chart components for that.
- **Types that match the backend.** FastAPI publishes an OpenAPI schema, so
  TypeScript types can be generated from it later and stay in sync with the
  Pydantic models.
- **Simple to run.** Vite is a single-page app with no server of its own:
  quick startup, quick rebuilds, and static files to deploy. FastAPI stays the
  only backend, which is why a full-stack framework like Next.js was not chosen.
- **React Query** handles server state (caching, refetching, loading and error
  states), which covers most of what a CRUD app needs without a global store.

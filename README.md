# Warehouse Management System

Foundation (structure, dependencies, configuration, frontend → API → PostgreSQL
wiring) plus the first feature: product management at `/api/products`.

## Layout

```
.
├── backend/                 FastAPI app (managed with uv)
│   ├── app/
│   │   ├── main.py          App factory, CORS, router mounting
│   │   ├── core/config.py   Pydantic settings (reads .env)
│   │   ├── db/              SQLAlchemy engine, session dependency, Base, models/ registry
│   │   ├── api/             router.py + routes/ (HTTP layer, one module per feature)
│   │   ├── schemas/         Pydantic request/response models (validation)
│   │   ├── services/        Business rules, owns transactions
│   │   ├── repositories/    Database queries
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

Before the first run, apply migrations with `uv run alembic upgrade head` in `backend/`.
The page shows the API and database health. Useful commands in `backend/`:
`uv run pytest`, `uv run ruff check .`, `uv run alembic revision --autogenerate -m "..."`,
`uv run alembic upgrade head`.

If another PostgreSQL already uses port 5432, set `POSTGRES_PORT=5433` in `.env` and
change the port in `DATABASE_URL` and `TEST_DATABASE_URL` to match.

## Testing

`uv run pytest` runs schema tests (no database) and API/persistence tests against a
separate test database (`TEST_DATABASE_URL`, created automatically, truncated after
each test). If PostgreSQL is unreachable, the database tests are skipped and the
reason is printed.

## Products API

| Method | Path | Result |
|---|---|---|
| `POST` | `/api/products` | 201 created · 409 SKU already exists · 422 invalid |
| `GET` | `/api/products?offset=0&limit=50` | 200 list ordered by id (limit 1–200) |
| `GET` | `/api/products/{id}` | 200 · 404 |
| `PATCH` | `/api/products/{id}` | 200 partial update · 404 · 422 |

Rules: the SKU is trimmed and uppercased, must match `^[A-Z0-9][A-Z0-9_-]{0,63}$`,
is unique (case-insensitive in practice) and cannot be changed after creation.
`name` is 1–255 characters, `description` is optional (up to 2000 characters),
and `unit_price` is a non-negative decimal with 2 places.

## Adding a feature

Follow the product module's layering:

1. ORM model in `app/db/models/`, imported in `app/db/models/__init__.py`, then
   an Alembic revision.
2. Pydantic schemas in `app/schemas/`.
3. Queries in `app/repositories/`, business rules in `app/services/`.
4. A thin router in `app/api/routes/`, registered in `app/api/router.py`.
5. Analytics or agent logic in `app/analytics/` / `app/agents/`, called from services.
6. Frontend API calls in `frontend/src/api/`, data fetched with React Query.

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

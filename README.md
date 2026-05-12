# Trading System

Scaffold for a trading system workspace.

## Structure

```text
trading-system/
├── backend/              # FastAPI
├── engine/               # Trading engine, separate process
├── shared/               # Shared Python code
├── research/             # Jupyter notebooks
├── frontend/             # Next.js
├── docker-compose.yml
├── .env.example
└── README.md
```

## Start Services

Copy the example environment file and fill in real secrets locally:

```bash
cp .env.example .env
```

Start PostgreSQL 16 with TimescaleDB and Redis 7:

```bash
docker compose up -d
```

PostgreSQL is exposed on `localhost:5432`.
Redis is exposed on `localhost:6379`.

## Set Up Backend

Install backend dependencies with uv:

```bash
cd backend
uv sync
```

Run database migrations:

```bash
uv run alembic upgrade head
```

Ingest market data for a ticker list:

```bash
uv run python -m app.scripts.ingest --tickers JNJ,KO,PG,MMM,WMT
```

When application code is added, run the FastAPI backend with uvicorn:

```bash
uv run uvicorn app.main:app --reload
```

No application code has been added yet.

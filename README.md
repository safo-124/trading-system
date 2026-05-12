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

Run the FastAPI backend with uvicorn:

```bash
uv run uvicorn app.main:app --reload
```

Useful local API checks:

```bash
curl http://localhost:8000/api/stocks
curl -X POST http://localhost:8000/api/pipeline/run
```

Swagger UI is available at `http://localhost:8000/docs`.

## Python Research Environment

Create and activate the project virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

Register the virtual environment as a Jupyter kernel:

```bash
python -m ipykernel install --user --name trading-system --display-name "Python (trading-system)"
```

## Set Up Frontend

Install frontend dependencies:

```bash
cd frontend
npm install
```

Regenerate API types whenever the FastAPI schema changes:

```bash
npm run gen:api
```

Run the Next.js app:

```bash
npm run dev
```

The frontend runs at `http://localhost:3000` and uses `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8000`.

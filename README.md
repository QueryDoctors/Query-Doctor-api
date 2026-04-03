# PostgreSQL Performance Advisor

An insight-driven tool that connects to a PostgreSQL database, analyzes performance, detects issues, and suggests concrete optimizations.

## Stack

- **Backend**: FastAPI + asyncpg — Clean Architecture + DDD
- **Frontend**: Next.js 16 + TypeScript + Tailwind CSS + App Router

## Features

- Connect to any PostgreSQL database
- Real-time metrics: active connections, QPS, avg query time, total queries
- Slow, frequent, and heaviest query analysis
- Automated recommendations with severity levels (high / medium / low)

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL with `pg_stat_statements` enabled

```sql
-- postgresql.conf
shared_preload_libraries = 'pg_stat_statements'

-- In target database
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

## Getting Started

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/connect-db` | Connect to a PostgreSQL database |
| GET | `/metrics/{db_id}` | Fetch live performance metrics |
| GET | `/queries/{db_id}` | Fetch slow, frequent, and heaviest queries |
| GET | `/recommendations/{db_id}` | Get optimization recommendations |

## Running Tests

```bash
# Unit tests (no DB required)
pytest tests/unit -v

# Integration tests (requires test PostgreSQL DB)
pytest tests/integration -v

# E2E tests
pytest tests/e2e -v

# All with coverage
pytest --cov=app --cov-report=term-missing
```

## License

MIT — see [LICENSE](LICENSE)

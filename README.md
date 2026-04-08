# PostgreSQL Performance Advisor - Backend

FastAPI + asyncpg backend following Clean Architecture + DDD principles.

## Stack

- **Framework**: FastAPI 0.111
- **Database driver**: asyncpg (async PostgreSQL)
- **Time-series**: ClickHouse (via clickhouse-connect)
- **Auth**: JWT (python-jose + bcrypt)
- **Rate limiting**: slowapi
- **Validation**: Pydantic v2
- **Config**: pydantic-settings + dotenv

## Architecture

```
Presentation → Application → Domain ← Infrastructure
```

| Layer | Responsibility | Depends On |
|---|---|---|
| **Domain** | Entities, value objects, repository interfaces, domain services | Nothing |
| **Application** | Use cases, orchestration, DTOs | Domain only |
| **Infrastructure** | asyncpg repos, pool manager, ClickHouse client, config | Domain + Application |
| **Presentation** | FastAPI routers, Pydantic schemas, DI wiring | Application only |

Domain is pure Python - zero framework imports.

## Prerequisites

- Python 3.11+
- PostgreSQL with `pg_stat_statements` enabled
- ClickHouse (for incident detection time-series)

### PostgreSQL Setup

```sql
-- postgresql.conf
shared_preload_libraries = 'pg_stat_statements'

-- In target database
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
```

## Getting Started

```bash
# Create virtual environment
python -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # for testing

# Configure environment
cp .env.example .env.local
# Edit .env.local with your database credentials

# Run ClickHouse migrations
APP_ENV=local python -m clickhouse_migrations.runner

# Start the server
uvicorn app.main:app --reload --port 8000
```

## Environment Configuration

The app loads environment variables from dotenv files based on `APP_ENV`:

| APP_ENV | File | ClickHouse DB |
|---|---|---|
| `local` (default) | `.env.local` | `query-doctor-local` |
| `dev` | `.env.dev` | `query-doctor-dev` |
| `prod` | `.env.prod` | `query-doctor-prod` |

### Required Environment Variables

| Variable | Description |
|---|---|
| `APP_DATABASE_URL` | PostgreSQL connection string for the app DB |
| `ENCRYPTION_KEY` | Key for encrypting stored credentials |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens |

### Optional Variables

| Variable | Default | Description |
|---|---|---|
| `APP_HOST` | `0.0.0.0` | Server bind address |
| `APP_PORT` | `8000` | Server port |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |
| `CLICKHOUSE_HOST` | `localhost` | ClickHouse host |
| `CLICKHOUSE_PORT` | `8123` | ClickHouse HTTP port |
| `DETECTION_INTERVAL_SECONDS` | `10` | Incident detection cycle interval |

## API Endpoints

### Public

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login, returns JWT tokens |

### Protected (JWT required)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/connect-db` | Connect to a PostgreSQL database |
| GET | `/metrics/{db_id}` | Fetch live performance metrics |
| GET | `/queries/{db_id}` | Slow, frequent, and heaviest queries |
| GET | `/recommendations/{db_id}` | Optimization recommendations |
| POST | `/snapshots` | Capture a query latency snapshot |
| GET | `/incidents/{db_id}` | Get detected incidents |
| GET | `/logs/{db_id}` | Query logs |
| * | `/saved-connections/*` | CRUD for saved connections |

## Real-time Events

The backend listens for PostgreSQL `NOTIFY` events from the Go detector service:

- `incident_update` - new/updated incidents
- `query_update` - query stat changes

These are broadcast to connected WebSocket clients.

## Testing

```bash
# Unit tests (no DB required)
pytest tests/unit -v

# Integration tests (requires test PostgreSQL)
pytest tests/integration -v

# E2E tests
pytest tests/e2e -v

# All tests with coverage
pytest --cov=app --cov-report=term-missing

# Skip integration tests
pytest -m "not integration" -v
```

### Test Pyramid

| Layer | Location | Dependencies |
|---|---|---|
| Unit - Domain | `tests/unit/domain/` | None (pure Python) |
| Unit - Application | `tests/unit/application/` | Mocked repositories |
| Integration | `tests/integration/` | Real PostgreSQL |
| E2E | `tests/e2e/` | FastAPI TestClient |

## Domain Model

### Entities

- **DatabaseConnection** - connected DB session (id, config, connected_at)
- **QueryStat** - normalized query with timing stats
- **Recommendation** - problem + impact + suggestion + severity
- **Incident** - detected performance anomaly with severity/status tracking
- **MutedQuery** - queries excluded from incident detection
- **QueryLatencySnapshot** - time-series latency data (stored in ClickHouse)

### Recommendation Engine Rules

| Rule | Condition | Severity |
|---|---|---|
| Slow query | `mean_time_ms > 200` AND `calls > 100` | HIGH |
| High total time | Top of heaviest queries | MEDIUM |
| Full table scan | `rows / calls > 10,000` | HIGH |
| Too many connections | `active_connections > 80` | HIGH |
| Low QPS + high latency | `qps < 10` AND `avg_query_time_ms > 500` | MEDIUM |

## License

MIT

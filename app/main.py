from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config import get_settings
from app.presentation.routers import connection, metrics, queries, recommendations
from app.presentation.routers import saved_connections, snapshots, logs
from app.presentation.dependencies import get_app_pg_manager

# ─── App-level singletons (shared across requests) ───────────────────────────
# Reuse the AppPgManager singleton that dependencies.py already owns
_app_pg_manager = get_app_pg_manager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to app database
    settings = get_settings()
    await _app_pg_manager.connect(settings)
    print(f"[startup] env={settings.env.value} | app DB connected")
    yield
    # Shutdown: close app database pool
    await _app_pg_manager.close()
    print("[shutdown] app DB pool closed")


# ─── FastAPI app ──────────────────────────────────────────────────────────────
# Settings loaded lazily inside lifespan — safe to import in tests without .env
app = FastAPI(
    title="PostgreSQL Performance Advisor",
    version="1.0.0",
    description="Insight-driven PostgreSQL performance analysis tool",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(connection.router)
app.include_router(metrics.router)
app.include_router(queries.router)
app.include_router(recommendations.router)
app.include_router(saved_connections.router)
app.include_router(snapshots.router)
app.include_router(logs.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}

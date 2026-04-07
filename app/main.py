import asyncio
import logging
from contextlib import asynccontextmanager

import asyncpg
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.infrastructure.config import get_settings
from app.presentation.routers import auth, connection, incidents as incidents_router
from app.presentation.routers import logs, metrics, queries, recommendations
from app.presentation.routers import saved_connections, snapshots
from app.presentation.dependencies import (
    get_app_pg_manager,
    get_current_user,
    get_pool_manager,
    get_ws_manager,
)

logger = logging.getLogger(__name__)

# ─── App-level singletons ─────────────────────────────────────────────────────
_app_pg_manager = get_app_pg_manager()
_pool_manager = get_pool_manager()
_ws_manager = get_ws_manager()

# Dedicated asyncpg connection for LISTEN (separate from the pool)
_notify_conn: asyncpg.Connection | None = None


async def _on_incident_notify(conn, pid, channel, payload: str) -> None:
    """Called by asyncpg when Go detector sends pg_notify('incident_update', db_id)."""
    try:
        await _ws_manager.broadcast(payload, "incident_update")
    except Exception as exc:
        logger.warning(f"[notify] incident broadcast failed for db_id={payload}: {exc}")


async def _on_query_notify(conn, pid, channel, payload: str) -> None:
    """Called by asyncpg when Go detector sends pg_notify('query_update', db_id)."""
    try:
        await _ws_manager.broadcast(payload, "query_update")
    except Exception as exc:
        logger.warning(f"[notify] query broadcast failed for db_id={payload}: {exc}")


async def _cleanup_refresh_tokens() -> None:
    from app.infrastructure.persistence.repositories.pg_refresh_token_repository import PgRefreshTokenRepository
    while True:
        await asyncio.sleep(3600)
        repo = PgRefreshTokenRepository(_app_pg_manager)
        deleted = await repo.delete_expired()
        logger.info(f"[cleanup] {deleted} expired/revoked refresh tokens deleted")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _notify_conn
    settings = get_settings()

    # ── Startup ───────────────────────────────────────────────────────────────
    await _app_pg_manager.connect(settings)
    logger.info(f"[startup] env={settings.env.value} | app DB connected")

    asyncio.create_task(_cleanup_refresh_tokens())

    # Open a dedicated connection for LISTEN — must NOT be from the pool
    _notify_conn = await asyncpg.connect(settings.app_database_url, ssl="disable")
    await _notify_conn.add_listener("incident_update", _on_incident_notify)
    await _notify_conn.add_listener("query_update", _on_query_notify)
    logger.info("[startup] LISTEN incident_update + query_update active")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    if _notify_conn:
        await _notify_conn.remove_listener("incident_update", _on_incident_notify)
        await _notify_conn.remove_listener("query_update", _on_query_notify)
        await _notify_conn.close()
        logger.info("[shutdown] LISTEN connection closed")

    await _app_pg_manager.close()
    logger.info("[shutdown] app DB pool closed")


# ─── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="PostgreSQL Performance Advisor",
    version="1.0.0",
    description="Insight-driven PostgreSQL performance analysis tool",
    lifespan=lifespan,
)

# Rate limiter (IP-based, in-memory)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth router — public
app.include_router(auth.router)

# Protected routers — JWT required
_auth_dep = [Depends(get_current_user)]
app.include_router(connection.router,         dependencies=_auth_dep)
app.include_router(metrics.router,            dependencies=_auth_dep)
app.include_router(queries.router,            dependencies=_auth_dep)
app.include_router(recommendations.router,    dependencies=_auth_dep)
app.include_router(saved_connections.router,  dependencies=_auth_dep)
app.include_router(snapshots.router,          dependencies=_auth_dep)
app.include_router(logs.router,               dependencies=_auth_dep)
app.include_router(incidents_router.router,   dependencies=_auth_dep)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}

import asyncpg
from fastapi import APIRouter, Depends, HTTPException

from app.presentation.schemas.connection_schema import (
    ConnectRequest,
    ConnectResponse,
    TestConnectionResponse,
)
from app.application.use_cases.connect_database import ConnectDatabaseUseCase
from app.application.dtos.connection_dto import ConnectRequest as ConnectRequestDTO
from app.presentation.dependencies import get_connect_use_case

router = APIRouter(tags=["connection"])


@router.post("/connect-db", response_model=ConnectResponse)
async def connect_db(
    body: ConnectRequest,
    use_case: ConnectDatabaseUseCase = Depends(get_connect_use_case),
) -> ConnectResponse:
    try:
        result = await use_case.execute(ConnectRequestDTO(
            host=body.host,
            port=body.port,
            database=body.database,
            user=body.user,
            password=body.password,
        ))
        return ConnectResponse(db_id=result.db_id, status=result.status)
    except RuntimeError as exc:
        # Domain validation failures (pg_stat_statements, etc.) → 400 with clear message
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Connection failed: {exc}") from exc


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(body: ConnectRequest) -> TestConnectionResponse:
    """
    Open a single temporary connection, run a ping query, check pg_stat_statements,
    then close immediately. Nothing is persisted — no db_id is created.
    """
    conn = None
    try:
        conn = await asyncpg.connect(
            host=body.host,
            port=body.port,
            database=body.database,
            user=body.user,
            password=body.password,
            ssl="prefer",
            timeout=15,
        )

        # Basic ping
        await conn.fetchval("SELECT 1")

        # Check pg_stat_statements
        try:
            await conn.fetchval("SELECT count(*) FROM pg_stat_statements LIMIT 1")
        except (asyncpg.UndefinedTableError, asyncpg.UndefinedFunctionError):
            return TestConnectionResponse(
                success=False,
                message=(
                    "Connected, but pg_stat_statements is not enabled. "
                    "Run: CREATE EXTENSION pg_stat_statements; "
                    "(may also require adding it to shared_preload_libraries and restarting)"
                ),
            )

        return TestConnectionResponse(success=True, message="Connection successful")

    except asyncpg.InvalidPasswordError:
        return TestConnectionResponse(success=False, message="Invalid username or password")
    except asyncpg.InvalidCatalogNameError:
        return TestConnectionResponse(success=False, message=f'Database "{body.database}" does not exist')
    except OSError as exc:
        return TestConnectionResponse(success=False, message=f"Cannot reach host: {body.host}:{body.port} — {exc}")
    except Exception as exc:
        return TestConnectionResponse(success=False, message=str(exc))
    finally:
        if conn:
            await conn.close()

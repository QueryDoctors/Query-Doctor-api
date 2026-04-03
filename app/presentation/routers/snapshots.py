from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.presentation.schemas.snapshot_schema import (
    SnapshotResponse,
    SnapshotQuerySchema,
    SnapshotRecommendationSchema,
    ListSnapshotsResponse,
)
from app.application.use_cases.save_snapshot import SaveSnapshotUseCase
from app.application.use_cases.get_snapshot import GetSnapshotUseCase
from app.application.use_cases.list_snapshots import ListSnapshotsUseCase
from app.presentation.dependencies import (
    get_save_snapshot_use_case,
    get_get_snapshot_use_case,
    get_list_snapshots_use_case,
)

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.post("/{db_id}", response_model=SnapshotResponse, status_code=201)
async def capture_snapshot(
    db_id: str,
    connection_id: str = Query(..., description="Saved connection ID to associate this snapshot with"),
    use_case: SaveSnapshotUseCase = Depends(get_save_snapshot_use_case),
) -> SnapshotResponse:
    try:
        result = await use_case.execute(db_id=db_id, connection_id=connection_id)
        return _to_response(result)
    except KeyError:
        raise HTTPException(status_code=404, detail="Active database connection not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/{snapshot_id}", response_model=SnapshotResponse)
async def get_snapshot(
    snapshot_id: str,
    use_case: GetSnapshotUseCase = Depends(get_get_snapshot_use_case),
) -> SnapshotResponse:
    result = await use_case.execute(snapshot_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return _to_response(result)


@router.get("", response_model=ListSnapshotsResponse)
async def list_snapshots(
    connection_id: str = Query(..., description="Saved connection ID to list snapshots for"),
    use_case: ListSnapshotsUseCase = Depends(get_list_snapshots_use_case),
) -> ListSnapshotsResponse:
    result = await use_case.execute(connection_id)
    return ListSnapshotsResponse(snapshots=[_to_response(s) for s in result.snapshots])


def _to_response(r) -> SnapshotResponse:
    return SnapshotResponse(
        id=r.id,
        connection_id=r.connection_id,
        captured_at=r.captured_at,
        active_connections=r.active_connections,
        qps=r.qps,
        avg_query_time_ms=r.avg_query_time_ms,
        total_queries=r.total_queries,
        queries=[
            SnapshotQuerySchema(
                id=q.id, category=q.category, query=q.query,
                mean_time_ms=q.mean_time_ms, calls=q.calls,
                total_time_ms=q.total_time_ms, rows=q.rows,
            )
            for q in r.queries
        ],
        recommendations=[
            SnapshotRecommendationSchema(
                id=rec.id, problem=rec.problem, impact=rec.impact,
                suggestion=rec.suggestion, severity=rec.severity,
            )
            for rec in r.recommendations
        ],
    )

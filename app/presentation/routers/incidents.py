import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from app.application.use_cases.get_incidents import GetIncidentsUseCase
from app.application.use_cases.acknowledge_incident import AcknowledgeIncidentUseCase
from app.application.use_cases.resolve_incident import ResolveIncidentUseCase
from app.application.use_cases.mute_query import MuteQueryUseCase
from app.application.use_cases.unmute_query import UnmuteQueryUseCase
from app.infrastructure.clickhouse.ch_training_repo import ChTrainingRepo
from app.infrastructure.websocket.manager import WebSocketManager
from app.presentation.schemas.incident_schema import IncidentResponse, IncidentsListResponse
from app.presentation.dependencies import (
    get_incidents_use_case,
    get_acknowledge_incident_use_case,
    get_resolve_incident_use_case,
    get_mute_query_use_case,
    get_unmute_query_use_case,
    get_ch_training_repo,
    get_ws_manager,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/{db_id}", response_model=IncidentsListResponse)
async def list_incidents(
    db_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    use_case: GetIncidentsUseCase = Depends(get_incidents_use_case),
):
    result = await use_case.execute(db_id, limit, offset)
    return IncidentsListResponse(
        incidents=[IncidentResponse(**vars(i)) for i in result.incidents],
        total=result.total,
    )


@router.patch("/{incident_id}/acknowledge", response_model=IncidentResponse)
async def acknowledge_incident(
    incident_id: str,
    use_case: AcknowledgeIncidentUseCase = Depends(get_acknowledge_incident_use_case),
    training_repo: ChTrainingRepo = Depends(get_ch_training_repo),
    ws_manager: WebSocketManager = Depends(get_ws_manager),
):
    try:
        dto = await use_case.execute(incident_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    await ws_manager.broadcast(dto.db_id, "incident_update")
    asyncio.create_task(asyncio.to_thread(
        training_repo.write_outcome, incident_id, "acknowledged", dto.db_id, dto.query_hash,
    ))
    return IncidentResponse(**vars(dto))


@router.patch("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: str,
    use_case: ResolveIncidentUseCase = Depends(get_resolve_incident_use_case),
    training_repo: ChTrainingRepo = Depends(get_ch_training_repo),
    ws_manager: WebSocketManager = Depends(get_ws_manager),
):
    try:
        dto = await use_case.execute(incident_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    await ws_manager.broadcast(dto.db_id, "incident_update")
    resolution_time_s = 0
    if dto.resolved_at and dto.start_time:
        resolution_time_s = int((dto.resolved_at - dto.start_time).total_seconds())
    asyncio.create_task(asyncio.to_thread(
        training_repo.write_outcome,
        incident_id, "resolved", dto.db_id, dto.query_hash, resolution_time_s,
    ))
    return IncidentResponse(**vars(dto))


@router.post("/queries/{db_id}/{query_hash}/mute", status_code=204)
async def mute_query(
    db_id: str,
    query_hash: str,
    use_case: MuteQueryUseCase = Depends(get_mute_query_use_case),
    training_repo: ChTrainingRepo = Depends(get_ch_training_repo),
    ws_manager: WebSocketManager = Depends(get_ws_manager),
):
    await use_case.execute(query_hash, db_id, whitelist=False)
    await ws_manager.broadcast(db_id, "incident_update")
    asyncio.create_task(asyncio.to_thread(
        training_repo.write_outcome, "", "muted", db_id, query_hash,
    ))


@router.delete("/queries/{db_id}/{query_hash}/mute", status_code=204)
async def unmute_query(
    db_id: str,
    query_hash: str,
    use_case: UnmuteQueryUseCase = Depends(get_unmute_query_use_case),
    ws_manager: WebSocketManager = Depends(get_ws_manager),
):
    await use_case.execute(query_hash, db_id)
    await ws_manager.broadcast(db_id, "incident_update")


@router.post("/queries/{db_id}/{query_hash}/whitelist", status_code=204)
async def whitelist_query(
    db_id: str,
    query_hash: str,
    use_case: MuteQueryUseCase = Depends(get_mute_query_use_case),
    training_repo: ChTrainingRepo = Depends(get_ch_training_repo),
    ws_manager: WebSocketManager = Depends(get_ws_manager),
):
    await use_case.execute(query_hash, db_id, whitelist=True)
    await ws_manager.broadcast(db_id, "incident_update")
    asyncio.create_task(asyncio.to_thread(
        training_repo.write_outcome, "", "whitelisted", db_id, query_hash,
    ))


@router.websocket("/ws/{db_id}")
async def incidents_ws(
    db_id: str,
    ws: WebSocket,
    ws_manager: WebSocketManager = Depends(get_ws_manager),
):
    await ws_manager.connect(db_id, ws)
    try:
        # Keep connection alive; client sends pings, server echoes pong
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(db_id, ws)
    except Exception as exc:
        logger.error(f"[ws] error db_id={db_id}: {exc}")
        ws_manager.disconnect(db_id, ws)

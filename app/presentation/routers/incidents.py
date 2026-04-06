from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.use_cases.get_incidents import GetIncidentsUseCase
from app.application.use_cases.acknowledge_incident import AcknowledgeIncidentUseCase
from app.application.use_cases.resolve_incident import ResolveIncidentUseCase
from app.application.use_cases.mute_query import MuteQueryUseCase
from app.application.use_cases.unmute_query import UnmuteQueryUseCase
from app.presentation.schemas.incident_schema import IncidentResponse, IncidentsListResponse
from app.presentation.dependencies import (
    get_incidents_use_case,
    get_acknowledge_incident_use_case,
    get_resolve_incident_use_case,
    get_mute_query_use_case,
    get_unmute_query_use_case,
)

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
):
    try:
        dto = await use_case.execute(incident_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return IncidentResponse(**vars(dto))


@router.patch("/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: str,
    use_case: ResolveIncidentUseCase = Depends(get_resolve_incident_use_case),
):
    try:
        dto = await use_case.execute(incident_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return IncidentResponse(**vars(dto))


@router.post("/queries/{db_id}/{query_hash}/mute", status_code=204)
async def mute_query(
    db_id: str,
    query_hash: str,
    use_case: MuteQueryUseCase = Depends(get_mute_query_use_case),
):
    await use_case.execute(query_hash, db_id, whitelist=False)


@router.delete("/queries/{db_id}/{query_hash}/mute", status_code=204)
async def unmute_query(
    db_id: str,
    query_hash: str,
    use_case: UnmuteQueryUseCase = Depends(get_unmute_query_use_case),
):
    await use_case.execute(query_hash, db_id)


@router.post("/queries/{db_id}/{query_hash}/whitelist", status_code=204)
async def whitelist_query(
    db_id: str,
    query_hash: str,
    use_case: MuteQueryUseCase = Depends(get_mute_query_use_case),
):
    await use_case.execute(query_hash, db_id, whitelist=True)

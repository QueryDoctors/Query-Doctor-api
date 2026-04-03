from fastapi import APIRouter, Depends, HTTPException

from app.presentation.schemas.saved_connection_schema import (
    SavedConnectionRequest,
    SavedConnectionResponse,
    ListSavedConnectionsResponse,
)
from app.application.use_cases.save_saved_connection import SaveSavedConnectionUseCase
from app.application.use_cases.get_saved_connection import GetSavedConnectionUseCase
from app.application.use_cases.list_saved_connections import ListSavedConnectionsUseCase
from app.application.use_cases.delete_saved_connection import DeleteSavedConnectionUseCase
from app.application.dtos.saved_connection_dto import SavedConnectionRequest as SavedConnectionDTO
from app.presentation.dependencies import (
    get_save_saved_connection_use_case,
    get_get_saved_connection_use_case,
    get_list_saved_connections_use_case,
    get_delete_saved_connection_use_case,
)

router = APIRouter(prefix="/saved-connections", tags=["saved-connections"])


@router.post("", response_model=SavedConnectionResponse, status_code=201)
async def create_saved_connection(
    body: SavedConnectionRequest,
    use_case: SaveSavedConnectionUseCase = Depends(get_save_saved_connection_use_case),
) -> SavedConnectionResponse:
    try:
        result = await use_case.execute(SavedConnectionDTO(
            name=body.name, host=body.host, port=body.port,
            database=body.database, user=body.user, password=body.password,
        ))
        return _to_response(result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("", response_model=ListSavedConnectionsResponse)
async def list_saved_connections(
    use_case: ListSavedConnectionsUseCase = Depends(get_list_saved_connections_use_case),
) -> ListSavedConnectionsResponse:
    result = await use_case.execute()
    return ListSavedConnectionsResponse(
        connections=[_to_response(c) for c in result.connections]
    )


@router.get("/{connection_id}", response_model=SavedConnectionResponse)
async def get_saved_connection(
    connection_id: str,
    use_case: GetSavedConnectionUseCase = Depends(get_get_saved_connection_use_case),
) -> SavedConnectionResponse:
    result = await use_case.execute(connection_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Saved connection not found")
    return _to_response(result)


@router.delete("/{connection_id}", status_code=204)
async def delete_saved_connection(
    connection_id: str,
    use_case: DeleteSavedConnectionUseCase = Depends(get_delete_saved_connection_use_case),
) -> None:
    try:
        await use_case.execute(connection_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Saved connection not found")


def _to_response(r) -> SavedConnectionResponse:
    return SavedConnectionResponse(
        id=r.id, name=r.name, host=r.host, port=r.port,
        database=r.database, user=r.user,
        created_at=r.created_at, last_used=r.last_used,
    )

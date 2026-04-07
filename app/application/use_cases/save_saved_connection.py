import uuid
from datetime import datetime, timezone

from app.domain.repositories.connection_store_repository import IConnectionStoreRepository
from app.domain.entities.saved_connection import SavedConnection
from app.application.dtos.saved_connection_dto import SavedConnectionRequest, SavedConnectionResult


class SaveSavedConnectionUseCase:
    def __init__(self, repo: IConnectionStoreRepository) -> None:
        self._repo = repo

    async def execute(self, request: SavedConnectionRequest) -> SavedConnectionResult:
        connection = SavedConnection(
            id=str(uuid.uuid4()),
            user_id=request.user_id,
            name=request.name,
            host=request.host,
            port=request.port,
            database=request.database,
            user=request.user,
            password=request.password,
            created_at=datetime.now(timezone.utc),
        )
        saved = await self._repo.save(connection)
        return _to_result(saved)


def _to_result(c: SavedConnection) -> SavedConnectionResult:
    return SavedConnectionResult(
        id=c.id,
        name=c.name,
        host=c.host,
        port=c.port,
        database=c.database,
        user=c.user,
        created_at=c.created_at,
        last_used=c.last_used,
    )

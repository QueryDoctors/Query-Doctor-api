from typing import Optional

from app.domain.repositories.connection_store_repository import IConnectionStoreRepository
from app.application.dtos.saved_connection_dto import SavedConnectionResult
from app.domain.entities.saved_connection import SavedConnection


class GetSavedConnectionUseCase:
    def __init__(self, repo: IConnectionStoreRepository) -> None:
        self._repo = repo

    async def execute(self, connection_id: str) -> Optional[SavedConnectionResult]:
        connection = await self._repo.get_by_id(connection_id)
        if connection is None:
            return None
        return _to_result(connection)


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

from app.domain.repositories.connection_store_repository import IConnectionStoreRepository
from app.application.dtos.saved_connection_dto import SavedConnectionResult, ListSavedConnectionsResult
from app.domain.entities.saved_connection import SavedConnection


class ListSavedConnectionsUseCase:
    def __init__(self, repo: IConnectionStoreRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: str) -> ListSavedConnectionsResult:
        connections = await self._repo.list_all(user_id)
        return ListSavedConnectionsResult(
            connections=[_to_result(c) for c in connections]
        )


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

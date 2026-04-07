from app.domain.repositories.connection_store_repository import IConnectionStoreRepository


class DeleteSavedConnectionUseCase:
    def __init__(self, repo: IConnectionStoreRepository) -> None:
        self._repo = repo

    async def execute(self, connection_id: str, user_id: str) -> None:
        existing = await self._repo.get_by_id(connection_id)
        if existing is None or existing.user_id != user_id:
            raise KeyError(f"Saved connection not found: {connection_id}")
        await self._repo.delete(connection_id, user_id)

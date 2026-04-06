from app.domain.repositories.muted_query_repository import IMutedQueryRepository


class UnmuteQueryUseCase:

    def __init__(self, repo: IMutedQueryRepository) -> None:
        self._repo = repo

    async def execute(self, query_hash: str, db_id: str) -> None:
        await self._repo.unmute(query_hash, db_id)

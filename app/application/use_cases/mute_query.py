from app.domain.repositories.muted_query_repository import IMutedQueryRepository


class MuteQueryUseCase:

    def __init__(self, repo: IMutedQueryRepository) -> None:
        self._repo = repo

    async def execute(self, query_hash: str, db_id: str, whitelist: bool = False) -> None:
        if whitelist:
            await self._repo.whitelist(query_hash, db_id)
        else:
            await self._repo.mute(query_hash, db_id)

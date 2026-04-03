from app.domain.repositories.query_repository import IQueryRepository
from app.domain.entities.query_stat import QueryStat
from app.application.dtos.query_dto import QueryStatDTO, QueriesResult


def _to_dto(q: QueryStat) -> QueryStatDTO:
    return QueryStatDTO(
        query=q.query,
        mean_time=q.mean_time_ms,
        calls=q.calls,
        total_time=q.total_time_ms,
        rows=q.rows,
    )


class GetQueriesUseCase:
    def __init__(self, query_repo: IQueryRepository) -> None:
        self._query_repo = query_repo

    async def execute(self, db_id: str) -> QueriesResult:
        slow = await self._query_repo.fetch_slow(db_id)
        frequent = await self._query_repo.fetch_frequent(db_id)
        heaviest = await self._query_repo.fetch_heaviest(db_id)
        return QueriesResult(
            slow_queries=[_to_dto(q) for q in slow],
            frequent_queries=[_to_dto(q) for q in frequent],
            heaviest_queries=[_to_dto(q) for q in heaviest],
        )

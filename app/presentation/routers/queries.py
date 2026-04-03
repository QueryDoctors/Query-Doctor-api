from fastapi import APIRouter, Depends, HTTPException

from app.presentation.schemas.query_schema import QueriesResponse, QueryStatSchema
from app.application.use_cases.get_queries import GetQueriesUseCase
from app.application.dtos.query_dto import QueryStatDTO
from app.presentation.dependencies import get_queries_use_case

router = APIRouter(tags=["queries"])


def _to_schema(q: QueryStatDTO) -> QueryStatSchema:
    return QueryStatSchema(
        query=q.query,
        mean_time=q.mean_time,
        calls=q.calls,
        total_time=q.total_time,
        rows=q.rows,
    )


@router.get("/queries/{db_id}", response_model=QueriesResponse)
async def get_queries(
    db_id: str,
    use_case: GetQueriesUseCase = Depends(get_queries_use_case),
) -> QueriesResponse:
    try:
        result = await use_case.execute(db_id)
        return QueriesResponse(
            slow_queries=[_to_schema(q) for q in result.slow_queries],
            frequent_queries=[_to_schema(q) for q in result.frequent_queries],
            heaviest_queries=[_to_schema(q) for q in result.heaviest_queries],
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Database connection not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

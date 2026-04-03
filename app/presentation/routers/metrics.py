from fastapi import APIRouter, Depends, HTTPException

from app.presentation.schemas.metrics_schema import MetricsResponse
from app.application.use_cases.get_metrics import GetMetricsUseCase
from app.presentation.dependencies import get_metrics_use_case

router = APIRouter(tags=["metrics"])


@router.get("/metrics/{db_id}", response_model=MetricsResponse)
async def get_metrics(
    db_id: str,
    use_case: GetMetricsUseCase = Depends(get_metrics_use_case),
) -> MetricsResponse:
    try:
        result = await use_case.execute(db_id)
        return MetricsResponse(
            active_connections=result.active_connections,
            qps=result.qps,
            avg_query_time_ms=result.avg_query_time_ms,
            total_queries=result.total_queries,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Database connection not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

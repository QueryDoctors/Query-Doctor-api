from fastapi import APIRouter, Depends, HTTPException

from app.presentation.schemas.recommendation_schema import RecommendationsResponse, RecommendationSchema
from app.application.use_cases.get_recommendations import GetRecommendationsUseCase
from app.application.dtos.recommendation_dto import RecommendationDTO
from app.presentation.dependencies import get_recommendations_use_case

router = APIRouter(tags=["recommendations"])


def _to_schema(r: RecommendationDTO) -> RecommendationSchema:
    return RecommendationSchema(
        problem=r.problem,
        impact=r.impact,
        suggestion=r.suggestion,
        severity=r.severity,
    )


@router.get("/recommendations/{db_id}", response_model=RecommendationsResponse)
async def get_recommendations(
    db_id: str,
    use_case: GetRecommendationsUseCase = Depends(get_recommendations_use_case),
) -> RecommendationsResponse:
    try:
        result = await use_case.execute(db_id)
        return RecommendationsResponse(
            recommendations=[_to_schema(r) for r in result.recommendations]
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Database connection not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

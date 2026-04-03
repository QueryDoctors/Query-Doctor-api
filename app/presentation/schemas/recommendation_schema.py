from pydantic import BaseModel
from typing import List


class RecommendationSchema(BaseModel):
    problem: str
    impact: str
    suggestion: str
    severity: str


class RecommendationsResponse(BaseModel):
    recommendations: List[RecommendationSchema]

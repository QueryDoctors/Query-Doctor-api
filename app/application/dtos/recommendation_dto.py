from dataclasses import dataclass
from typing import List


@dataclass
class RecommendationDTO:
    problem: str
    impact: str
    suggestion: str
    severity: str


@dataclass
class RecommendationsResult:
    recommendations: List[RecommendationDTO]

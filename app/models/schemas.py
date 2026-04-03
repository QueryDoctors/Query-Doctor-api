from pydantic import BaseModel
from typing import Optional, List


class ConnectionRequest(BaseModel):
    host: str
    port: int = 5432
    database: str
    user: str
    password: str


class ConnectionResponse(BaseModel):
    db_id: str
    status: str


class MetricsResponse(BaseModel):
    active_connections: int
    qps: float
    avg_query_time_ms: float
    total_queries: int


class QueryStat(BaseModel):
    query: str
    mean_time: float
    calls: int
    total_time: float
    rows: Optional[int] = None


class QueriesResponse(BaseModel):
    slow_queries: List[QueryStat]
    frequent_queries: List[QueryStat]
    heaviest_queries: List[QueryStat]


class Recommendation(BaseModel):
    problem: str
    impact: str
    suggestion: str
    severity: str  # "high" | "medium" | "low"


class RecommendationsResponse(BaseModel):
    recommendations: List[Recommendation]

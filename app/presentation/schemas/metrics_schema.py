from pydantic import BaseModel


class MetricsResponse(BaseModel):
    active_connections: int
    qps: float
    avg_query_time_ms: float
    total_queries: int

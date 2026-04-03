from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class SnapshotQuerySchema(BaseModel):
    id: str
    category: str
    query: str
    mean_time_ms: Optional[float] = None
    calls: Optional[int] = None
    total_time_ms: Optional[float] = None
    rows: Optional[int] = None


class SnapshotRecommendationSchema(BaseModel):
    id: str
    problem: str
    impact: str
    suggestion: str
    severity: str


class SnapshotResponse(BaseModel):
    id: str
    connection_id: str
    captured_at: datetime
    active_connections: Optional[int] = None
    qps: Optional[float] = None
    avg_query_time_ms: Optional[float] = None
    total_queries: Optional[int] = None
    queries: List[SnapshotQuerySchema] = []
    recommendations: List[SnapshotRecommendationSchema] = []


class ListSnapshotsResponse(BaseModel):
    snapshots: List[SnapshotResponse]

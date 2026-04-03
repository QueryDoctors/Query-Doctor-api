from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class SnapshotQueryDTO:
    id: str
    category: str
    query: str
    mean_time_ms: Optional[float] = None
    calls: Optional[int] = None
    total_time_ms: Optional[float] = None
    rows: Optional[int] = None


@dataclass
class SnapshotRecommendationDTO:
    id: str
    problem: str
    impact: str
    suggestion: str
    severity: str


@dataclass
class SnapshotResult:
    id: str
    connection_id: str
    captured_at: datetime
    active_connections: Optional[int] = None
    qps: Optional[float] = None
    avg_query_time_ms: Optional[float] = None
    total_queries: Optional[int] = None
    queries: List[SnapshotQueryDTO] = field(default_factory=list)
    recommendations: List[SnapshotRecommendationDTO] = field(default_factory=list)


@dataclass
class ListSnapshotsResult:
    snapshots: List[SnapshotResult]

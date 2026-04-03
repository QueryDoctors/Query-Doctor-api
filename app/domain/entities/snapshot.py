from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class SnapshotQuery:
    id: str
    category: str             # slow | frequent | heaviest
    query: str
    mean_time_ms: Optional[float] = None
    calls: Optional[int] = None
    total_time_ms: Optional[float] = None
    rows: Optional[int] = None


@dataclass
class SnapshotRecommendation:
    id: str
    problem: str
    impact: str
    suggestion: str
    severity: str             # high | medium | low


@dataclass
class Snapshot:
    id: str
    connection_id: str
    captured_at: datetime
    active_connections: Optional[int] = None
    qps: Optional[float] = None
    avg_query_time_ms: Optional[float] = None
    total_queries: Optional[int] = None
    queries: List[SnapshotQuery] = field(default_factory=list)
    recommendations: List[SnapshotRecommendation] = field(default_factory=list)

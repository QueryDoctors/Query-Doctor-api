from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class IncidentDTO:
    id: str
    db_id: str
    query_hash: str
    query_text: str
    severity: str
    status: str
    start_time: datetime
    last_updated: datetime
    current_latency_ms: float
    baseline_latency_ms: float
    latency_ratio: float
    calls_per_minute: float
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None


@dataclass
class IncidentsResult:
    incidents: List[IncidentDTO]
    total: int

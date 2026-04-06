from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.value_objects.severity import Severity
from app.domain.value_objects.incident_status import IncidentStatus


@dataclass
class Incident:
    id: str
    db_id: str
    query_hash: str
    query_text: str
    severity: Severity
    status: IncidentStatus
    start_time: datetime
    last_updated: datetime
    current_latency_ms: float
    baseline_latency_ms: float
    latency_ratio: float
    calls_per_minute: float
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None

from dataclasses import dataclass
from datetime import datetime


@dataclass
class QueryLatencySnapshot:
    db_id: str
    query_hash: str
    query_text: str
    mean_latency_ms: float
    calls: int
    calls_per_minute: float
    captured_at: datetime

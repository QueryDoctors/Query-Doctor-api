from dataclasses import dataclass
from typing import Optional


@dataclass
class QueryStat:
    query: str
    mean_time_ms: float
    calls: int
    total_time_ms: float
    rows: Optional[int] = None

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class QueryStatDTO:
    query: str
    mean_time: float
    calls: int
    total_time: float
    rows: Optional[int] = None


@dataclass
class QueriesResult:
    slow_queries: List[QueryStatDTO]
    frequent_queries: List[QueryStatDTO]
    heaviest_queries: List[QueryStatDTO]

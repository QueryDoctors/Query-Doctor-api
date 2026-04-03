from dataclasses import dataclass


@dataclass
class MetricsResult:
    active_connections: int
    qps: float
    avg_query_time_ms: float
    total_queries: int

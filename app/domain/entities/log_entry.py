from dataclasses import dataclass
from datetime import datetime


@dataclass
class LogEntry:
    pid: int
    username: str
    application_name: str
    state: str                      # active | idle in transaction | idle in transaction (aborted)
    query: str | None
    duration_ms: float | None       # None when query_start is NULL
    wait_event_type: str | None
    wait_event: str | None
    query_start: datetime | None

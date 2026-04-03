from dataclasses import dataclass
from datetime import datetime


@dataclass
class LogEntryDTO:
    pid: int
    username: str
    application_name: str
    state: str
    query: str | None
    duration_ms: float | None
    wait_event_type: str | None
    wait_event: str | None
    query_start: datetime | None

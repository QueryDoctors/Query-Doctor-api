from datetime import datetime
from pydantic import BaseModel


class LogEntrySchema(BaseModel):
    pid: int
    username: str
    application_name: str
    state: str
    query: str | None
    duration_ms: float | None
    wait_event_type: str | None
    wait_event: str | None
    query_start: datetime | None

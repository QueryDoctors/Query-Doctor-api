from dataclasses import dataclass
from datetime import datetime


@dataclass
class MutedQuery:
    query_hash: str
    db_id: str
    muted_at: datetime
    is_whitelisted: bool = False

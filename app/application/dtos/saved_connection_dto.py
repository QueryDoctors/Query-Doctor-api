from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class SavedConnectionRequest:
    user_id: str
    name: str
    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass
class SavedConnectionResult:
    id: str
    name: str
    host: str
    port: int
    database: str
    user: str
    created_at: datetime
    last_used: Optional[datetime] = None


@dataclass
class ListSavedConnectionsResult:
    connections: List[SavedConnectionResult]

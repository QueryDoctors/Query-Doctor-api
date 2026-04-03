from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class SavedConnectionRequest(BaseModel):
    name: str
    host: str
    port: int = 5432
    database: str
    user: str
    password: str


class SavedConnectionResponse(BaseModel):
    id: str
    name: str
    host: str
    port: int
    database: str
    user: str
    created_at: datetime
    last_used: Optional[datetime] = None


class ListSavedConnectionsResponse(BaseModel):
    connections: List[SavedConnectionResponse]

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SavedConnection:
    id: str
    user_id: str           # owner — scoped per authenticated user
    name: str
    host: str
    port: int
    database: str
    user: str
    password: str          # decrypted — never persisted as plaintext
    created_at: datetime
    last_used: Optional[datetime] = None

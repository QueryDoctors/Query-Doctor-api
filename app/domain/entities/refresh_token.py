from dataclasses import dataclass
from datetime import datetime


@dataclass
class RefreshToken:
    id: str
    user_id: str
    token_hash: str   # SHA-256 of the raw opaque token — raw token is never stored
    expires_at: datetime
    created_at: datetime
    revoked: bool

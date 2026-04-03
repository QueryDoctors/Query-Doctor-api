from dataclasses import dataclass
from datetime import datetime
from app.domain.value_objects.connection_config import ConnectionConfig


@dataclass
class DatabaseConnection:
    id: str
    config: ConnectionConfig
    connected_at: datetime

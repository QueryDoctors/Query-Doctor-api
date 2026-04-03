from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionConfig:
    host: str
    port: int
    database: str
    user: str
    password: str

from dataclasses import dataclass


@dataclass
class ConnectRequest:
    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass
class ConnectResult:
    db_id: str
    status: str

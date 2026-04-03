from pydantic import BaseModel


class ConnectRequest(BaseModel):
    host: str
    port: int = 5432
    database: str
    user: str
    password: str


class ConnectResponse(BaseModel):
    db_id: str
    status: str


class TestConnectionResponse(BaseModel):
    success: bool
    message: str

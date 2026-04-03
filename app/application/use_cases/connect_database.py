from app.domain.repositories.connection_repository import IConnectionRepository
from app.domain.value_objects.connection_config import ConnectionConfig
from app.application.dtos.connection_dto import ConnectRequest, ConnectResult


class ConnectDatabaseUseCase:
    def __init__(self, connection_repo: IConnectionRepository) -> None:
        self._connection_repo = connection_repo

    async def execute(self, request: ConnectRequest) -> ConnectResult:
        config = ConnectionConfig(
            host=request.host,
            port=request.port,
            database=request.database,
            user=request.user,
            password=request.password,
        )
        db_id = await self._connection_repo.create(config)
        return ConnectResult(db_id=db_id, status="connected")

from app.domain.repositories.log_repository import ILogRepository
from app.application.dtos.log_dto import LogEntryDTO


class GetLiveLogsUseCase:
    def __init__(self, log_repo: ILogRepository) -> None:
        self._log_repo = log_repo

    async def execute(self, db_id: str) -> list[LogEntryDTO]:
        entries = await self._log_repo.fetch(db_id)
        return [
            LogEntryDTO(
                pid=e.pid,
                username=e.username,
                application_name=e.application_name,
                state=e.state,
                query=e.query,
                duration_ms=e.duration_ms,
                wait_event_type=e.wait_event_type,
                wait_event=e.wait_event,
                query_start=e.query_start,
            )
            for e in entries
        ]

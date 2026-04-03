from fastapi import APIRouter, Depends, HTTPException

from app.presentation.schemas.log_schema import LogEntrySchema
from app.application.use_cases.get_live_logs import GetLiveLogsUseCase
from app.presentation.dependencies import get_live_logs_use_case

router = APIRouter(tags=["logs"])


@router.get("/logs/{db_id}", response_model=list[LogEntrySchema])
async def get_live_logs(
    db_id: str,
    use_case: GetLiveLogsUseCase = Depends(get_live_logs_use_case),
) -> list[LogEntrySchema]:
    try:
        entries = await use_case.execute(db_id)
        return [
            LogEntrySchema(
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
    except KeyError:
        raise HTTPException(status_code=404, detail="Active database connection not found")

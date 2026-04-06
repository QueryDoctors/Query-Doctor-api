import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DetectionScheduler:
    """
    Background asyncio task that runs the detection cycle for every
    actively connected db_id at a configurable interval (default 10s).
    Started/stopped in main.py lifespan.
    """

    def __init__(self, detection_use_case, pool_manager, interval_seconds: int = 10) -> None:
        self._use_case = detection_use_case
        self._pool_manager = pool_manager
        self._interval = interval_seconds
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop(), name="detection-scheduler")
        logger.info(f"[detection] scheduler started (interval={self._interval}s)")

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[detection] scheduler stopped")

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self._interval)
            db_ids = list(self._pool_manager.all_ids())
            for db_id in db_ids:
                try:
                    await self._use_case.execute(db_id)
                except Exception as exc:
                    logger.error(f"[detection] cycle error for db_id={db_id}: {exc}", exc_info=True)

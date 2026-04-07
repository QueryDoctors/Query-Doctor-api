import asyncio
import logging
from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages per-db_id WebSocket connections.
    Thread-safe via asyncio — all calls must run in the same event loop.
    """

    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, db_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._connections[db_id].add(ws)
        logger.debug(f"[ws] client connected db_id={db_id} total={len(self._connections[db_id])}")

    def disconnect(self, db_id: str, ws: WebSocket) -> None:
        self._connections[db_id].discard(ws)
        if not self._connections[db_id]:
            del self._connections[db_id]
        logger.debug(f"[ws] client disconnected db_id={db_id}")

    async def broadcast(self, db_id: str, message: str) -> None:
        """Send message to all connected clients for db_id. Dead connections are pruned."""
        dead: Set[WebSocket] = set()
        for ws in list(self._connections.get(db_id, set())):
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(db_id, ws)

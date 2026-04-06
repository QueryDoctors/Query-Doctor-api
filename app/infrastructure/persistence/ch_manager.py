import asyncio
from typing import Optional

import clickhouse_connect
import clickhouse_connect.driver.client

from app.infrastructure.config import Settings


class ClickHouseManager:
    """
    Manages a clickhouse-connect HTTP client (port 8123).
    Started/stopped in main.py lifespan alongside AppPgManager.
    """

    def __init__(self) -> None:
        self._client: Optional[clickhouse_connect.driver.client.Client] = None

    async def connect(self, settings: Settings) -> None:
        self._client = await asyncio.to_thread(
            clickhouse_connect.get_client,
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            database=settings.clickhouse_db,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
        )

    @property
    def client(self) -> clickhouse_connect.driver.client.Client:
        if self._client is None:
            raise RuntimeError("ClickHouseManager not connected. Call connect() first.")
        return self._client

    async def close(self) -> None:
        if self._client:
            await asyncio.to_thread(self._client.close)
            self._client = None

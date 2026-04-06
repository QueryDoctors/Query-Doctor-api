from abc import ABC, abstractmethod


class IMutedQueryRepository(ABC):

    @abstractmethod
    async def mute(self, query_hash: str, db_id: str) -> None: ...

    @abstractmethod
    async def unmute(self, query_hash: str, db_id: str) -> None: ...

    @abstractmethod
    async def whitelist(self, query_hash: str, db_id: str) -> None: ...

    @abstractmethod
    async def is_muted(self, query_hash: str, db_id: str) -> bool: ...

    @abstractmethod
    async def is_whitelisted(self, query_hash: str, db_id: str) -> bool: ...

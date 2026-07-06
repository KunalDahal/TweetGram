from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from tweetgrambot.app.config.settings import Settings


class Mongo:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncIOMotorClient | None = None

    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            self._client = AsyncIOMotorClient(
                self._settings.mongodb_uri,
                serverSelectionTimeoutMS=self._settings.mongodb_server_selection_timeout_ms,
            )
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        return self.client[self._settings.mongodb_database]

    async def ping(self) -> None:
        await self.client.admin.command("ping")

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

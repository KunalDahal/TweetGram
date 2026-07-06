from __future__ import annotations

from typing import Any

from twitter_telegram_bot.app.core.models import WorkerLog
from twitter_telegram_bot.app.database.repositories.base import MongoRepository


class LogsRepository(MongoRepository):
    collection_name = "worker_logs"

    async def write(self, log: WorkerLog) -> None:
        await self.collection.insert_one(log.model_dump())

    async def recent_for_account(self, account_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return await self.collection.find({"account_id": account_id}).sort("created_at", -1).limit(limit).to_list(limit)

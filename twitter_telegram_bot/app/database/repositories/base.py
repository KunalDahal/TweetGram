from __future__ import annotations

from typing import Any

from twitter_telegram_bot.app.utils.time import utc_now


class MongoRepository:
    collection_name: str

    def __init__(self, db) -> None:
        self.db = db
        self.collection = db[self.collection_name]

    async def delete_many(self, filter_: dict[str, Any]) -> int:
        result = await self.collection.delete_many(filter_)
        return int(result.deleted_count)

    async def touch(self, filter_: dict[str, Any], update: dict[str, Any]) -> None:
        update.setdefault("$set", {})["updated_at"] = utc_now()
        await self.collection.update_one(filter_, update)

from __future__ import annotations

from typing import Any

from twitter_telegram_bot.app.core.models import PostJob
from twitter_telegram_bot.app.database.repositories.base import MongoRepository
from twitter_telegram_bot.app.utils.time import utc_now


class PostJobsRepository(MongoRepository):
    collection_name = "post_jobs"

    async def create(self, job: PostJob) -> None:
        await self.collection.insert_one(job.model_dump())

    async def pending_for_account(self, account_id: str) -> list[dict[str, Any]]:
        return await self.collection.find(
            {"account_id": account_id, "status": {"$nin": ["telegram_sent", "cancelled"]}}
        ).sort("created_at", 1).to_list(None)

    async def pending_for_list(self, account_id: str, twitter_list_id: str) -> list[dict[str, Any]]:
        return await self.collection.find(
            {
                "account_id": account_id,
                "twitter_list_id": twitter_list_id,
                "status": {"$nin": ["telegram_sent", "cancelled"]},
            }
        ).sort("created_at", 1).to_list(None)

    async def set_status(self, job_id, status: str, error: str | None = None) -> None:
        update: dict[str, Any] = {"status": status, "updated_at": utc_now()}
        if error is not None:
            update["last_error"] = error
        await self.collection.update_one({"_id": job_id}, {"$set": update})

    async def save_caption(self, job_id, caption: str) -> None:
        await self.collection.update_one(
            {"_id": job_id},
            {"$set": {"llm.generated_caption": caption, "status": "caption_generated", "updated_at": utc_now()}},
        )

    async def mark_sent(self, job_id, message_ids: list[int]) -> None:
        await self.collection.update_one(
            {"_id": job_id},
            {
                "$set": {
                    "delivery.telegram_message_ids": message_ids,
                    "delivery.sent_at": utc_now(),
                    "status": "telegram_sent",
                    "updated_at": utc_now(),
                }
            },
        )

    async def cancel_for_list(self, account_id: str, twitter_list_id: str) -> int:
        result = await self.collection.update_many(
            {
                "account_id": account_id,
                "twitter_list_id": twitter_list_id,
                "status": {"$nin": ["telegram_sent", "cancelled"]},
            },
            {"$set": {"status": "cancelled", "updated_at": utc_now()}},
        )
        return int(result.modified_count)

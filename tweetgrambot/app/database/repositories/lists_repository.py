from __future__ import annotations

from typing import Any

from tweetgrambot.app.core.models import ListAssignment
from tweetgrambot.app.database.repositories.base import MongoRepository
from tweetgrambot.app.utils.time import utc_now


class ListsRepository(MongoRepository):
    collection_name = "list_assignments"

    async def next_sequence(self, account_id: str) -> int:
        current = await self.collection.find({"account_id": account_id}).sort("sequence", -1).limit(1).to_list(1)
        return int(current[0]["sequence"]) + 1 if current else 1

    async def create(self, assignment: ListAssignment) -> None:
        await self.collection.insert_one(assignment.model_dump())

    async def active_for_account(self, account_id: str) -> list[dict[str, Any]]:
        return await self.collection.find(
            {"account_id": account_id, "status": "active", "cancel_requested": False}
        ).sort("sequence", 1).to_list(None)

    async def request_cancel(self, account_id: str, twitter_list_id: str) -> None:
        await self.touch(
            {"account_id": account_id, "twitter_list_id": twitter_list_id},
            {"$set": {"cancel_requested": True, "status": "cancelled"}},
        )

    async def mark_cycle_started(self, account_id: str, twitter_list_id: str) -> None:
        await self.touch(
            {"account_id": account_id, "twitter_list_id": twitter_list_id},
            {"$set": {"last_cycle_started_at": utc_now()}},
        )

    async def mark_cycle_completed(self, account_id: str, twitter_list_id: str) -> None:
        await self.touch(
            {"account_id": account_id, "twitter_list_id": twitter_list_id},
            {"$set": {"last_cycle_completed_at": utc_now()}},
        )

    async def update_checkpoint(
        self, account_id: str, twitter_list_id: str, source_post_id: str
    ) -> None:
        await self.touch(
            {"account_id": account_id, "twitter_list_id": twitter_list_id},
            {"$set": {"last_delivered_post_id": source_post_id}},
        )

from __future__ import annotations

from tweetgrambot.app.database.repositories.lists_repository import ListsRepository


class CheckpointService:
    def __init__(self, lists: ListsRepository) -> None:
        self.lists = lists

    async def mark_delivered(self, account_id: str, twitter_list_id: str, source_post_id: str) -> None:
        await self.lists.update_checkpoint(account_id, twitter_list_id, source_post_id)

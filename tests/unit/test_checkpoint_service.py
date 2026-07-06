from __future__ import annotations

import pytest

from tweetgrambot.app.services.checkpoint_service import CheckpointService


class FakeListsRepository:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    async def update_checkpoint(self, account_id: str, twitter_list_id: str, source_post_id: str) -> None:
        self.calls.append((account_id, twitter_list_id, source_post_id))


@pytest.mark.asyncio
async def test_checkpoint_service_marks_delivery_checkpoint() -> None:
    lists = FakeListsRepository()
    service = CheckpointService(lists)

    await service.mark_delivered("acc_1", "list_1", "post_1")

    assert lists.calls == [("acc_1", "list_1", "post_1")]

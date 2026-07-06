from __future__ import annotations

import pytest

from tweetgrambot.app.core.account_manager import AccountManager


class FakeAccounts:
    def __init__(self) -> None:
        self.llm_update = None

    async def update_llm(self, account_id, update):
        self.llm_update = (account_id, update)


@pytest.mark.asyncio
async def test_account_manager_sets_llm_provider_model() -> None:
    accounts = FakeAccounts()
    manager = AccountManager(
        accounts=accounts,
        lists=None,
        proxies=None,
        jobs=None,
        logs=None,
        settings=None,
        worker_pool=None,
        validator=None,
        encryption=None,
        proxy_manager=None,
        scraper=None,
        temp_storage=None,
    )

    await manager.set_llm_provider_model("acc_1", "openai", "gpt-4.1-mini")

    assert accounts.llm_update == ("acc_1", {"provider": "openai", "model": "gpt-4.1-mini"})

from __future__ import annotations

import pytest

from tweetgrambot.app.core.account_manager import AccountManager


class FakeAccounts:
    def __init__(self) -> None:
        self.llm_update = None
        self.cookie_update = None
        self.account = {"account_id": "acc_1", "username": "user"}
        self.created = None

    async def create(self, account):
        self.created = account

    async def get(self, account_id):
        if account_id == self.account["account_id"]:
            return self.account
        return None

    async def update_cookie_auth(self, account_id, auth_token_enc, ct0_enc):
        self.cookie_update = (account_id, auth_token_enc, ct0_enc)

    async def update_llm(self, account_id, update):
        self.llm_update = (account_id, update)


class FakeValidator:
    def __init__(self) -> None:
        self.cookies = None

    async def validate_cookies(self, **kwargs):
        self.cookies = kwargs

    async def validate_credentials(self, **kwargs):
        self.credentials = kwargs


class FakeEncryption:
    def encrypt(self, value):
        return f"enc:{value}"


class FakeProxyManager:
    def __init__(self) -> None:
        self.proxies = []

    async def add_proxy(self, account_id, proxy):
        self.proxies.append((account_id, proxy))
        return "proxy_1"

    async def choose_proxy(self, account_id):
        return None


class FakeLists:
    def __init__(self) -> None:
        self.created = None

    async def next_sequence(self, account_id):
        return 1

    async def create(self, assignment):
        self.created = assignment


class FakeScraper:
    async def newest_post_id_for_list(self, twitter_list_id, account, proxy):
        return "post_now"


class FakeWorkerPool:
    def __init__(self) -> None:
        self.stopped = []

    async def stop(self, account_id):
        self.stopped.append(account_id)


class FakeSettings:
    async def get_runtime(self):
        return {"default_cycle_delay_seconds": 37}


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


@pytest.mark.asyncio
async def test_account_manager_refreshes_cookie_auth_for_existing_account() -> None:
    accounts = FakeAccounts()
    validator = FakeValidator()
    proxy_manager = FakeProxyManager()
    worker_pool = FakeWorkerPool()
    manager = AccountManager(
        accounts=accounts,
        lists=None,
        proxies=None,
        jobs=None,
        logs=None,
        settings=None,
        worker_pool=worker_pool,
        validator=validator,
        encryption=FakeEncryption(),
        proxy_manager=proxy_manager,
        scraper=None,
        temp_storage=None,
    )

    await manager.refresh_cookies(
        account_id="acc_1",
        auth_token="new_auth",
        ct0="new_ct0",
        proxy="http://proxy",
    )

    assert validator.cookies == {
        "username": "user",
        "auth_token": "new_auth",
        "ct0": "new_ct0",
        "proxy": "http://proxy",
    }
    assert accounts.cookie_update == ("acc_1", "enc:new_auth", "enc:new_ct0")
    assert worker_pool.stopped == ["acc_1"]
    assert proxy_manager.proxies == [("acc_1", "http://proxy")]


@pytest.mark.asyncio
async def test_account_manager_uses_runtime_default_cycle_delay_for_new_cookie_account() -> None:
    accounts = FakeAccounts()
    manager = AccountManager(
        accounts=accounts,
        lists=None,
        proxies=None,
        jobs=None,
        logs=None,
        settings=FakeSettings(),
        worker_pool=None,
        validator=FakeValidator(),
        encryption=FakeEncryption(),
        proxy_manager=FakeProxyManager(),
        scraper=None,
        temp_storage=None,
    )

    await manager.create_with_cookies(username="user", auth_token="auth", ct0="ct0")

    assert accounts.created.cycle_delay_seconds == 37


@pytest.mark.asyncio
async def test_assign_list_starts_from_current_latest_post() -> None:
    accounts = FakeAccounts()
    lists = FakeLists()
    manager = AccountManager(
        accounts=accounts,
        lists=lists,
        proxies=None,
        jobs=None,
        logs=None,
        settings=None,
        worker_pool=None,
        validator=None,
        encryption=None,
        proxy_manager=FakeProxyManager(),
        scraper=FakeScraper(),
        temp_storage=None,
    )

    await manager.assign_list("acc_1", "list_1")

    assert lists.created.baseline_post_id == "post_now"
    assert lists.created.last_delivered_post_id == "post_now"
    assert lists.created.resume_cursor is None

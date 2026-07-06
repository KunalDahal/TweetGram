from __future__ import annotations

import pytest

from tweetgrambot.app.bot.commands.acc import AccCommandHandler


class FakeManager:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    async def create_with_cookies(self, **kwargs) -> str:
        self.calls.append(("cookies", kwargs))
        return "acc_1"

    async def assign_list(self, account_id: str, twitter_list_id: str) -> None:
        self.calls.append(("assign_list", account_id, twitter_list_id))

    async def set_llm_provider_model(self, account_id: str, provider: str, model: str) -> None:
        self.calls.append(("llm", account_id, provider, model))

    async def status(self) -> str:
        return "status"


@pytest.mark.asyncio
async def test_acc_cookie_command_dispatches_to_manager() -> None:
    manager = FakeManager()
    handler = AccCommandHandler(manager)

    response = await handler.dispatch(["-c", "user", "auth", "ct0", "http://proxy"])

    assert response == "Account created: acc_1"
    assert manager.calls == [
        (
            "cookies",
            {
                "username": "user",
                "auth_token": "auth",
                "ct0": "ct0",
                "proxy": "http://proxy",
            },
        )
    ]


@pytest.mark.asyncio
async def test_acc_assign_list_dispatches_to_manager() -> None:
    manager = FakeManager()
    handler = AccCommandHandler(manager)

    response = await handler.dispatch(["-l", "123", "-a", "acc_1"])

    assert response == "List 123 assigned to acc_1."
    assert manager.calls == [("assign_list", "acc_1", "123")]


@pytest.mark.asyncio
async def test_acc_llm_provider_model_command() -> None:
    manager = FakeManager()
    handler = AccCommandHandler(manager)

    response = await handler.dispatch(["acc_1", "-lm", "openai", "gpt-4.1-mini"])

    assert response == "LLM provider/model set for acc_1."
    assert manager.calls == [("llm", "acc_1", "openai", "gpt-4.1-mini")]

from __future__ import annotations

import pytest

from tweetgrambot.app.bot.commands.acc import AccCommandHandler


class FakeManager:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    async def create_with_cookies(self, **kwargs) -> str:
        self.calls.append(("cookies", kwargs))
        return "acc_1"

    async def refresh_cookies(self, **kwargs) -> None:
        self.calls.append(("refresh_cookies", kwargs))

    async def assign_list(self, account_id: str, twitter_list_id: str) -> None:
        self.calls.append(("assign_list", account_id, twitter_list_id))

    async def set_llm_provider_model(self, account_id: str, provider: str, model: str) -> None:
        self.calls.append(("llm", account_id, provider, model))

    async def status(self) -> str:
        return "status"


class FakeMessage:
    def __init__(self, text: str) -> None:
        self.text = text
        self.replies = []

    async def reply_text(self, text: str, reply_markup=None) -> None:
        self.replies.append((text, reply_markup))


class FakeUpdate:
    def __init__(self, text: str) -> None:
        self.effective_message = FakeMessage(text)


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
async def test_acc_refresh_cookie_command_dispatches_to_manager() -> None:
    manager = FakeManager()
    handler = AccCommandHandler(manager)

    response = await handler.dispatch(["acc_1", "-c", "new_auth", "new_ct0", "http://proxy"])

    assert response == "Cookies refreshed for acc_1. Use /acc -i acc_1 to reactivate the worker."
    assert manager.calls == [
        (
            "refresh_cookies",
            {
                "account_id": "acc_1",
                "auth_token": "new_auth",
                "ct0": "new_ct0",
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


@pytest.mark.asyncio
async def test_acc_llm_without_provider_sends_provider_buttons() -> None:
    manager = FakeManager()
    handler = AccCommandHandler(manager)
    update = FakeUpdate("/acc acc_1 -lm")

    await handler.handle(update, None)

    text, keyboard = update.effective_message.replies[0]
    assert text == "Choose LLM provider for acc_1:"
    callback_data = [row[0].callback_data for row in keyboard.inline_keyboard]
    assert "llm:provider:acc_1:openai" in callback_data
    assert "llm:provider:acc_1:gemini" in callback_data

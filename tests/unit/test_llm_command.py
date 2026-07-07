from __future__ import annotations

import pytest

from tweetgrambot.app.bot.commands.llm import LlmCommandHandler


class FakeManager:
    def __init__(self) -> None:
        self.calls = []

    async def set_llm_provider_model(self, account_id: str, provider: str, model: str) -> None:
        self.calls.append((account_id, provider, model))


class FakeCallbackQuery:
    def __init__(self, data: str) -> None:
        self.data = data
        self.answers = []
        self.edits = []

    async def answer(self, *args, **kwargs) -> None:
        self.answers.append((args, kwargs))

    async def edit_message_text(self, text: str, reply_markup=None) -> None:
        self.edits.append((text, reply_markup))


class FakeUpdate:
    def __init__(self, data: str) -> None:
        self.callback_query = FakeCallbackQuery(data)


def test_llm_provider_keyboard_contains_provider_callbacks() -> None:
    handler = LlmCommandHandler(FakeManager())

    keyboard = handler.provider_keyboard("acc_1")

    callback_data = [row[0].callback_data for row in keyboard.inline_keyboard]
    assert "llm:provider:acc_1:openai" in callback_data
    assert "llm:provider:acc_1:anthropic" in callback_data


@pytest.mark.asyncio
async def test_llm_provider_callback_shows_model_buttons() -> None:
    handler = LlmCommandHandler(FakeManager())
    update = FakeUpdate("llm:provider:acc_1:openai")

    await handler.handle_callback(update, None)

    assert update.callback_query.answers
    text, keyboard = update.callback_query.edits[0]
    assert text == "Choose model for acc_1 / OpenAI:"
    assert keyboard.inline_keyboard[0][0].callback_data == "llm:model:acc_1:openai:0"


@pytest.mark.asyncio
async def test_llm_model_callback_updates_account_model() -> None:
    manager = FakeManager()
    handler = LlmCommandHandler(manager)
    update = FakeUpdate("llm:model:acc_1:openai:0")

    await handler.handle_callback(update, None)

    assert manager.calls == [("acc_1", "openai", "gpt-4.1-mini")]
    assert update.callback_query.edits[0][0] == "LLM provider/model set for acc_1: openai/gpt-4.1-mini"

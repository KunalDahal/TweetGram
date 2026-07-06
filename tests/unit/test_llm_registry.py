from __future__ import annotations

import pytest

from tweetgrambot.app.services.llm.base import LLMProvider
from tweetgrambot.app.services.llm.provider_registry import ProviderRegistry


class FakeProvider(LLMProvider):
    async def generate_caption(self, **kwargs) -> str:
        return "caption"


def test_registry_returns_registered_provider_case_insensitively() -> None:
    registry = ProviderRegistry()
    provider = FakeProvider()
    registry.register("OpenAI", provider)
    assert registry.get("openai") is provider


def test_registry_rejects_unknown_provider() -> None:
    registry = ProviderRegistry()
    with pytest.raises(ValueError):
        registry.get("missing")

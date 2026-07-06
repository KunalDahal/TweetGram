from __future__ import annotations

from tweetgrambot.app.services.llm.base import LLMProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {}

    def register(self, name: str, provider: LLMProvider) -> None:
        self._providers[name.lower()] = provider

    def get(self, name: str) -> LLMProvider:
        try:
            return self._providers[name.lower()]
        except KeyError as exc:
            raise ValueError(f"Unsupported LLM provider: {name}") from exc

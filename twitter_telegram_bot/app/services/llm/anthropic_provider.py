from __future__ import annotations

from twitter_telegram_bot.app.services.llm.base import LLMProvider


class AnthropicProvider(LLMProvider):
    async def generate_caption(self, **kwargs) -> str:
        _ = kwargs
        raise NotImplementedError("Anthropic provider is not wired yet.")

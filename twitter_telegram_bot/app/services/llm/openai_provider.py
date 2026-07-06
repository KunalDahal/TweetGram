from __future__ import annotations

from twitter_telegram_bot.app.services.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    async def generate_caption(self, **kwargs) -> str:
        _ = kwargs
        raise NotImplementedError("OpenAI provider is not wired yet.")

from __future__ import annotations

from tweetgrambot.app.services.llm.base import LLMProvider


class GroqProvider(LLMProvider):
    async def generate_caption(self, **kwargs) -> str:
        _ = kwargs
        raise NotImplementedError("Groq provider is not wired yet.")

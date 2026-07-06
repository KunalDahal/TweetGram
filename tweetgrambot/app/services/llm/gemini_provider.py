from __future__ import annotations

from tweetgrambot.app.services.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    async def generate_caption(self, **kwargs) -> str:
        _ = kwargs
        raise NotImplementedError("Gemini provider is not wired yet.")

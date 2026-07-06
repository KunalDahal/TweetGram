from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def generate_caption(
        self,
        *,
        api_key: str,
        model: str,
        global_prompt: str,
        source_text: str,
        quote_text: str | None,
        source_url: str,
    ) -> str:
        raise NotImplementedError

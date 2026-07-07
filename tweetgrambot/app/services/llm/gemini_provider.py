from __future__ import annotations

from typing import Any

import aiohttp

from tweetgrambot.app.services.llm.base import LLMProvider


class GeminiProviderError(RuntimeError):
    """Raised when Gemini cannot produce a usable caption."""


class GeminiProvider(LLMProvider):
    api_base_url = "https://generativelanguage.googleapis.com/v1beta"
    max_output_tokens = 2048

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
        prompt = self._build_prompt(
            global_prompt=global_prompt,
            source_text=source_text,
            quote_text=quote_text,
            source_url=source_url,
        )
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": self.max_output_tokens,
            },
        }
        url = f"{self.api_base_url}/models/{model}:generateContent"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                params={"key": api_key},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:
                data = await response.json(content_type=None)
                if response.status >= 400:
                    message = self._error_message(data)
                    raise GeminiProviderError(f"Gemini request failed: {message}")

        caption = self._extract_text(data).strip()
        if not caption:
            raise GeminiProviderError("Gemini returned an empty caption.")
        finish_reason = self._finish_reason(data)
        if finish_reason == "MAX_TOKENS":
            raise GeminiProviderError(
                "Gemini stopped because max output tokens were reached. "
                "Shorten the prompt or use a model with a larger output limit."
            )
        return caption

    def _build_prompt(
        self,
        *,
        global_prompt: str,
        source_text: str,
        quote_text: str | None,
        source_url: str,
    ) -> str:
        instructions = global_prompt.strip() or (
            "Write a concise, engaging Telegram caption for this X/Twitter post. "
            "Do not invent facts. Preserve the meaning of the source post."
        )
        parts = [
            instructions,
            "",
            "Source post text:",
            source_text.strip() or "<no text>",
        ]
        if quote_text:
            parts.extend(["", "Quoted post text:", quote_text.strip()])
        parts.extend(["", "Source URL:", source_url])
        return "\n".join(parts)

    def _extract_text(self, data: dict[str, Any]) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts") or []
        return "".join(str(part.get("text", "")) for part in parts)

    def _error_message(self, data: dict[str, Any]) -> str:
        error = data.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error)
        return str(data)

    def _finish_reason(self, data: dict[str, Any]) -> str | None:
        candidates = data.get("candidates") or []
        if not candidates:
            return None
        finish_reason = candidates[0].get("finishReason")
        return str(finish_reason) if finish_reason else None

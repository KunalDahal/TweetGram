from __future__ import annotations

import pytest

from tweetgrambot.app.services.llm.gemini_provider import GeminiProvider


def test_gemini_provider_builds_prompt_with_source_and_quote() -> None:
    provider = GeminiProvider()

    prompt = provider._build_prompt(
        global_prompt="Use a sharp editorial tone.",
        source_text="Main post",
        quote_text="Quoted post",
        source_url="https://x.com/user/status/1",
    )

    assert "Use a sharp editorial tone." in prompt
    assert "Main post" in prompt
    assert "Quoted post" in prompt
    assert "https://x.com/user/status/1" in prompt


def test_gemini_provider_extracts_caption_text() -> None:
    provider = GeminiProvider()

    caption = provider._extract_text(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Hello "},
                            {"text": "world"},
                        ]
                    }
                }
            ]
        }
    )

    assert caption == "Hello world"


def test_gemini_provider_detects_max_token_finish_reason() -> None:
    provider = GeminiProvider()

    finish_reason = provider._finish_reason(
        {
            "candidates": [
                {
                    "finishReason": "MAX_TOKENS",
                    "content": {"parts": [{"text": "partial"}]},
                }
            ]
        }
    )

    assert finish_reason == "MAX_TOKENS"


@pytest.mark.asyncio
async def test_gemini_provider_is_wired() -> None:
    provider = GeminiProvider()

    assert provider.api_base_url == "https://generativelanguage.googleapis.com/v1beta"
    assert provider.max_output_tokens == 2048

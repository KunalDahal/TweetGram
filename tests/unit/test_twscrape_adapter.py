from __future__ import annotations

import pytest

from tweetgrambot.app.services.twscrape_adapter import (
    TwscrapeAdapter,
    TwscrapeAuthenticationError,
)


class FakeEncryption:
    def decrypt(self, value: str) -> str:
        return value


@pytest.mark.asyncio
async def test_twscrape_adapter_requires_cookie_auth() -> None:
    adapter = TwscrapeAdapter(FakeEncryption())

    with pytest.raises(TwscrapeAuthenticationError):
        await adapter.newest_post_id_for_list(
            "123",
            {"username": "user", "auth": {}},
            proxy=None,
        )

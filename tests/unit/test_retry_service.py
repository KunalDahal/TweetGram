from __future__ import annotations

import pytest

from tweetgrambot.app.services.retry_service import RetryExhaustedError, RetryService


@pytest.mark.asyncio
async def test_retry_service_retries_until_success() -> None:
    attempts = 0
    retry = RetryService(max_attempts=3, base_delay_seconds=0)

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise RuntimeError("try again")
        return "ok"

    assert await retry.run(operation) == "ok"
    assert attempts == 2


@pytest.mark.asyncio
async def test_retry_service_raises_after_exhaustion() -> None:
    retry = RetryService(max_attempts=2, base_delay_seconds=0)

    async def operation() -> str:
        raise RuntimeError("nope")

    with pytest.raises(RetryExhaustedError):
        await retry.run(operation)

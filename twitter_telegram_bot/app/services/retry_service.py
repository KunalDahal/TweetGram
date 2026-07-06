from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class RetryExhaustedError(RuntimeError):
    pass


class RetryService:
    def __init__(self, max_attempts: int = 3, base_delay_seconds: float = 1.0) -> None:
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds

    async def run(self, operation: Callable[[], Awaitable[T]]) -> T:
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return await operation()
            except Exception as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    await asyncio.sleep(self.base_delay_seconds * attempt)
        raise RetryExhaustedError(str(last_error)) from last_error

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


async def run_in_transaction(client, operation: Callable[[object], Awaitable[T]]) -> T:
    async with await client.start_session() as session:
        async with session.start_transaction():
            return await operation(session)

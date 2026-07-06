from __future__ import annotations

import pytest

from twitter_telegram_bot.app.core.worker_pool import WorkerPool


class FakeWorker:
    def __init__(self) -> None:
        self.running = False
        self.starts = 0
        self.stops = 0

    def start(self) -> None:
        self.running = True
        self.starts += 1

    async def stop(self) -> None:
        self.running = False
        self.stops += 1


@pytest.mark.asyncio
async def test_worker_pool_prevents_duplicate_running_workers() -> None:
    workers: list[FakeWorker] = []

    def factory(account_id: str) -> FakeWorker:
        worker = FakeWorker()
        workers.append(worker)
        return worker

    pool = WorkerPool(factory)

    first = await pool.start("acc_1")
    second = await pool.start("acc_1")

    assert first is second
    assert len(workers) == 1
    assert first.starts == 1


@pytest.mark.asyncio
async def test_worker_pool_stops_and_removes_worker() -> None:
    worker = FakeWorker()
    pool = WorkerPool(lambda account_id: worker)

    await pool.start("acc_1")
    await pool.stop("acc_1")

    assert worker.stops == 1
    assert pool.get("acc_1") is None

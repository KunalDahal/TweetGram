from __future__ import annotations

from collections.abc import Callable

from twitter_telegram_bot.app.core.worker import Worker


class WorkerPool:
    def __init__(self, worker_factory: Callable[[str], Worker]) -> None:
        self._worker_factory = worker_factory
        self._workers: dict[str, Worker] = {}

    def get(self, account_id: str) -> Worker | None:
        return self._workers.get(account_id)

    async def start(self, account_id: str) -> Worker:
        worker = self._workers.get(account_id)
        if worker and worker.running:
            return worker
        worker = worker or self._worker_factory(account_id)
        self._workers[account_id] = worker
        worker.start()
        return worker

    async def stop(self, account_id: str) -> None:
        worker = self._workers.pop(account_id, None)
        if worker:
            await worker.stop()

    async def restore_active(self, account_ids: list[str]) -> None:
        for account_id in account_ids:
            await self.start(account_id)

    async def stop_all(self) -> None:
        for account_id in list(self._workers):
            await self.stop(account_id)

    def status(self) -> dict[str, str]:
        return {
            account_id: "running" if worker.running else "stopped"
            for account_id, worker in self._workers.items()
        }

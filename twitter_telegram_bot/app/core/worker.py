from __future__ import annotations

import asyncio
from contextlib import suppress

from twitter_telegram_bot.app.core.job_runner import JobRunner
from twitter_telegram_bot.app.database.repositories.accounts_repository import AccountsRepository
from twitter_telegram_bot.app.database.repositories.lists_repository import ListsRepository
from twitter_telegram_bot.app.database.repositories.logs_repository import LogsRepository
from twitter_telegram_bot.app.database.repositories.post_jobs_repository import PostJobsRepository
from twitter_telegram_bot.app.database.repositories.settings_repository import SettingsRepository
from twitter_telegram_bot.app.services.alert_service import AlertService
from twitter_telegram_bot.app.services.post_extractor import PostExtractor
from twitter_telegram_bot.app.services.proxy_manager import ProxyManager
from twitter_telegram_bot.app.services.twscrape_adapter import TwscrapeAdapter
from twitter_telegram_bot.app.utils.ids import worker_id_for


class Worker:
    def __init__(
        self,
        *,
        account_id: str,
        accounts: AccountsRepository,
        lists: ListsRepository,
        jobs: PostJobsRepository,
        logs: LogsRepository,
        settings: SettingsRepository,
        proxy_manager: ProxyManager,
        scraper: TwscrapeAdapter,
        extractor: PostExtractor,
        job_runner: JobRunner,
        alerts: AlertService,
    ) -> None:
        self.account_id = account_id
        self.worker_id = worker_id_for(account_id)
        self.accounts = accounts
        self.lists = lists
        self.jobs = jobs
        self.logs = logs
        self.settings = settings
        self.proxy_manager = proxy_manager
        self.scraper = scraper
        self.extractor = extractor
        self.job_runner = job_runner
        self.alerts = alerts
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self) -> None:
        if not self.running:
            self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            with suppress(asyncio.CancelledError):
                await self._task

    async def _run_loop(self) -> None:
        await self.accounts.set_worker_status(self.account_id, "running")
        while not self._stop_event.is_set():
            account = await self.accounts.get(self.account_id)
            if not account or not account.get("is_active"):
                break
            try:
                await self._run_cycle(account)
            except Exception as exc:
                await self.accounts.set_worker_status(self.account_id, "error")
                await self.alerts.notify_admins(f"Worker {self.account_id} paused: {exc}")
                return
            delay = int(account.get("cycle_delay_seconds") or 900)
            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self._stop_event.wait(), timeout=delay)
        await self.accounts.set_worker_status(self.account_id, "stopped")

    async def _run_cycle(self, account: dict) -> None:
        runtime_settings = await self.settings.get_runtime() or {}
        await self._resume_pending_jobs(account, runtime_settings)
        proxy = await self.proxy_manager.choose_proxy(self.account_id)
        assignments = await self.lists.active_for_account(self.account_id)
        for assignment in assignments:
            if self._stop_event.is_set():
                return
            await self._process_list(account, assignment, proxy, runtime_settings)

    async def _resume_pending_jobs(self, account: dict, runtime_settings: dict) -> None:
        for job in await self.jobs.pending_for_account(self.account_id):
            if self._stop_event.is_set():
                return
            await self.job_runner.run_job(job, account, runtime_settings)

    async def _process_list(
        self, account: dict, assignment: dict, proxy: str | None, runtime_settings: dict
    ) -> None:
        llm = account.get("llm") or {}
        if not llm.get("provider") or not llm.get("model"):
            raise ValueError("LLM provider and model must be configured before running.")
        await self.lists.mark_cycle_started(self.account_id, assignment["twitter_list_id"])
        posts = await self.scraper.new_posts_for_list(
            twitter_list_id=assignment["twitter_list_id"],
            since_post_id=assignment.get("last_delivered_post_id") or assignment.get("baseline_post_id"),
            account=account,
            proxy=proxy,
        )
        for post in reversed(posts):
            job = self.extractor.build_job(
                account_id=self.account_id,
                twitter_list_id=assignment["twitter_list_id"],
                post=post,
                provider=llm["provider"],
                model=llm["model"],
                prompt_version=int(runtime_settings.get("global_prompt_version", 1)),
            )
            await self.jobs.create(job)
            stored = await self.jobs.collection.find_one(
                {
                    "account_id": self.account_id,
                    "twitter_list_id": assignment["twitter_list_id"],
                    "source_post_id": post.post_id,
                }
            )
            await self.job_runner.run_job(stored, account, runtime_settings)
        await self.lists.mark_cycle_completed(self.account_id, assignment["twitter_list_id"])

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from tweetgrambot.app.core.job_runner import JobRunner
from tweetgrambot.app.database.repositories.accounts_repository import AccountsRepository
from tweetgrambot.app.database.repositories.lists_repository import ListsRepository
from tweetgrambot.app.database.repositories.logs_repository import LogsRepository
from tweetgrambot.app.database.repositories.post_jobs_repository import PostJobsRepository
from tweetgrambot.app.database.repositories.settings_repository import SettingsRepository
from tweetgrambot.app.services.alert_service import AlertService
from tweetgrambot.app.services.post_extractor import PostExtractor
from tweetgrambot.app.services.proxy_manager import ProxyManager
from tweetgrambot.app.services.twscrape_adapter import TwscrapeAdapter, TwscrapeAuthenticationError
from tweetgrambot.app.utils.ids import worker_id_for


logger = logging.getLogger(__name__)


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
            logger.info("Starting worker loop for account_id=%s", self.account_id)
            self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        logger.info("Stopping worker loop for account_id=%s", self.account_id)
        self._stop_event.set()
        if self._task is not None:
            with suppress(asyncio.CancelledError):
                await self._task

    async def _run_loop(self) -> None:
        await self.accounts.set_worker_status(self.account_id, "running")
        logger.info("Worker loop running for account_id=%s", self.account_id)
        while not self._stop_event.is_set():
            account = await self.accounts.get(self.account_id)
            if not account or not account.get("is_active"):
                logger.info("Worker account inactive; stopping account_id=%s", self.account_id)
                break
            try:
                await self._run_cycle(account)
            except TwscrapeAuthenticationError as exc:
                reason = str(exc) or "X authentication failed; refresh auth_token and ct0."
                await self.accounts.mark_auth_failed(self.account_id, reason)
                logger.warning("Worker paused for auth refresh account_id=%s reason=%s", self.account_id, reason)
                await self.alerts.notify_admins(
                    f"Worker {self.account_id} paused: X authentication failed. "
                    f"Refresh cookies with /acc {self.account_id} -c <auth_token> <ct0>."
                )
                return
            except Exception as exc:
                await self.accounts.set_worker_status(self.account_id, "error")
                logger.exception("Worker paused after error for account_id=%s", self.account_id)
                await self.alerts.notify_admins(f"Worker {self.account_id} paused: {exc}")
                return
            runtime_settings = await self.settings.get_runtime() or {}
            delay = int(
                account.get("cycle_delay_seconds")
                or runtime_settings.get("default_cycle_delay_seconds")
                or 900
            )
            logger.info(
                "Worker cycle complete for account_id=%s; next_cycle_seconds=%s",
                self.account_id,
                delay,
            )
            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self._stop_event.wait(), timeout=delay)
        await self.accounts.set_worker_status(self.account_id, "stopped")
        logger.info("Worker loop stopped for account_id=%s", self.account_id)

    async def _run_cycle(self, account: dict) -> None:
        runtime_settings = await self.settings.get_runtime() or {}
        await self._resume_pending_jobs(account, runtime_settings)
        proxy = await self.proxy_manager.choose_proxy(self.account_id)
        assignments = await self.lists.active_for_account(self.account_id)
        logger.info(
            "Worker cycle started for account_id=%s; assignments=%s",
            self.account_id,
            len(assignments),
        )
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

        since_post_id = assignment.get("last_delivered_post_id") or assignment.get("baseline_post_id")
        if since_post_id is None and assignment.get("resume_cursor") != "empty_baseline":
            latest_post_id = await self.scraper.newest_post_id_for_list(
                assignment["twitter_list_id"],
                account,
                proxy,
            )
            await self.lists.initialize_checkpoint(
                self.account_id,
                assignment["twitter_list_id"],
                latest_post_id,
            )
            logger.info(
                "Initialized list checkpoint for account_id=%s twitter_list_id=%s post_id=%s",
                self.account_id,
                assignment["twitter_list_id"],
                latest_post_id,
            )
            await self.lists.mark_cycle_completed(self.account_id, assignment["twitter_list_id"])
            return

        posts = await self.scraper.new_posts_for_list(
            twitter_list_id=assignment["twitter_list_id"],
            since_post_id=since_post_id,
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

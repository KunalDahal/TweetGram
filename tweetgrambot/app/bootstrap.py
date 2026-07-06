from __future__ import annotations

import logging

from telegram import Bot

from tweetgrambot.app.config.settings import Settings
from tweetgrambot.app.core.account_manager import AccountManager
from tweetgrambot.app.core.job_runner import JobRunner
from tweetgrambot.app.core.worker import Worker
from tweetgrambot.app.core.worker_pool import WorkerPool
from tweetgrambot.app.database.indexes import ensure_indexes
from tweetgrambot.app.database.mongo import Mongo
from tweetgrambot.app.database.repositories.accounts_repository import AccountsRepository
from tweetgrambot.app.database.repositories.lists_repository import ListsRepository
from tweetgrambot.app.database.repositories.logs_repository import LogsRepository
from tweetgrambot.app.database.repositories.post_jobs_repository import PostJobsRepository
from tweetgrambot.app.database.repositories.proxies_repository import ProxiesRepository
from tweetgrambot.app.database.repositories.settings_repository import SettingsRepository
from tweetgrambot.app.services.account_validator import AccountValidator
from tweetgrambot.app.services.alert_service import AlertService
from tweetgrambot.app.services.checkpoint_service import CheckpointService
from tweetgrambot.app.services.encryption_service import EncryptionService
from tweetgrambot.app.services.llm.provider_registry import ProviderRegistry
from tweetgrambot.app.services.media_downloader import MediaDownloader
from tweetgrambot.app.services.post_extractor import PostExtractor
from tweetgrambot.app.services.proxy_manager import ProxyManager
from tweetgrambot.app.services.retry_service import RetryService
from tweetgrambot.app.services.telegram_publisher import TelegramPublisher
from tweetgrambot.app.services.temp_storage_service import TempStorageService
from tweetgrambot.app.services.twscrape_adapter import TwscrapeAdapter


logger = logging.getLogger(__name__)


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.mongo = Mongo(settings)
        self.db = self.mongo.database
        self.bot = Bot(settings.telegram_bot_token)

        self.accounts = AccountsRepository(self.db)
        self.lists = ListsRepository(self.db)
        self.proxies = ProxiesRepository(self.db)
        self.jobs = PostJobsRepository(self.db)
        self.logs = LogsRepository(self.db)
        self.app_settings = SettingsRepository(self.db)

        self.encryption = EncryptionService(settings.encryption_key)
        self.validator = AccountValidator()
        self.proxy_manager = ProxyManager(self.proxies, self.encryption)
        self.scraper = TwscrapeAdapter()
        self.extractor = PostExtractor()
        self.temp_storage = TempStorageService(settings.temp_media_directory)
        self.media_downloader = MediaDownloader(settings.temp_media_directory)
        self.retry = RetryService(settings.max_retry_attempts)
        self.llm_registry = ProviderRegistry()
        self.publisher = TelegramPublisher(self.bot, settings.telegram_target_channel_id)
        self.alerts = AlertService(self.bot, settings.allowed_telegram_user_ids)
        self.checkpoints = CheckpointService(self.lists)

        self.job_runner = JobRunner(
            jobs=self.jobs,
            checkpoints=self.checkpoints,
            media_downloader=self.media_downloader,
            llm_registry=self.llm_registry,
            telegram_publisher=self.publisher,
            encryption=self.encryption,
            retry=self.retry,
        )
        self.worker_pool = WorkerPool(self._make_worker)
        self.manager = AccountManager(
            accounts=self.accounts,
            lists=self.lists,
            proxies=self.proxies,
            jobs=self.jobs,
            logs=self.logs,
            settings=self.app_settings,
            worker_pool=self.worker_pool,
            validator=self.validator,
            encryption=self.encryption,
            proxy_manager=self.proxy_manager,
            scraper=self.scraper,
            temp_storage=self.temp_storage,
        )

    async def initialize(self) -> None:
        logger.info("Checking MongoDB connection")
        await self.mongo.ping()
        logger.info("MongoDB connection ready")
        logger.info("Ensuring MongoDB indexes")
        await ensure_indexes(self.db)
        logger.info("Ensuring runtime settings")
        await self.app_settings.ensure_runtime(
            self.settings.telegram_target_channel_id,
            self.settings.default_cycle_delay_seconds,
        )
        active_account_ids = [account["account_id"] for account in await self.accounts.list_active()]
        logger.info("Restoring %s active workers", len(active_account_ids))
        await self.worker_pool.restore_active(active_account_ids)
        logger.info("Container initialization complete")

    def _make_worker(self, account_id: str) -> Worker:
        return Worker(
            account_id=account_id,
            accounts=self.accounts,
            lists=self.lists,
            jobs=self.jobs,
            logs=self.logs,
            settings=self.app_settings,
            proxy_manager=self.proxy_manager,
            scraper=self.scraper,
            extractor=self.extractor,
            job_runner=self.job_runner,
            alerts=self.alerts,
        )

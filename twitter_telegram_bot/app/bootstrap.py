from __future__ import annotations

from telegram import Bot

from twitter_telegram_bot.app.config.settings import Settings
from twitter_telegram_bot.app.core.account_manager import AccountManager
from twitter_telegram_bot.app.core.job_runner import JobRunner
from twitter_telegram_bot.app.core.worker import Worker
from twitter_telegram_bot.app.core.worker_pool import WorkerPool
from twitter_telegram_bot.app.database.indexes import ensure_indexes
from twitter_telegram_bot.app.database.mongo import Mongo
from twitter_telegram_bot.app.database.repositories.accounts_repository import AccountsRepository
from twitter_telegram_bot.app.database.repositories.lists_repository import ListsRepository
from twitter_telegram_bot.app.database.repositories.logs_repository import LogsRepository
from twitter_telegram_bot.app.database.repositories.post_jobs_repository import PostJobsRepository
from twitter_telegram_bot.app.database.repositories.proxies_repository import ProxiesRepository
from twitter_telegram_bot.app.database.repositories.settings_repository import SettingsRepository
from twitter_telegram_bot.app.services.account_validator import AccountValidator
from twitter_telegram_bot.app.services.alert_service import AlertService
from twitter_telegram_bot.app.services.checkpoint_service import CheckpointService
from twitter_telegram_bot.app.services.encryption_service import EncryptionService
from twitter_telegram_bot.app.services.llm.provider_registry import ProviderRegistry
from twitter_telegram_bot.app.services.media_downloader import MediaDownloader
from twitter_telegram_bot.app.services.post_extractor import PostExtractor
from twitter_telegram_bot.app.services.proxy_manager import ProxyManager
from twitter_telegram_bot.app.services.retry_service import RetryService
from twitter_telegram_bot.app.services.telegram_publisher import TelegramPublisher
from twitter_telegram_bot.app.services.temp_storage_service import TempStorageService
from twitter_telegram_bot.app.services.twscrape_adapter import TwscrapeAdapter


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
        await ensure_indexes(self.db)
        await self.app_settings.ensure_runtime(
            self.settings.telegram_target_channel_id,
            self.settings.default_cycle_delay_seconds,
        )
        await self.worker_pool.restore_active(
            [account["account_id"] for account in await self.accounts.list_active()]
        )

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

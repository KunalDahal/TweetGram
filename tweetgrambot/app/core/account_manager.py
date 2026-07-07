from __future__ import annotations

from pymongo.errors import DuplicateKeyError

from tweetgrambot.app.core.models import Account, AccountAuth, ListAssignment
from tweetgrambot.app.core.worker_pool import WorkerPool
from tweetgrambot.app.database.repositories.accounts_repository import AccountsRepository
from tweetgrambot.app.database.repositories.lists_repository import ListsRepository
from tweetgrambot.app.database.repositories.logs_repository import LogsRepository
from tweetgrambot.app.database.repositories.post_jobs_repository import PostJobsRepository
from tweetgrambot.app.database.repositories.proxies_repository import ProxiesRepository
from tweetgrambot.app.database.repositories.settings_repository import SettingsRepository
from tweetgrambot.app.services.account_validator import AccountValidator
from tweetgrambot.app.services.encryption_service import EncryptionService
from tweetgrambot.app.services.proxy_manager import ProxyManager
from tweetgrambot.app.services.temp_storage_service import TempStorageService
from tweetgrambot.app.services.twscrape_adapter import TwscrapeAdapter
from tweetgrambot.app.utils.ids import new_account_id
from tweetgrambot.app.utils.masking import mask_secret
from tweetgrambot.app.utils.time import utc_now


class AccountManager:
    def __init__(
        self,
        *,
        accounts: AccountsRepository,
        lists: ListsRepository,
        proxies: ProxiesRepository,
        jobs: PostJobsRepository,
        logs: LogsRepository,
        settings: SettingsRepository,
        worker_pool: WorkerPool,
        validator: AccountValidator,
        encryption: EncryptionService,
        proxy_manager: ProxyManager,
        scraper: TwscrapeAdapter,
        temp_storage: TempStorageService,
    ) -> None:
        self.accounts = accounts
        self.lists = lists
        self.proxies = proxies
        self.jobs = jobs
        self.logs = logs
        self.settings = settings
        self.worker_pool = worker_pool
        self.validator = validator
        self.encryption = encryption
        self.proxy_manager = proxy_manager
        self.scraper = scraper
        self.temp_storage = temp_storage

    async def create_with_credentials(
        self,
        *,
        username: str,
        password: str,
        email: str,
        email_password: str,
        proxy: str | None = None,
    ) -> str:
        await self.validator.validate_credentials(
            username=username,
            password=password,
            email=email,
            email_password=email_password,
            proxy=proxy,
        )
        account_id = new_account_id()
        account = Account(
            account_id=account_id,
            username=username,
            cycle_delay_seconds=await self._default_cycle_delay_seconds(),
            auth=AccountAuth(
                mode="credentials",
                password_enc=self.encryption.encrypt(password),
                email_enc=self.encryption.encrypt(email),
                email_password_enc=self.encryption.encrypt(email_password),
                validated_at=utc_now(),
            ),
        )
        await self.accounts.create(account)
        if proxy:
            await self.proxy_manager.add_proxy(account_id, proxy)
        return account_id

    async def create_with_cookies(
        self,
        *,
        username: str,
        auth_token: str,
        ct0: str,
        proxy: str | None = None,
    ) -> str:
        await self.validator.validate_cookies(username=username, auth_token=auth_token, ct0=ct0, proxy=proxy)
        account_id = new_account_id()
        account = Account(
            account_id=account_id,
            username=username,
            cycle_delay_seconds=await self._default_cycle_delay_seconds(),
            auth=AccountAuth(
                mode="cookies",
                auth_token_enc=self.encryption.encrypt(auth_token),
                ct0_enc=self.encryption.encrypt(ct0),
                validated_at=utc_now(),
            ),
        )
        await self.accounts.create(account)
        if proxy:
            await self.proxy_manager.add_proxy(account_id, proxy)
        return account_id

    async def refresh_cookies(
        self,
        *,
        account_id: str,
        auth_token: str,
        ct0: str,
        proxy: str | None = None,
    ) -> None:
        account = await self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Unknown account: {account_id}")
        await self.validator.validate_cookies(
            username=account["username"],
            auth_token=auth_token,
            ct0=ct0,
            proxy=proxy,
        )
        if self.worker_pool:
            await self.worker_pool.stop(account_id)
        await self.accounts.update_cookie_auth(
            account_id,
            auth_token_enc=self.encryption.encrypt(auth_token),
            ct0_enc=self.encryption.encrypt(ct0),
        )
        if proxy:
            await self.proxy_manager.add_proxy(account_id, proxy)

    async def remove_account(self, account_id: str) -> None:
        await self.worker_pool.stop(account_id)
        await self.accounts.delete_account(account_id)
        await self.lists.delete_many({"account_id": account_id})
        await self.proxies.delete_many({"account_id": account_id})
        await self.jobs.delete_many({"account_id": account_id})
        await self.logs.delete_many({"account_id": account_id})
        self.temp_storage.remove_account_directory(account_id)

    async def _default_cycle_delay_seconds(self) -> int:
        if not self.settings:
            return 900
        runtime = await self.settings.get_runtime()
        if not runtime:
            return 900
        return int(runtime.get("default_cycle_delay_seconds") or 900)

    async def assign_list(self, account_id: str, twitter_list_id: str) -> None:
        account = await self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Unknown account: {account_id}")
        proxy = await self.proxy_manager.choose_proxy(account_id)
        baseline = await self.scraper.newest_post_id_for_list(twitter_list_id, account, proxy)
        assignment = ListAssignment(
            account_id=account_id,
            twitter_list_id=twitter_list_id,
            sequence=await self.lists.next_sequence(account_id),
            baseline_post_id=baseline,
            baseline_observed_at=utc_now(),
            last_delivered_post_id=baseline,
            resume_cursor="empty_baseline" if baseline is None else None,
        )
        try:
            await self.lists.create(assignment)
        except DuplicateKeyError as exc:
            raise ValueError("That Twitter List is already assigned to an account.") from exc

    async def remove_list(self, account_id: str, twitter_list_id: str) -> None:
        await self.lists.request_cancel(account_id, twitter_list_id)
        await self.jobs.cancel_for_list(account_id, twitter_list_id)
        await self.lists.delete_many({"account_id": account_id, "twitter_list_id": twitter_list_id})

    async def activate_account(self, account_id: str) -> None:
        await self.accounts.set_active(account_id, True)
        await self.worker_pool.start(account_id)

    async def halt_account(self, account_id: str) -> None:
        await self.accounts.set_active(account_id, False)
        await self.worker_pool.stop(account_id)

    async def add_proxy(self, account_id: str, proxy: str) -> str:
        return await self.proxy_manager.add_proxy(account_id, proxy)

    async def remove_proxy(self, account_id: str, proxy: str) -> int:
        return await self.proxy_manager.remove_proxy(account_id, proxy)

    async def set_llm_key(self, account_id: str, api_key: str) -> None:
        await self.accounts.update_llm(
            account_id,
            {
                "api_key_enc": self.encryption.encrypt(api_key),
                "key_fingerprint": self.encryption.fingerprint(api_key),
                "enabled": True,
            },
        )

    async def remove_llm_key(self, account_id: str, api_key: str) -> None:
        account = await self.accounts.get(account_id)
        if not account or account.get("llm", {}).get("key_fingerprint") != self.encryption.fingerprint(api_key):
            raise ValueError("LLM key does not match the stored key.")
        await self.accounts.update_llm(
            account_id,
            {"api_key_enc": None, "key_fingerprint": None, "enabled": False},
        )
        await self.halt_account(account_id)
        await self.accounts.set_worker_status(account_id, "error")

    async def set_llm_provider_model(self, account_id: str, provider: str, model: str) -> None:
        await self.accounts.update_llm(account_id, {"provider": provider, "model": model})

    async def update_global_prompt(self, prompt: str) -> int:
        return await self.settings.update_prompt(prompt)

    async def status(self) -> str:
        worker_status = self.worker_pool.status()
        lines = []
        for account in await self.accounts.list_all():
            llm = account.get("llm") or {}
            lists = await self.lists.active_for_account(account["account_id"])
            recent_logs = await self.logs.recent_for_account(account["account_id"], limit=3)
            lines.append(
                "\n".join(
                    [
                        f"Account {account['account_id']} (@{account['username']})",
                        f"Active: {account.get('is_active')} | Worker: {worker_status.get(account['account_id'], account.get('worker_status'))}",
                        f"Auth: {account.get('auth', {}).get('mode')} | Validated: {account.get('auth', {}).get('validated_at')}",
                        f"Lists: {', '.join(item['twitter_list_id'] for item in lists) or '<none>'}",
                        f"LLM: {llm.get('provider') or '<unset>'}/{llm.get('model') or '<unset>'} | Key: {mask_secret(llm.get('key_fingerprint'))}",
                        f"Recent logs: {len(recent_logs)}",
                    ]
                )
            )
        return "\n\n".join(lines) or "No accounts configured."

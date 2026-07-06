from __future__ import annotations

import random

from tweetgrambot.app.database.repositories.proxies_repository import ProxiesRepository
from tweetgrambot.app.services.encryption_service import EncryptionService


class ProxyManager:
    def __init__(self, proxies: ProxiesRepository, encryption: EncryptionService) -> None:
        self.proxies = proxies
        self.encryption = encryption

    async def add_proxy(self, account_id: str, proxy: str) -> str:
        from tweetgrambot.app.core.models import ProxyRecord

        fingerprint = self.encryption.fingerprint(proxy)
        await self.proxies.create(
            ProxyRecord(
                account_id=account_id,
                proxy_enc=self.encryption.encrypt(proxy),
                proxy_fingerprint=fingerprint,
            )
        )
        return fingerprint

    async def choose_proxy(self, account_id: str) -> str | None:
        records = await self.proxies.available_for_account(account_id)
        if not records:
            return None
        return self.encryption.decrypt(random.choice(records)["proxy_enc"])

    async def remove_proxy(self, account_id: str, proxy: str) -> int:
        return await self.proxies.delete_by_fingerprint(account_id, self.encryption.fingerprint(proxy))

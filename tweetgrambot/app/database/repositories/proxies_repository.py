from __future__ import annotations

from typing import Any

from tweetgrambot.app.core.models import ProxyRecord
from tweetgrambot.app.database.repositories.base import MongoRepository


class ProxiesRepository(MongoRepository):
    collection_name = "proxies"

    async def create(self, proxy: ProxyRecord) -> None:
        await self.collection.insert_one(proxy.model_dump())

    async def available_for_account(self, account_id: str) -> list[dict[str, Any]]:
        return await self.collection.find({"account_id": account_id, "status": "available"}).to_list(None)

    async def delete_by_fingerprint(self, account_id: str, fingerprint: str) -> int:
        result = await self.collection.delete_one(
            {"account_id": account_id, "proxy_fingerprint": fingerprint}
        )
        return int(result.deleted_count)

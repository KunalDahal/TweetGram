from __future__ import annotations

from typing import Any

from tweetgrambot.app.core.models import Account
from tweetgrambot.app.database.repositories.base import MongoRepository
from tweetgrambot.app.utils.time import utc_now


class AccountsRepository(MongoRepository):
    collection_name = "accounts"

    async def create(self, account: Account) -> None:
        await self.collection.insert_one(account.model_dump())

    async def get(self, account_id: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"account_id": account_id})

    async def get_by_username(self, username: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"username": username})

    async def list_all(self) -> list[dict[str, Any]]:
        return await self.collection.find().sort("created_at", 1).to_list(None)

    async def list_active(self) -> list[dict[str, Any]]:
        return await self.collection.find({"is_active": True}).sort("created_at", 1).to_list(None)

    async def apply_default_cycle_delay(
        self, default_delay: int, previous_default_delay: int | None = None
    ) -> int:
        filters: list[dict[str, Any]] = [{"cycle_delay_seconds": {"$exists": False}}]
        if previous_default_delay is not None:
            filters.append({"cycle_delay_seconds": previous_default_delay})
        result = await self.collection.update_many(
            {"$or": filters},
            {"$set": {"cycle_delay_seconds": default_delay, "updated_at": utc_now()}},
        )
        return int(result.modified_count)

    async def set_active(self, account_id: str, active: bool) -> None:
        status = "starting" if active else "stopping"
        await self.touch(
            {"account_id": account_id},
            {"$set": {"is_active": active, "worker_status": status}},
        )

    async def set_worker_status(
        self, account_id: str, status: str, validation_error: str | None = None
    ) -> None:
        update: dict[str, Any] = {"worker_status": status, "updated_at": utc_now()}
        if validation_error is not None:
            update["auth.validation_error"] = validation_error
        await self.collection.update_one({"account_id": account_id}, {"$set": update})

    async def mark_auth_failed(self, account_id: str, reason: str) -> None:
        await self.touch(
            {"account_id": account_id},
            {
                "$set": {
                    "is_active": False,
                    "worker_status": "auth_error",
                    "auth.validation_error": reason,
                }
            },
        )

    async def update_cookie_auth(self, account_id: str, auth_token_enc: str, ct0_enc: str) -> None:
        await self.touch(
            {"account_id": account_id},
            {
                "$set": {
                    "auth.mode": "cookies",
                    "auth.auth_token_enc": auth_token_enc,
                    "auth.ct0_enc": ct0_enc,
                    "auth.validated_at": utc_now(),
                    "auth.validation_error": None,
                    "is_active": False,
                    "worker_status": "stopped",
                },
                "$unset": {
                    "auth.password_enc": "",
                    "auth.email_enc": "",
                    "auth.email_password_enc": "",
                },
            },
        )

    async def update_llm(self, account_id: str, llm_update: dict[str, Any]) -> None:
        update = {f"llm.{key}": value for key, value in llm_update.items()}
        update["updated_at"] = utc_now()
        await self.collection.update_one({"account_id": account_id}, {"$set": update})

    async def delete_account(self, account_id: str) -> int:
        result = await self.collection.delete_one({"account_id": account_id})
        return int(result.deleted_count)

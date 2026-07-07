from __future__ import annotations

from typing import Any

from tweetgrambot.app.config.constants import RUNTIME_SETTINGS_ID
from tweetgrambot.app.database.repositories.base import MongoRepository
from tweetgrambot.app.utils.time import utc_now


class SettingsRepository(MongoRepository):
    collection_name = "app_settings"

    async def get_runtime(self) -> dict[str, Any] | None:
        return await self.collection.find_one({"_id": RUNTIME_SETTINGS_ID})

    async def sync_runtime_from_env(
        self,
        *,
        telegram_target_channel_id: str,
        default_cycle_delay_seconds: int,
        max_retry_attempts: int,
    ) -> dict[str, Any] | None:
        previous = await self.get_runtime()
        await self.collection.update_one(
            {"_id": RUNTIME_SETTINGS_ID},
            {
                "$set": {
                    "telegram_target_channel_id": telegram_target_channel_id,
                    "default_cycle_delay_seconds": default_cycle_delay_seconds,
                    "max_retry_attempts": max_retry_attempts,
                    "updated_at": utc_now(),
                },
                "$setOnInsert": {
                    "_id": RUNTIME_SETTINGS_ID,
                    "global_llm_prompt": "",
                    "global_prompt_version": 1,
                }
            },
            upsert=True,
        )
        return previous

    async def ensure_runtime(self, telegram_target_channel_id: str, default_delay: int) -> None:
        await self.sync_runtime_from_env(
            telegram_target_channel_id=telegram_target_channel_id,
            default_cycle_delay_seconds=default_delay,
            max_retry_attempts=3,
        )

    async def update_prompt(self, prompt: str) -> int:
        result = await self.collection.find_one_and_update(
            {"_id": RUNTIME_SETTINGS_ID},
            {"$set": {"global_llm_prompt": prompt, "updated_at": utc_now()}, "$inc": {"global_prompt_version": 1}},
            return_document=True,
        )
        return int(result["global_prompt_version"])

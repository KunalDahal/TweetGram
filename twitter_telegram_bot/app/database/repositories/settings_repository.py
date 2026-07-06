from __future__ import annotations

from typing import Any

from twitter_telegram_bot.app.config.constants import RUNTIME_SETTINGS_ID
from twitter_telegram_bot.app.database.repositories.base import MongoRepository
from twitter_telegram_bot.app.utils.time import utc_now


class SettingsRepository(MongoRepository):
    collection_name = "app_settings"

    async def get_runtime(self) -> dict[str, Any] | None:
        return await self.collection.find_one({"_id": RUNTIME_SETTINGS_ID})

    async def ensure_runtime(self, telegram_target_channel_id: str, default_delay: int) -> None:
        await self.collection.update_one(
            {"_id": RUNTIME_SETTINGS_ID},
            {
                "$setOnInsert": {
                    "_id": RUNTIME_SETTINGS_ID,
                    "telegram_target_channel_id": telegram_target_channel_id,
                    "global_llm_prompt": "",
                    "global_prompt_version": 1,
                    "default_cycle_delay_seconds": default_delay,
                    "updated_at": utc_now(),
                }
            },
            upsert=True,
        )

    async def update_prompt(self, prompt: str) -> int:
        result = await self.collection.find_one_and_update(
            {"_id": RUNTIME_SETTINGS_ID},
            {"$set": {"global_llm_prompt": prompt, "updated_at": utc_now()}, "$inc": {"global_prompt_version": 1}},
            return_document=True,
        )
        return int(result["global_prompt_version"])

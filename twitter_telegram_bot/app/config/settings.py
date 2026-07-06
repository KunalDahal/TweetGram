from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = Field(alias="MONGODB_URI")
    mongodb_database: str = Field(alias="MONGODB_DATABASE")
    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_target_channel_id: str = Field(alias="TELEGRAM_TARGET_CHANNEL_ID")
    allowed_telegram_user_ids: set[int] = Field(alias="ALLOWED_TELEGRAM_USER_IDS")
    encryption_key: str = Field(alias="ENCRYPTION_KEY")
    temp_media_directory: Path = Field(default=Path("storage/temp"), alias="TEMP_MEDIA_DIRECTORY")
    default_cycle_delay_seconds: int = Field(default=900, alias="DEFAULT_CYCLE_DELAY_SECONDS")
    max_retry_attempts: int = Field(default=3, alias="MAX_RETRY_ATTEMPTS")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("allowed_telegram_user_ids", mode="before")
    @classmethod
    def parse_allowed_users(cls, value: object) -> set[int]:
        if isinstance(value, set):
            return value
        if isinstance(value, str):
            return {int(part.strip()) for part in value.split(",") if part.strip()}
        if isinstance(value, list | tuple):
            return {int(item) for item in value}
        raise TypeError("ALLOWED_TELEGRAM_USER_IDS must be comma-separated integers")

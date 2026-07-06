from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


AuthMode = Literal["credentials", "cookies"]
WorkerStatus = Literal["inactive", "starting", "running", "stopping", "stopped", "error"]
JobStatus = Literal[
    "discovered",
    "downloading",
    "downloaded",
    "caption_generating",
    "caption_generated",
    "telegram_sending",
    "telegram_sent",
    "failed",
    "cancelled",
]


class AccountAuth(BaseModel):
    mode: AuthMode
    password_enc: str | None = None
    email_enc: str | None = None
    email_password_enc: str | None = None
    auth_token_enc: str | None = None
    ct0_enc: str | None = None
    validated_at: datetime | None = None
    validation_error: str | None = None


class LLMConfig(BaseModel):
    provider: str | None = None
    model: str | None = None
    api_key_enc: str | None = None
    key_fingerprint: str | None = None
    enabled: bool = False


class Account(BaseModel):
    account_id: str
    username: str
    auth: AccountAuth
    llm: LLMConfig = Field(default_factory=LLMConfig)
    is_active: bool = False
    worker_status: WorkerStatus = "inactive"
    active_proxy_id: str | None = None
    cycle_delay_seconds: int = 900
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ListAssignment(BaseModel):
    account_id: str
    twitter_list_id: str
    sequence: int
    status: str = "active"
    baseline_post_id: str | None = None
    baseline_observed_at: datetime | None = None
    last_delivered_post_id: str | None = None
    resume_cursor: str | None = None
    cancel_requested: bool = False
    assigned_at: datetime = Field(default_factory=utc_now)
    last_cycle_started_at: datetime | None = None
    last_cycle_completed_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utc_now)


class ProxyRecord(BaseModel):
    account_id: str
    proxy_enc: str
    proxy_fingerprint: str
    status: str = "available"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PostSource(BaseModel):
    type: str
    source_url: str
    source_caption: str | None = None
    quote_caption: str | None = None
    reposted_post_id: str | None = None
    quoted_post_id: str | None = None
    published_at: datetime | None = None


class MediaItem(BaseModel):
    origin: str
    source_url: str
    media_type: str
    media_index: int
    download_status: str = "pending"
    temp_path: str | None = None


class JobLLM(BaseModel):
    provider: str
    model: str
    prompt_version: int
    generated_caption: str | None = None


class JobDelivery(BaseModel):
    telegram_message_ids: list[int] = Field(default_factory=list)
    sent_at: datetime | None = None


class PostJob(BaseModel):
    account_id: str
    twitter_list_id: str
    source_post_id: str
    source: PostSource
    media: list[MediaItem] = Field(default_factory=list)
    llm: JobLLM
    delivery: JobDelivery = Field(default_factory=JobDelivery)
    status: JobStatus = "discovered"
    retry_count: int = 0
    last_error: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class WorkerLog(BaseModel):
    account_id: str
    worker_id: str
    level: str
    event: str
    message: str
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class AppSettings(BaseModel):
    id: str = Field(default="runtime", serialization_alias="_id")
    telegram_target_channel_id: str
    global_llm_prompt: str = ""
    global_prompt_version: int = 1
    default_cycle_delay_seconds: int = 900
    updated_at: datetime = Field(default_factory=utc_now)

from __future__ import annotations

from twitter_telegram_bot.app.database.repositories.post_jobs_repository import PostJobsRepository
from twitter_telegram_bot.app.services.checkpoint_service import CheckpointService
from twitter_telegram_bot.app.services.encryption_service import EncryptionService
from twitter_telegram_bot.app.services.llm.provider_registry import ProviderRegistry
from twitter_telegram_bot.app.services.media_downloader import MediaDownloader
from twitter_telegram_bot.app.services.retry_service import RetryService
from twitter_telegram_bot.app.services.telegram_publisher import TelegramPublisher


class JobRunner:
    def __init__(
        self,
        *,
        jobs: PostJobsRepository,
        checkpoints: CheckpointService,
        media_downloader: MediaDownloader,
        llm_registry: ProviderRegistry,
        telegram_publisher: TelegramPublisher,
        encryption: EncryptionService,
        retry: RetryService,
    ) -> None:
        self.jobs = jobs
        self.checkpoints = checkpoints
        self.media_downloader = media_downloader
        self.llm_registry = llm_registry
        self.telegram_publisher = telegram_publisher
        self.encryption = encryption
        self.retry = retry

    async def run_job(self, job: dict, account: dict, runtime_settings: dict) -> None:
        if not account.get("llm", {}).get("api_key_enc"):
            raise ValueError("LLM API key is missing.")
        await self.jobs.set_status(job["_id"], "downloading")
        await self.retry.run(lambda: self.media_downloader.download_job_media(job))

        caption = job.get("llm", {}).get("generated_caption")
        if not caption:
            await self.jobs.set_status(job["_id"], "caption_generating")
            provider = self.llm_registry.get(job["llm"]["provider"])
            api_key = self.encryption.decrypt(account["llm"]["api_key_enc"])
            caption = await self.retry.run(
                lambda: provider.generate_caption(
                    api_key=api_key,
                    model=job["llm"]["model"],
                    global_prompt=runtime_settings.get("global_llm_prompt", ""),
                    source_text=job["source"].get("source_caption") or "",
                    quote_text=job["source"].get("quote_caption"),
                    source_url=job["source"]["source_url"],
                )
            )
            await self.jobs.save_caption(job["_id"], caption)

        await self.jobs.set_status(job["_id"], "telegram_sending")
        message_ids = await self.retry.run(lambda: self.telegram_publisher.publish_job(job, caption))
        await self.jobs.mark_sent(job["_id"], message_ids)
        await self.checkpoints.mark_delivered(
            job["account_id"], job["twitter_list_id"], job["source_post_id"]
        )

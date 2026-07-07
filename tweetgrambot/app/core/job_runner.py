from __future__ import annotations

from tweetgrambot.app.database.repositories.post_jobs_repository import PostJobsRepository
from tweetgrambot.app.services.checkpoint_service import CheckpointService
from tweetgrambot.app.services.encryption_service import EncryptionService
from tweetgrambot.app.services.llm.provider_registry import ProviderRegistry
from tweetgrambot.app.services.media_downloader import MediaDownloader
from tweetgrambot.app.services.retry_service import RetryService
from tweetgrambot.app.services.telegram_publisher import TelegramPublisher


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
        downloaded_media = await self.retry.run(lambda: self.media_downloader.download_job_media(job))
        if downloaded_media != job.get("media", []):
            job["media"] = downloaded_media
            await self.jobs.save_media(job["_id"], downloaded_media)

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
                    source_text=self._caption_context(job),
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

    def _caption_context(self, job: dict) -> str:
        source = job["source"]
        lines = [
            f"Post type: {source.get('type') or 'original'}",
            f"Post text: {source.get('source_caption') or '<no text>'}",
        ]
        if source.get("quote_caption"):
            lines.append(f"Quoted post text: {source['quote_caption']}")
        if source.get("reposted_post_id"):
            lines.append(f"Reposted post ID: {source['reposted_post_id']}")
        if source.get("quoted_post_id"):
            lines.append(f"Quoted post ID: {source['quoted_post_id']}")
        if source.get("published_at"):
            lines.append(f"Published at: {source['published_at']}")
        if job.get("media"):
            media_urls = [item.get("source_url") for item in job["media"] if item.get("source_url")]
            lines.append(f"Media count: {len(media_urls)}")
            lines.extend(f"Media URL: {url}" for url in media_urls)
        lines.append(f"Source URL: {source['source_url']}")
        return "\n".join(lines)

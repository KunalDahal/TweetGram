from __future__ import annotations

from twitter_telegram_bot.app.core.models import JobLLM, MediaItem, PostJob, PostSource
from twitter_telegram_bot.app.services.twscrape_adapter import ScrapedPost


class PostExtractor:
    def build_job(
        self,
        *,
        account_id: str,
        twitter_list_id: str,
        post: ScrapedPost,
        provider: str,
        model: str,
        prompt_version: int,
    ) -> PostJob:
        source_type = "repost" if post.reposted_post_id else "quote" if post.quoted_post_id else "original"
        media = [
            MediaItem(
                origin="source",
                source_url=url,
                media_type="image",
                media_index=index,
            )
            for index, url in enumerate(post.media_urls)
        ]
        return PostJob(
            account_id=account_id,
            twitter_list_id=twitter_list_id,
            source_post_id=post.post_id,
            source=PostSource(
                type=source_type,
                source_url=post.url,
                source_caption=post.text,
                quote_caption=post.quote_text,
                reposted_post_id=post.reposted_post_id,
                quoted_post_id=post.quoted_post_id,
                published_at=post.published_at,
            ),
            media=media,
            llm=JobLLM(provider=provider, model=model, prompt_version=prompt_version),
        )

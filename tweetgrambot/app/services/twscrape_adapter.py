from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class ScrapedPost:
    post_id: str
    url: str
    text: str | None
    published_at: datetime | None = None
    quote_text: str | None = None
    quoted_post_id: str | None = None
    reposted_post_id: str | None = None
    media_urls: list[str] = field(default_factory=list)


class TwscrapeAdapter:
    async def newest_post_id_for_list(self, twitter_list_id: str, account: dict, proxy: str | None) -> str | None:
        _ = (twitter_list_id, account, proxy)
        return None

    async def new_posts_for_list(
        self,
        *,
        twitter_list_id: str,
        since_post_id: str | None,
        account: dict,
        proxy: str | None,
    ) -> list[ScrapedPost]:
        _ = (twitter_list_id, since_post_id, account, proxy)
        return []

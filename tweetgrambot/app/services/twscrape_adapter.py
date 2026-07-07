from __future__ import annotations

import tempfile
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator

from twscrape import API, AccountsPool, ConnectError, NoAccountError, Tweet

from tweetgrambot.app.services.encryption_service import EncryptionService


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


class TwscrapeAuthenticationError(RuntimeError):
    """Raised when X requires fresh account authentication."""


class TwscrapeAdapter:
    def __init__(self, encryption: EncryptionService) -> None:
        self.encryption = encryption

    async def newest_post_id_for_list(self, twitter_list_id: str, account: dict, proxy: str | None) -> str | None:
        tweets = await self._fetch_list_posts(
            twitter_list_id=twitter_list_id,
            account=account,
            proxy=proxy,
            limit=1,
        )
        if not tweets:
            return None
        return tweets[0].post_id

    async def new_posts_for_list(
        self,
        *,
        twitter_list_id: str,
        since_post_id: str | None,
        account: dict,
        proxy: str | None,
    ) -> list[ScrapedPost]:
        posts = await self._fetch_list_posts(
            twitter_list_id=twitter_list_id,
            account=account,
            proxy=proxy,
            limit=100,
        )
        if since_post_id is None:
            return posts

        new_posts: list[ScrapedPost] = []
        for post in posts:
            if post.post_id == since_post_id:
                break
            new_posts.append(post)
        return new_posts

    async def _fetch_list_posts(
        self,
        *,
        twitter_list_id: str,
        account: dict,
        proxy: str | None,
        limit: int,
    ) -> list[ScrapedPost]:
        try:
            list_id = int(twitter_list_id)
        except ValueError as exc:
            raise ValueError(f"Invalid Twitter List ID: {twitter_list_id}") from exc

        async with self._api_for_account(account, proxy) as api:
            posts: list[ScrapedPost] = []
            try:
                async for tweet in api.list_timeline(list_id, limit=limit):
                    posts.append(self._to_scraped_post(tweet))
            except NoAccountError as exc:
                raise TwscrapeAuthenticationError("No active X account is available.") from exc
            except ConnectError:
                raise

        return posts

    @asynccontextmanager
    async def _api_for_account(self, account: dict, proxy: str | None) -> AsyncIterator[API]:
        auth = account.get("auth") or {}
        auth_token_enc = auth.get("auth_token_enc")
        ct0_enc = auth.get("ct0_enc")
        if not auth_token_enc or not ct0_enc:
            raise TwscrapeAuthenticationError("X auth_token and ct0 cookies are missing.")

        username = account.get("username") or account.get("account_id") or "account"
        cookies = (
            f"auth_token={self.encryption.decrypt(auth_token_enc)}; "
            f"ct0={self.encryption.decrypt(ct0_enc)}"
        )

        with tempfile.TemporaryDirectory(prefix="tweetgrambot_tws_") as temp_dir:
            pool = AccountsPool(
                db_file=str(Path(temp_dir) / "accounts.db"),
                raise_when_no_account=True,
            )
            await pool.add_account_cookies(username, cookies)
            yield API(pool, proxy=proxy, raise_when_no_account=True)

    def _to_scraped_post(self, tweet: Tweet) -> ScrapedPost:
        quote = tweet.quotedTweet
        repost = tweet.retweetedTweet
        return ScrapedPost(
            post_id=tweet.id_str,
            url=tweet.url,
            text=tweet.rawContent,
            published_at=tweet.date,
            quote_text=quote.rawContent if quote else None,
            quoted_post_id=quote.id_str if quote else None,
            reposted_post_id=repost.id_str if repost else None,
            media_urls=self._media_urls(tweet),
        )

    def _media_urls(self, tweet: Tweet) -> list[str]:
        media = tweet.media
        if not media:
            return []
        urls = [photo.url for photo in media.photos]
        urls.extend(video.thumbnailUrl for video in media.videos)
        urls.extend(animated.thumbnailUrl for animated in media.animated)
        return urls

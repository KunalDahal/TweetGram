from __future__ import annotations

import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import aiohttp


class MediaDownloader:
    def __init__(self, temp_directory: Path) -> None:
        self.temp_directory = temp_directory

    async def download_job_media(self, job: dict) -> list[dict]:
        self.temp_directory.mkdir(parents=True, exist_ok=True)
        downloaded: list[dict] = []
        for item in job.get("media", []):
            media_item = dict(item)
            target_path = self._target_path(job, media_item)
            try:
                await self._download(media_item["source_url"], target_path)
            except Exception:
                media_item["download_status"] = "failed"
                media_item["temp_path"] = None
                downloaded.append(media_item)
                raise
            media_item["download_status"] = "downloaded"
            media_item["temp_path"] = str(target_path)
            downloaded.append(media_item)
        return downloaded

    async def _download(self, url: str, target_path: Path) -> None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                response.raise_for_status()
                content = await response.read()
        target_path.write_bytes(content)

    def _target_path(self, job: dict, media_item: dict) -> Path:
        extension = self._extension(media_item["source_url"], media_item.get("media_type", "media"))
        return (
            self.temp_directory
            / job["account_id"]
            / job["twitter_list_id"]
            / job["source_post_id"]
            / f"{int(media_item.get('media_index', 0)):02d}{extension}"
        )

    def _extension(self, url: str, media_type: str) -> str:
        path = urlparse(url).path
        suffix = Path(path).suffix
        if suffix:
            return suffix
        guessed = mimetypes.guess_extension(media_type)
        return guessed or ".bin"

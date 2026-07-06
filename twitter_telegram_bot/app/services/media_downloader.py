from __future__ import annotations

from pathlib import Path


class MediaDownloader:
    def __init__(self, temp_directory: Path) -> None:
        self.temp_directory = temp_directory

    async def download_job_media(self, job: dict) -> list[dict]:
        self.temp_directory.mkdir(parents=True, exist_ok=True)
        return list(job.get("media", []))

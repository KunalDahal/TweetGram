from __future__ import annotations

import shutil
from pathlib import Path


class TempStorageService:
    def __init__(self, base_directory: Path) -> None:
        self.base_directory = base_directory

    def job_directory(self, account_id: str, twitter_list_id: str, source_post_id: str) -> Path:
        return self.base_directory / account_id / twitter_list_id / source_post_id

    def remove_job_directory(self, account_id: str, twitter_list_id: str, source_post_id: str) -> None:
        shutil.rmtree(self.job_directory(account_id, twitter_list_id, source_post_id), ignore_errors=True)

    def remove_account_directory(self, account_id: str) -> None:
        shutil.rmtree(self.base_directory / account_id, ignore_errors=True)

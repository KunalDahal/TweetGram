from __future__ import annotations

import pytest

from tweetgrambot.app.core.worker import Worker


class FakeAccounts:
    pass


class FakeLists:
    def __init__(self) -> None:
        self.started: list[tuple[str, str]] = []
        self.completed: list[tuple[str, str]] = []
        self.initialized: list[tuple[str, str, str | None]] = []

    async def mark_cycle_started(self, account_id: str, twitter_list_id: str) -> None:
        self.started.append((account_id, twitter_list_id))

    async def mark_cycle_completed(self, account_id: str, twitter_list_id: str) -> None:
        self.completed.append((account_id, twitter_list_id))

    async def initialize_checkpoint(
        self, account_id: str, twitter_list_id: str, source_post_id: str | None
    ) -> None:
        self.initialized.append((account_id, twitter_list_id, source_post_id))


class FakeJobs:
    def __init__(self) -> None:
        self.created = []

    async def create(self, job) -> None:
        self.created.append(job)


class FakeScraper:
    def __init__(self) -> None:
        self.newest_calls: list[tuple[str, dict, str | None]] = []
        self.new_posts_calls: list[dict] = []

    async def newest_post_id_for_list(
        self, twitter_list_id: str, account: dict, proxy: str | None
    ) -> str:
        self.newest_calls.append((twitter_list_id, account, proxy))
        return "post_latest"

    async def new_posts_for_list(self, **kwargs):
        self.new_posts_calls.append(kwargs)
        return []


class FakeExtractor:
    pass


class FakeJobRunner:
    pass


class FakeAlerts:
    pass


def make_worker(*, lists: FakeLists, jobs: FakeJobs, scraper: FakeScraper) -> Worker:
    return Worker(
        account_id="acc_1",
        accounts=FakeAccounts(),
        lists=lists,
        jobs=jobs,
        logs=None,
        settings=None,
        proxy_manager=None,
        scraper=scraper,
        extractor=FakeExtractor(),
        job_runner=FakeJobRunner(),
        alerts=FakeAlerts(),
    )


@pytest.mark.asyncio
async def test_process_list_initializes_missing_checkpoint_and_skips_history() -> None:
    lists = FakeLists()
    jobs = FakeJobs()
    scraper = FakeScraper()
    worker = make_worker(lists=lists, jobs=jobs, scraper=scraper)

    await worker._process_list(
        account={"llm": {"provider": "openai", "model": "gpt-test"}},
        assignment={"twitter_list_id": "list_1", "last_delivered_post_id": None, "baseline_post_id": None},
        proxy="proxy_1",
        runtime_settings={},
    )

    assert lists.started == [("acc_1", "list_1")]
    assert lists.initialized == [("acc_1", "list_1", "post_latest")]
    assert lists.completed == [("acc_1", "list_1")]
    assert scraper.new_posts_calls == []
    assert jobs.created == []


@pytest.mark.asyncio
async def test_process_list_uses_existing_checkpoint_for_new_posts() -> None:
    lists = FakeLists()
    jobs = FakeJobs()
    scraper = FakeScraper()
    worker = make_worker(lists=lists, jobs=jobs, scraper=scraper)

    await worker._process_list(
        account={"llm": {"provider": "openai", "model": "gpt-test"}},
        assignment={"twitter_list_id": "list_1", "last_delivered_post_id": "post_10"},
        proxy=None,
        runtime_settings={},
    )

    assert lists.initialized == []
    assert scraper.new_posts_calls == [
        {
            "twitter_list_id": "list_1",
            "since_post_id": "post_10",
            "account": {"llm": {"provider": "openai", "model": "gpt-test"}},
            "proxy": None,
        }
    ]


@pytest.mark.asyncio
async def test_process_list_uses_observed_empty_baseline_for_new_posts() -> None:
    lists = FakeLists()
    jobs = FakeJobs()
    scraper = FakeScraper()
    worker = make_worker(lists=lists, jobs=jobs, scraper=scraper)

    await worker._process_list(
        account={"llm": {"provider": "openai", "model": "gpt-test"}},
        assignment={
            "twitter_list_id": "list_1",
            "last_delivered_post_id": None,
            "baseline_post_id": None,
            "baseline_observed_at": "2026-07-07T00:00:00Z",
            "resume_cursor": "empty_baseline",
        },
        proxy=None,
        runtime_settings={},
    )

    assert lists.initialized == []
    assert scraper.new_posts_calls == [
        {
            "twitter_list_id": "list_1",
            "since_post_id": None,
            "account": {"llm": {"provider": "openai", "model": "gpt-test"}},
            "proxy": None,
        }
    ]


@pytest.mark.asyncio
async def test_process_list_reinitializes_corrupted_none_checkpoint() -> None:
    lists = FakeLists()
    jobs = FakeJobs()
    scraper = FakeScraper()
    worker = make_worker(lists=lists, jobs=jobs, scraper=scraper)

    await worker._process_list(
        account={"llm": {"provider": "openai", "model": "gpt-test"}},
        assignment={
            "twitter_list_id": "list_1",
            "last_delivered_post_id": None,
            "baseline_post_id": None,
            "baseline_observed_at": "2026-07-07T00:00:00Z",
            "resume_cursor": None,
        },
        proxy=None,
        runtime_settings={},
    )

    assert lists.initialized == [("acc_1", "list_1", "post_latest")]
    assert scraper.new_posts_calls == []

from __future__ import annotations

from pathlib import Path

import pytest

from tweetgrambot.app.services.telegram_publisher import TelegramPublisher


class FakeMessage:
    def __init__(self, message_id: int) -> None:
        self.message_id = message_id


class FakeBot:
    def __init__(self) -> None:
        self.sent_messages = []
        self.sent_photos = []
        self.sent_groups = []

    async def send_message(self, **kwargs):
        self.sent_messages.append(kwargs)
        return FakeMessage(len(self.sent_messages))

    async def send_photo(self, **kwargs):
        self.sent_photos.append(kwargs)
        return FakeMessage(2)

    async def send_media_group(self, **kwargs):
        self.sent_groups.append(kwargs)
        return [FakeMessage(3), FakeMessage(4)]


@pytest.mark.asyncio
async def test_publish_job_sends_downloaded_photo(tmp_path: Path) -> None:
    media_path = tmp_path / "photo.jpg"
    media_path.write_bytes(b"image")
    bot = FakeBot()
    publisher = TelegramPublisher(bot, "channel")

    message_ids = await publisher.publish_job(
        {
            "source": {"source_url": "https://x.com/user/status/1"},
            "media": [
                {
                    "download_status": "downloaded",
                    "temp_path": str(media_path),
                }
            ],
        },
        "caption",
    )

    assert message_ids == [2]
    assert bot.sent_messages == []
    assert len(bot.sent_photos) == 1


@pytest.mark.asyncio
async def test_publish_job_falls_back_to_text_without_downloaded_media() -> None:
    bot = FakeBot()
    publisher = TelegramPublisher(bot, "channel")

    message_ids = await publisher.publish_job(
        {
            "source": {"source_url": "https://x.com/user/status/1"},
            "media": [{"download_status": "failed", "temp_path": None}],
        },
        "caption",
    )

    assert message_ids == [1]
    assert len(bot.sent_messages) == 1


@pytest.mark.asyncio
async def test_publish_job_splits_long_text_messages() -> None:
    bot = FakeBot()
    publisher = TelegramPublisher(bot, "channel")
    caption = "A" * 4100

    message_ids = await publisher.publish_job(
        {
            "source": {"source_url": "https://x.com/user/status/1"},
            "media": [],
        },
        caption,
    )

    assert message_ids == [1, 2]
    assert len(bot.sent_messages) == 2
    assert all(len(message["text"]) <= publisher.text_message_limit for message in bot.sent_messages)

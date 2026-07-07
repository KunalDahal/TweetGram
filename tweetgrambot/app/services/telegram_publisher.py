from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path

from telegram import InputMediaPhoto


class TelegramPublisher:
    media_caption_limit = 1024
    text_message_limit = 4096

    def __init__(self, bot, target_channel_id: str) -> None:
        self.bot = bot
        self.target_channel_id = target_channel_id

    def ensure_source_link(self, caption: str, source_url: str) -> str:
        if source_url in caption:
            return caption
        return f"{caption.rstrip()}\n\nSource: {source_url}"

    async def publish_job(self, job: dict, caption: str) -> list[int]:
        caption = self.ensure_source_link(caption, job["source"]["source_url"])
        downloaded_media = [
            item for item in job.get("media", [])
            if item.get("download_status") == "downloaded" and item.get("temp_path")
        ]
        if not downloaded_media:
            return await self._send_text(caption)

        if len(downloaded_media) == 1:
            media_path = Path(downloaded_media[0]["temp_path"])
            with media_path.open("rb") as media_file:
                message = await self.bot.send_photo(
                    chat_id=self.target_channel_id,
                    photo=media_file,
                    caption=caption if len(caption) <= self.media_caption_limit else None,
                )
            message_ids = [message.message_id]
            if len(caption) > self.media_caption_limit:
                message_ids.extend(await self._send_text(caption))
            return message_ids

        with ExitStack() as stack:
            media_group = []
            for index, item in enumerate(downloaded_media[:10]):
                media_file = stack.enter_context(Path(item["temp_path"]).open("rb"))
                media_group.append(
                    InputMediaPhoto(
                        media=media_file,
                        caption=caption
                        if index == 0 and len(caption) <= self.media_caption_limit
                        else None,
                    )
                )
            messages = await self.bot.send_media_group(
                chat_id=self.target_channel_id,
                media=media_group,
            )
        message_ids = [message.message_id for message in messages]
        if len(caption) > self.media_caption_limit:
            message_ids.extend(await self._send_text(caption))
        return message_ids

    async def _send_text(self, text: str) -> list[int]:
        message_ids: list[int] = []
        for chunk in self._split_text(text):
            message = await self.bot.send_message(chat_id=self.target_channel_id, text=chunk)
            message_ids.append(message.message_id)
        return message_ids

    def _split_text(self, text: str) -> list[str]:
        if len(text) <= self.text_message_limit:
            return [text]

        chunks: list[str] = []
        remaining = text
        while remaining:
            if len(remaining) <= self.text_message_limit:
                chunks.append(remaining)
                break
            split_at = remaining.rfind("\n", 0, self.text_message_limit + 1)
            if split_at < self.text_message_limit // 2:
                split_at = remaining.rfind(" ", 0, self.text_message_limit + 1)
            if split_at < self.text_message_limit // 2:
                split_at = self.text_message_limit
            chunks.append(remaining[:split_at].rstrip())
            remaining = remaining[split_at:].lstrip()
        return chunks

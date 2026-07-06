from __future__ import annotations


class TelegramPublisher:
    def __init__(self, bot, target_channel_id: str) -> None:
        self.bot = bot
        self.target_channel_id = target_channel_id

    def ensure_source_link(self, caption: str, source_url: str) -> str:
        if source_url in caption:
            return caption
        return f"{caption.rstrip()}\n\nSource: {source_url}"

    async def publish_job(self, job: dict, caption: str) -> list[int]:
        caption = self.ensure_source_link(caption, job["source"]["source_url"])
        if not job.get("media"):
            message = await self.bot.send_message(chat_id=self.target_channel_id, text=caption)
            return [message.message_id]
        message = await self.bot.send_message(chat_id=self.target_channel_id, text=caption)
        return [message.message_id]

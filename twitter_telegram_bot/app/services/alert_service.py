from __future__ import annotations


class AlertService:
    def __init__(self, bot, allowed_user_ids: set[int]) -> None:
        self.bot = bot
        self.allowed_user_ids = allowed_user_ids

    async def notify_admins(self, message: str) -> None:
        for user_id in self.allowed_user_ids:
            await self.bot.send_message(chat_id=user_id, text=message)

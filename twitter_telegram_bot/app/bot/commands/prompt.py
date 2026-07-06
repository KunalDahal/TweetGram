from __future__ import annotations

import shlex

from telegram import Update
from telegram.ext import ContextTypes

from twitter_telegram_bot.app.bot.responses.status_messages import prompt_updated
from twitter_telegram_bot.app.core.account_manager import AccountManager


class PromptCommandHandler:
    def __init__(self, manager: AccountManager) -> None:
        self.manager = manager

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = update.effective_message.text if update.effective_message else ""
        args = shlex.split(text)
        if len(args) < 2:
            await update.effective_message.reply_text("Usage: /prompt \"text\"")
            return
        version = await self.manager.update_global_prompt(args[1])
        await update.effective_message.reply_text(prompt_updated(version))

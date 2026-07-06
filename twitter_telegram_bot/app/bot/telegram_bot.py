from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from twitter_telegram_bot.app.bot.authorization import is_authorized
from twitter_telegram_bot.app.bot.commands.acc import AccCommandHandler
from twitter_telegram_bot.app.bot.commands.prompt import PromptCommandHandler
from twitter_telegram_bot.app.bot.responses.error_messages import UNAUTHORIZED, command_error
from twitter_telegram_bot.app.config.settings import Settings
from twitter_telegram_bot.app.core.account_manager import AccountManager


def build_application(settings: Settings, manager: AccountManager) -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    acc = AccCommandHandler(manager)
    prompt = PromptCommandHandler(manager)

    async def guarded_acc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_authorized(update.effective_user.id if update.effective_user else None, settings.allowed_telegram_user_ids):
            await update.effective_message.reply_text(UNAUTHORIZED)
            return
        try:
            await acc.handle(update, context)
        except Exception as exc:
            await update.effective_message.reply_text(command_error(exc))

    async def guarded_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_authorized(update.effective_user.id if update.effective_user else None, settings.allowed_telegram_user_ids):
            await update.effective_message.reply_text(UNAUTHORIZED)
            return
        try:
            await prompt.handle(update, context)
        except Exception as exc:
            await update.effective_message.reply_text(command_error(exc))

    app.add_handler(CommandHandler("acc", guarded_acc))
    app.add_handler(CommandHandler("prompt", guarded_prompt))
    return app

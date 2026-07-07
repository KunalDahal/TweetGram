from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from tweetgrambot.app.bot.authorization import is_authorized
from tweetgrambot.app.bot.commands.acc import AccCommandHandler
from tweetgrambot.app.bot.commands.prompt import PromptCommandHandler
from tweetgrambot.app.bot.responses.error_messages import UNAUTHORIZED, command_error
from tweetgrambot.app.bot.responses.help_messages import HELP_MESSAGE
from tweetgrambot.app.config.settings import Settings
from tweetgrambot.app.core.account_manager import AccountManager


logger = logging.getLogger(__name__)


def build_application(settings: Settings, manager: AccountManager) -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    acc = AccCommandHandler(manager)
    prompt = PromptCommandHandler(manager)

    async def guarded_acc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id if update.effective_user else None
        logger.info("Received /acc command from user_id=%s", user_id)
        if not is_authorized(user_id, settings.allowed_telegram_user_ids):
            logger.warning("Rejected unauthorized /acc command from user_id=%s", user_id)
            await update.effective_message.reply_text(UNAUTHORIZED)
            return
        try:
            await acc.handle(update, context)
        except Exception as exc:
            await update.effective_message.reply_text(command_error(exc))

    async def guarded_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id if update.effective_user else None
        logger.info("Received /prompt command from user_id=%s", user_id)
        if not is_authorized(user_id, settings.allowed_telegram_user_ids):
            logger.warning("Rejected unauthorized /prompt command from user_id=%s", user_id)
            await update.effective_message.reply_text(UNAUTHORIZED)
            return
        try:
            await prompt.handle(update, context)
        except Exception as exc:
            await update.effective_message.reply_text(command_error(exc))

    async def guarded_llm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id if update.effective_user else None
        logger.info("Received LLM callback from user_id=%s", user_id)
        if not is_authorized(user_id, settings.allowed_telegram_user_ids):
            logger.warning("Rejected unauthorized LLM callback from user_id=%s", user_id)
            if update.callback_query:
                await update.callback_query.answer(UNAUTHORIZED, show_alert=True)
            return
        try:
            await acc.llm.handle_callback(update, context)
        except Exception as exc:
            if update.callback_query:
                await update.callback_query.edit_message_text(command_error(exc))

    async def guarded_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id if update.effective_user else None
        logger.info("Received help command from user_id=%s", user_id)
        if not is_authorized(user_id, settings.allowed_telegram_user_ids):
            logger.warning("Rejected unauthorized help command from user_id=%s", user_id)
            await update.effective_message.reply_text(UNAUTHORIZED)
            return
        await update.effective_message.reply_text(HELP_MESSAGE)

    app.add_handler(CommandHandler("start", guarded_help))
    app.add_handler(CommandHandler("help", guarded_help))
    app.add_handler(CommandHandler("acc", guarded_acc))
    app.add_handler(CommandHandler("prompt", guarded_prompt))
    app.add_handler(CallbackQueryHandler(guarded_llm_callback, pattern=r"^llm:"))
    return app

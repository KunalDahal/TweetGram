from __future__ import annotations

import shlex

from telegram import Update
from telegram.ext import ContextTypes

from tweetgrambot.app.bot.commands.llm import LlmCommandHandler
from tweetgrambot.app.bot.responses import account_messages
from tweetgrambot.app.core.account_manager import AccountManager


class AccCommandHandler:
    def __init__(self, manager: AccountManager) -> None:
        self.manager = manager
        self.llm = LlmCommandHandler(manager)

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        text = update.effective_message.text if update.effective_message else ""
        args = shlex.split(text)[1:]
        if len(args) == 2 and args[1] == "-lm":
            await update.effective_message.reply_text(
                f"Choose LLM provider for {args[0]}:",
                reply_markup=self.llm.provider_keyboard(args[0]),
            )
            return
        response = await self.dispatch(args)
        await update.effective_message.reply_text(response)

    async def dispatch(self, args: list[str]) -> str:
        if not args:
            return await self.manager.status()

        if args == ["-s"]:
            return await self.manager.status()

        if args[0] == "-a":
            username, password, email, email_password, *rest = args[1:]
            account_id = await self.manager.create_with_credentials(
                username=username,
                password=password,
                email=email,
                email_password=email_password,
                proxy=rest[0] if rest else None,
            )
            return account_messages.account_created(account_id)

        if args[0] == "-c":
            username, auth_token, ct0, *rest = args[1:]
            account_id = await self.manager.create_with_cookies(
                username=username,
                auth_token=auth_token,
                ct0=ct0,
                proxy=rest[0] if rest else None,
            )
            return account_messages.account_created(account_id)

        if len(args) >= 4 and args[1] == "-c":
            account_id, _, auth_token, ct0, *rest = args
            await self.manager.refresh_cookies(
                account_id=account_id,
                auth_token=auth_token,
                ct0=ct0,
                proxy=rest[0] if rest else None,
            )
            return account_messages.account_cookies_refreshed(account_id)

        if args[0] == "-r":
            account_id = args[1]
            await self.manager.remove_account(account_id)
            return account_messages.account_removed(account_id)

        if args[0] == "-l" and "-a" in args:
            twitter_list_id = args[1]
            account_id = args[args.index("-a") + 1]
            await self.manager.assign_list(account_id, twitter_list_id)
            return f"List {twitter_list_id} assigned to {account_id}."

        if args[0] == "-l" and "-r" in args:
            twitter_list_id = args[1]
            account_id = args[args.index("-r") + 1]
            await self.manager.remove_list(account_id, twitter_list_id)
            return f"List {twitter_list_id} removed from {account_id}."

        if args[0] == "-i":
            account_id = args[1]
            await self.manager.activate_account(account_id)
            return account_messages.account_activated(account_id)

        if args[0] == "-h":
            account_id = args[1]
            await self.manager.halt_account(account_id)
            return account_messages.account_halted(account_id)

        if args[0] == "-p" and "-a" in args:
            account_id = args[1]
            proxy = args[args.index("-a") + 1]
            await self.manager.add_proxy(account_id, proxy)
            return f"Proxy added to {account_id}."

        if args[0] == "-p" and "-r" in args:
            account_id = args[1]
            proxy = args[args.index("-r") + 1]
            removed = await self.manager.remove_proxy(account_id, proxy)
            return f"Removed {removed} proxy record(s) from {account_id}."

        if len(args) >= 3 and args[1] == "-ka":
            await self.manager.set_llm_key(args[0], args[2])
            return f"LLM key stored for {args[0]}."

        if len(args) >= 3 and args[1] == "-kr":
            await self.manager.remove_llm_key(args[0], args[2])
            return f"LLM key removed for {args[0]}."

        if len(args) >= 4 and args[1] == "-lm":
            await self.manager.set_llm_provider_model(args[0], args[2], args[3])
            return f"LLM provider/model set for {args[0]}."

        raise ValueError("Unsupported /acc command.")

from __future__ import annotations

import logging

from pymongo.errors import ServerSelectionTimeoutError
from telegram.ext import Application
from twscrape import set_log_level as set_twscrape_log_level

from tweetgrambot.app.bootstrap import Container
from tweetgrambot.app.bot.telegram_bot import build_application
from tweetgrambot.app.config.environment import get_settings
from tweetgrambot.app.config.settings import Settings


logger = logging.getLogger(__name__)


class SecretRedactionFilter(logging.Filter):
    def __init__(self, secrets: list[str]) -> None:
        super().__init__()
        self.secrets = [secret for secret in secrets if secret]

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._redact(record.msg)
        if isinstance(record.args, dict):
            record.args = {key: self._redact(value) for key, value in record.args.items()}
        elif isinstance(record.args, tuple):
            record.args = tuple(self._redact(value) for value in record.args)
        return True

    def _redact(self, value):
        if not isinstance(value, str):
            return value
        for secret in self.secrets:
            value = value.replace(secret, "<redacted>")
        return value


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    redaction_filter = SecretRedactionFilter([settings.telegram_bot_token])
    for handler in logging.getLogger().handlers:
        handler.addFilter(redaction_filter)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    set_twscrape_log_level("ERROR")


async def post_init(app: Application) -> None:
    container: Container = app.bot_data["container"]
    logger.info("Initializing TweetGramBot")
    try:
        await container.initialize()
    except ServerSelectionTimeoutError as exc:
        logger.error(
            "MongoDB is unreachable. If you use Atlas, allowlist this machine's IP "
            "in Atlas Network Access and verify the MONGODB_URI. Original error: %s",
            exc,
        )
        raise
    logger.info("TweetGramBot is running and polling Telegram updates")


async def post_shutdown(app: Application) -> None:
    container: Container = app.bot_data["container"]
    logger.info("Shutting down TweetGramBot")
    await container.worker_pool.stop_all()
    container.mongo.close()
    logger.info("TweetGramBot stopped")


def main() -> None:
    settings = get_settings()
    configure_logging(settings)
    logger.info("Starting TweetGramBot")
    container = Container(settings)
    application = build_application(settings, container.manager)
    application.bot_data["container"] = container
    application.post_init = post_init
    application.post_shutdown = post_shutdown
    application.run_polling()


if __name__ == "__main__":
    main()

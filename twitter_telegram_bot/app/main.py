from __future__ import annotations

from twitter_telegram_bot.app.bootstrap import Container
from twitter_telegram_bot.app.bot.telegram_bot import build_application
from twitter_telegram_bot.app.config.environment import get_settings


async def post_init(app) -> None:
    container: Container = app.bot_data["container"]
    await container.initialize()


def main() -> None:
    settings = get_settings()
    container = Container(settings)
    application = build_application(settings, container.manager)
    application.bot_data["container"] = container
    application.post_init = post_init
    application.run_polling()


if __name__ == "__main__":
    main()

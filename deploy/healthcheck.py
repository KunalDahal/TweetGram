from __future__ import annotations

from tweetgrambot.app.config.environment import get_settings


def main() -> None:
    settings = get_settings()
    if not settings.mongodb_uri or not settings.telegram_bot_token:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

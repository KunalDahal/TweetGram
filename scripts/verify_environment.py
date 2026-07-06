from __future__ import annotations

from cryptography.fernet import Fernet

from tweetgrambot.app.config.environment import get_settings


def main() -> None:
    settings = get_settings()
    Fernet(settings.encryption_key.encode("utf-8"))
    settings.temp_media_directory.mkdir(parents=True, exist_ok=True)
    print("Environment is valid.")


if __name__ == "__main__":
    main()

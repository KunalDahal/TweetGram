from __future__ import annotations

import shutil

from tweetgrambot.app.config.environment import get_settings


def main() -> None:
    temp_dir = get_settings().temp_media_directory
    shutil.rmtree(temp_dir, ignore_errors=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    print(f"Cleaned {temp_dir}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import asyncio

from tweetgrambot.app.config.environment import get_settings
from tweetgrambot.app.database.indexes import ensure_indexes
from tweetgrambot.app.database.mongo import Mongo


async def main() -> None:
    mongo = Mongo(get_settings())
    try:
        await ensure_indexes(mongo.database)
    finally:
        mongo.close()


if __name__ == "__main__":
    asyncio.run(main())

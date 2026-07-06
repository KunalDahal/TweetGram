from __future__ import annotations

from pymongo import ASCENDING


async def ensure_indexes(db) -> None:
    await db.accounts.create_index("account_id", unique=True)
    await db.accounts.create_index("username", unique=True)

    await db.list_assignments.create_index("twitter_list_id", unique=True)
    await db.list_assignments.create_index(
        [("account_id", ASCENDING), ("sequence", ASCENDING)],
        unique=True,
    )
    await db.list_assignments.create_index(
        [("account_id", ASCENDING), ("status", ASCENDING), ("sequence", ASCENDING)]
    )

    await db.proxies.create_index(
        [("account_id", ASCENDING), ("proxy_fingerprint", ASCENDING)],
        unique=True,
    )

    await db.post_jobs.create_index(
        [("account_id", ASCENDING), ("twitter_list_id", ASCENDING), ("source_post_id", ASCENDING)],
        unique=True,
    )
    await db.post_jobs.create_index(
        [("account_id", ASCENDING), ("status", ASCENDING), ("created_at", ASCENDING)]
    )

    await db.worker_logs.create_index([("account_id", ASCENDING), ("created_at", ASCENDING)])

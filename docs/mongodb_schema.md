# MongoDB Schema

Collections:

- `accounts`
- `list_assignments`
- `proxies`
- `post_jobs`
- `worker_logs`
- `app_settings`

Required indexes are defined in `twitter_telegram_bot/app/database/indexes.py`.

The important delivery invariant is:

1. Telegram delivery succeeds.
2. Telegram message IDs are saved on the post job.
3. The post job is marked `telegram_sent`.
4. The list checkpoint is updated.

This keeps retries recoverable after crashes.

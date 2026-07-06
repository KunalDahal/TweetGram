# Architecture

The app is a single Telegram-controlled Python process. Telegram commands call `AccountManager`, which persists state in MongoDB and starts or stops per-account workers through `WorkerPool`.

Each active account owns one `Worker`. Workers resume unfinished jobs first, then process assigned Twitter/X Lists in sequence. The worker never advances a list checkpoint until Telegram delivery succeeds.

External integrations are intentionally isolated:

- `TwscrapeAdapter` fetches list posts.
- `MediaDownloader` stores source media in temporary storage.
- `ProviderRegistry` selects the configured LLM provider.
- `TelegramPublisher` sends generated captions and appends the source link when needed.
- Repositories are the only MongoDB access path for application code.

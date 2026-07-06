# Failure Recovery

Retryable operations use three total attempts. On terminal failure, the worker moves to `error`, preserves the job state, and alerts authorized Telegram users.

Workers resume unfinished jobs before discovering new posts. Generated captions and downloaded media are reused where possible.

Rate limits are not treated as proxy failures by default. Failed proxies can be deleted and replaced by another account proxy, falling back to the VPS IP if none remain.

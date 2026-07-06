# Telegram-Controlled Twitter/X List Processing Bot

Private Python application for managing multiple Twitter/X accounts from Telegram. Each active account has one worker that reads assigned Twitter/X Lists, creates resumable post jobs, sends content to an account-specific LLM, and publishes the generated caption plus source link to one shared Telegram channel.

## Status

This repository contains the backend scaffold: configuration, MongoDB repositories and indexes, account manager, worker pool, job runner, Telegram command handlers, deployment files, and documentation. Provider-specific LLM clients and the concrete `twscrape` implementation are intentionally isolated behind adapters.

## Quick Start

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .[dev]
copy .env.example .env
python scripts/verify_environment.py
python -m twitter_telegram_bot.app.main
```

## Key Commands

- `/acc -a <username> <password> <email> <email_password> [proxy]`
- `/acc -c <username> <auth_token> <ct0> [proxy]`
- `/acc -l <twitter_list_id> -a <account_id>`
- `/acc -i <account_id>`
- `/acc -h <account_id>`
- `/acc <account_id> -ka <llm_key>`
- `/acc <account_id> -lm <provider> <model>`
- `/prompt "<text>"`
- `/acc -s`

See `docs/command_reference.md` for the full command list.

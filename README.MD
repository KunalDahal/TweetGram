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
python -m tweetgrambot.app.main
```

## Key Commands

- `/acc -a <username> <password> <email> <email_password> [proxy]`
- `/acc -c <username> <auth_token> <ct0> [proxy]`
- `/acc <account_id> -c <auth_token> <ct0> [proxy]`
- `/acc -l <twitter_list_id> -a <account_id>`
- `/acc -i <account_id>`
- `/acc -h <account_id>`
- `/acc <account_id> -ka <llm_key>`
- `/acc <account_id> -lm`
- `/prompt "<text>"`
- `/acc -s`

See `docs/command_reference.md` for the full command list.

## X Cookie Sessions

`auth_token` and `ct0` are temporary X session credentials. X does not publish a fixed lifetime for either cookie, so treat them as renewable credentials rather than long-term unattended auth. They can last from hours to weeks or longer, but may stop working after logout, cookie clearing, password changes or resets, session revocation, security checks, account locks, suspicious-login detection, or server-side session rotation.

A password reset explicitly logs out active X sessions, so any captured cookies should be treated as invalid afterward. X also lets you review and revoke sessions through its Apps and sessions controls.

For `twscrape`, design around renewal:

1. Add the account with `/acc -c <username> <auth_token> <ct0> [proxy]`.
2. Detect authentication failures such as 401 or login-required responses.
3. Export fresh `auth_token` and `ct0` values from a newly logged-in browser session.
4. Replace the cookies with `/acc <account_id> -c <auth_token> <ct0> [proxy]`.

Refresh `auth_token` and `ct0` together from the same browser session because `ct0` can rotate independently.

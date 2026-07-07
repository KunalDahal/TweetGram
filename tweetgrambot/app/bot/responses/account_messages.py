from __future__ import annotations


def account_created(account_id: str) -> str:
    return f"Account created: {account_id}"


def account_cookies_refreshed(account_id: str) -> str:
    return f"Cookies refreshed for {account_id}. Use /acc -i {account_id} to reactivate the worker."


def account_removed(account_id: str) -> str:
    return f"Account removed: {account_id}"


def account_activated(account_id: str) -> str:
    return f"Account activated: {account_id}"


def account_halted(account_id: str) -> str:
    return f"Account halted: {account_id}"

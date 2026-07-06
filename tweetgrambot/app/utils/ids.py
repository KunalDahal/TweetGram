from __future__ import annotations

from secrets import token_hex


def new_account_id() -> str:
    return f"acc_{token_hex(4)}"


def worker_id_for(account_id: str) -> str:
    return f"worker_{account_id}"

from __future__ import annotations


def command_error(error: Exception) -> str:
    return f"Error: {error}"


UNAUTHORIZED = "Unauthorized."

from __future__ import annotations


def require_non_empty(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} is required")
    return cleaned


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]

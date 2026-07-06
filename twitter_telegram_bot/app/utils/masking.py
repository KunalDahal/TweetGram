from __future__ import annotations


def mask_secret(value: str | None, *, visible: int = 4) -> str:
    if not value:
        return "<none>"
    if len(value) <= visible:
        return "*" * len(value)
    return f"{value[:visible]}...{value[-visible:]}"


def mask_proxy(proxy: str | None) -> str:
    if not proxy:
        return "<vps-ip>"
    if "@" not in proxy:
        return mask_secret(proxy)
    prefix, suffix = proxy.rsplit("@", 1)
    scheme = prefix.split("://", 1)[0] if "://" in prefix else "proxy"
    return f"{scheme}://***@{suffix}"

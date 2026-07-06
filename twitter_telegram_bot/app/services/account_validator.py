from __future__ import annotations


class AccountValidator:
    async def validate_credentials(
        self,
        *,
        username: str,
        password: str,
        email: str,
        email_password: str,
        proxy: str | None = None,
    ) -> None:
        _ = (username, password, email, email_password, proxy)

    async def validate_cookies(
        self,
        *,
        username: str,
        auth_token: str,
        ct0: str,
        proxy: str | None = None,
    ) -> None:
        _ = (username, auth_token, ct0, proxy)
